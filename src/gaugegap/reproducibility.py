"""Deterministic source-tree attestations for reproducible scientific builds."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
from typing import Iterable


DEFAULT_INPUTS = (
    "pyproject.toml",
    "config",
    "src",
    "scripts",
    "benchmarks",
    "formal",
    "tests",
)
_EXCLUDED_PARTS = {".git", ".venv", "__pycache__", "build", "dist", "results", "site"}


@dataclass(frozen=True)
class AttestedFile:
    path: str
    size: int
    sha256: str


@dataclass(frozen=True)
class BuildAttestation:
    source_date_epoch: int
    files: tuple[AttestedFile, ...]
    content_digest: str

    def summary(self) -> dict[str, object]:
        return {
            "schema": "gaugegap.build_attestation.v1",
            "source_date_epoch": self.source_date_epoch,
            "file_count": len(self.files),
            "files": [asdict(item) for item in self.files],
            "content_digest": self.content_digest,
            "claim_boundary": (
                "deterministic source-input attestation only; identical source digests do "
                "not by themselves prove identical external toolchains or hardware"
            ),
        }


def _iter_files(root: Path, inputs: Iterable[str]) -> Iterable[Path]:
    for item in inputs:
        candidate = root / item
        if candidate.is_file():
            yield candidate
            continue
        if not candidate.exists():
            continue
        for path in sorted(candidate.rglob("*")):
            if path.is_file() and not any(part in _EXCLUDED_PARTS for part in path.parts):
                yield path


def build_attestation(
    root: Path | str,
    *,
    source_date_epoch: int = 0,
    inputs: Iterable[str] = DEFAULT_INPUTS,
) -> BuildAttestation:
    root_path = Path(root).resolve()
    records: list[AttestedFile] = []
    seen: set[str] = set()
    for path in _iter_files(root_path, inputs):
        relative = path.relative_to(root_path).as_posix()
        if relative in seen:
            continue
        seen.add(relative)
        data = path.read_bytes()
        records.append(
            AttestedFile(
                path=relative,
                size=len(data),
                sha256=hashlib.sha256(data).hexdigest(),
            )
        )
    records.sort(key=lambda item: item.path)
    canonical = json.dumps(
        {
            "source_date_epoch": int(source_date_epoch),
            "files": [asdict(item) for item in records],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return BuildAttestation(
        source_date_epoch=int(source_date_epoch),
        files=tuple(records),
        content_digest=hashlib.sha256(canonical).hexdigest(),
    )
