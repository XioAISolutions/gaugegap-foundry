"""Fail-closed research claim manifests for finite scientific artifacts.

A manifest binds a claim to its scope, evidence, assumptions, reproducibility
metadata, and explicit exclusions.  The validator refuses promotion to stronger
claim classes when the required evidence is absent.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence


class ClaimLevel(str, Enum):
    NUMERICAL_DEMO = "numerical_demo"
    REPRODUCIBLE_FINITE_RESULT = "reproducible_finite_result"
    CERTIFIED_FINITE_RESULT = "certified_finite_result"
    FORMAL_FINITE_THEOREM = "formal_finite_theorem"
    CONTINUUM_CONJECTURE = "continuum_conjecture"
    CONTINUUM_THEOREM = "continuum_theorem"


@dataclass(frozen=True)
class EvidenceArtifact:
    path: str
    kind: str
    sha256: str
    bytes: int
    verifier: str | None = None
    description: str = ""

    @classmethod
    def from_path(
        cls,
        path: Path,
        *,
        base: Path | None = None,
        kind: str = "artifact",
        verifier: str | None = None,
        description: str = "",
    ) -> "EvidenceArtifact":
        payload = path.read_bytes()
        display = path if base is None else path.relative_to(base)
        return cls(
            path=display.as_posix(),
            kind=kind,
            sha256=hashlib.sha256(payload).hexdigest(),
            bytes=len(payload),
            verifier=verifier,
            description=description,
        )


@dataclass(frozen=True)
class ResearchClaim:
    claim_id: str
    title: str
    statement: str
    level: ClaimLevel
    finite_scope: str
    assumptions: tuple[str, ...]
    exclusions: tuple[str, ...]
    evidence: tuple[EvidenceArtifact, ...] = ()
    methods: tuple[str, ...] = ()
    parameters: Mapping[str, object] = field(default_factory=dict)
    git_commit: str | None = None
    external_review: tuple[str, ...] = ()
    schema: str = "gaugegap.research_claim.v1"

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["level"] = self.level.value
        payload["parameters"] = dict(self.parameters)
        return payload

    def digest(self) -> str:
        payload = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ManifestValidation:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

    def raise_for_errors(self) -> None:
        if self.errors:
            raise ValueError("; ".join(self.errors))


def validate_claim(claim: ResearchClaim) -> ManifestValidation:
    errors: list[str] = []
    warnings: list[str] = []

    if not claim.claim_id.strip():
        errors.append("claim_id must be non-empty")
    if not claim.statement.strip():
        errors.append("statement must be non-empty")
    if not claim.finite_scope.strip():
        errors.append("finite_scope must be explicit")
    if not claim.exclusions:
        errors.append("at least one explicit exclusion is required")

    paths = [artifact.path for artifact in claim.evidence]
    if len(paths) != len(set(paths)):
        errors.append("evidence artifact paths must be unique")
    for artifact in claim.evidence:
        if len(artifact.sha256) != 64:
            errors.append(f"invalid sha256 for {artifact.path}")
        if artifact.bytes < 0:
            errors.append(f"invalid byte count for {artifact.path}")

    kinds = {artifact.kind for artifact in claim.evidence}
    verified = {artifact.kind for artifact in claim.evidence if artifact.verifier}

    if claim.level in {
        ClaimLevel.REPRODUCIBLE_FINITE_RESULT,
        ClaimLevel.CERTIFIED_FINITE_RESULT,
        ClaimLevel.FORMAL_FINITE_THEOREM,
    }:
        if not claim.git_commit:
            errors.append(f"{claim.level.value} requires a git commit")
        if not claim.evidence:
            errors.append(f"{claim.level.value} requires evidence artifacts")
        if not any(kind in kinds for kind in {"data", "result", "certificate", "formal_proof"}):
            errors.append(f"{claim.level.value} requires a scientific result artifact")

    if claim.level == ClaimLevel.CERTIFIED_FINITE_RESULT:
        if not ({"certificate", "interval_enclosure", "residual_bound"} & kinds):
            errors.append("certified_finite_result requires a certificate or rigorous bound")
        if not verified:
            errors.append("certified_finite_result requires an independently named verifier")

    if claim.level == ClaimLevel.FORMAL_FINITE_THEOREM:
        if "formal_proof" not in kinds:
            errors.append("formal_finite_theorem requires a formal_proof artifact")
        if "formal_proof" not in verified:
            errors.append("formal_finite_theorem requires a checked formal proof")
        if not claim.assumptions:
            errors.append("formal_finite_theorem must list its assumptions")

    if claim.level == ClaimLevel.CONTINUUM_CONJECTURE:
        warnings.append("continuum conjectures are research directions, not established results")
        if not claim.external_review:
            warnings.append("no external expert review is recorded")

    if claim.level == ClaimLevel.CONTINUUM_THEOREM:
        if len(claim.external_review) < 2:
            errors.append("continuum_theorem requires at least two independent external reviews")
        if "formal_proof" not in verified:
            errors.append("continuum_theorem requires a machine-checked formal proof artifact")
        if "peer_reviewed_publication" not in kinds:
            errors.append("continuum_theorem requires a peer-reviewed publication artifact")
        if not any("continuum" in method.lower() for method in claim.methods):
            errors.append("continuum_theorem must identify the continuum argument")

    return ManifestValidation(valid=not errors, errors=tuple(errors), warnings=tuple(warnings))


def write_manifest(path: Path, claims: Sequence[ResearchClaim]) -> dict[str, object]:
    validations = [validate_claim(claim) for claim in claims]
    for validation in validations:
        validation.raise_for_errors()
    payload = {
        "schema": "gaugegap.research_manifest_collection.v1",
        "claims": [claim.to_dict() | {"digest": claim.digest()} for claim in claims],
        "warnings": [warning for validation in validations for warning in validation.warnings],
    }
    canonical = json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical, encoding="utf-8")
    return payload


def artifacts_from_directory(
    directory: Path,
    *,
    kind_by_suffix: Mapping[str, str] | None = None,
    ignored_names: Iterable[str] = (),
) -> tuple[EvidenceArtifact, ...]:
    mapping = {
        ".json": "result",
        ".jsonl": "ledger",
        ".csv": "data",
        ".svg": "figure",
        ".html": "interactive_view",
        ".lean": "formal_proof",
        ".v": "formal_proof",
        ".md": "report",
    }
    if kind_by_suffix:
        mapping.update(kind_by_suffix)
    ignored = set(ignored_names)
    records: list[EvidenceArtifact] = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.name in ignored:
            continue
        kind = mapping.get(path.suffix.lower(), "artifact")
        verifier = None
        if path.suffix == ".lean":
            verifier = "Lean 4"
        elif path.suffix == ".v":
            verifier = "Coq"
        records.append(EvidenceArtifact.from_path(path, base=directory, kind=kind, verifier=verifier))
    return tuple(records)
