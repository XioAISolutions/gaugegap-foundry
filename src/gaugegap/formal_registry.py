"""Inventory machine-checkable proof artifacts, their holes, and their assumptions.

Two different things can make a proof artifact weaker than it looks, and they
need separate names:

*holes* -- ``sorry``, ``admit``, ``Admitted``: a proof that was abandoned. The
prover itself flags these.

*trust inputs* -- ``axiom``, ``Axiom``, ``Parameter``, ``native_decide``: a
statement asserted rather than proved. The prover accepts them silently, so a
file resting entirely on axioms is syntactically hole-free. Counting only holes
therefore overstates how much has been established, which is why they are
tracked separately here rather than folded together.

Coq ``Variable`` and ``Hypothesis`` inside a ``Section`` are deliberately not
trust inputs: at ``End`` they become universal quantifiers on the section's
theorems, which is ordinary mathematics. The same keywords outside a section do
assume something, and are counted.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path
import re
from typing import Iterable


FORMAL_SUFFIXES = {".lean": "lean4", ".v": "coq", ".thy": "isabelle", ".smt2": "smtlib"}
_HOLE_PATTERNS = {
    "lean4": re.compile(r"(?m)^\s*(?:sorry|admit)\b"),
    "coq": re.compile(r"\b(?:Admitted|admit)\."),
    "isabelle": re.compile(r"(?m)^\s*(?:sorry|oops)\b"),
    "smtlib": re.compile(r"a^"),
}

#: Declarations and tactics that introduce something unproved. ``native_decide``
#: is included because it discharges a goal by trusting the compiler's evaluator
#: rather than the kernel.
#:
#: The capture groups are (name, declared type); the type decides whether the
#: declaration asserts a *fact* or merely names an opaque *constant*.
_TRUST_PATTERNS = {
    "lean4": re.compile(r"(?m)^\s*axiom\s+(\w+)\s*:([^\n]*)|\b(native_decide)()\b"),
    "coq": re.compile(r"(?ms)^\s*(?:Axiom|Parameter|Conjecture)\s+(\w+)\s*:(.*?)\."),
    "isabelle": re.compile(r"(?m)^\s*axiomatization\s+(\w+)\s*(.*)$"),
    "smtlib": re.compile(r"a^"),
}

#: A declared type mentioning a relation or connective states a proposition;
#: anything else (``axiom E : ℝ``) just names a constant of an inhabited type,
#: which is conservative and assumes nothing about it.
_PROPOSITIONAL = re.compile(
    r"[=<>≥≤≠∧∨¬→↔∀∃]|>=|<=|<>|\\/|/\\|->|\bforall\b|\bexists\b|\bProp\b"
)

#: Coq keywords that assume only when they appear outside a ``Section``.
_COQ_SECTION_LOCAL = re.compile(
    r"(?m)^\s*(?:Variables?|Hypothes[ie]s)\s+(\w+)"
)
_COQ_SECTION = re.compile(r"(?ms)^\s*Section\s+\w+\s*\..*?^\s*End\s+\w+\s*\.")


#: Comment syntax per prover. Prose that *mentions* ``sorry`` or ``axiom`` --
#: including a docstring promising there are none -- must not be mistaken for
#: the real thing.
_COMMENT_PATTERNS = {
    "lean4": (re.compile(r"(?s)/-.*?-/"), re.compile(r"--.*")),
    "coq": (re.compile(r"(?s)\(\*.*?\*\)"),),
    "isabelle": (re.compile(r"(?s)\(\*.*?\*\)"), re.compile(r"(?s)\{\*.*?\*\}")),
    "smtlib": (re.compile(r";.*"),),
}


def _strip_comments(prover: str, text: str) -> str:
    for pattern in _COMMENT_PATTERNS[prover]:
        text = pattern.sub(" ", text)
    return text


def _trust_inputs(prover: str, text: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """``(assumed_facts, assumed_constants)`` for this artifact.

    Only the facts weaken the result. Positing a constant of an inhabited type
    is a conservative extension: ``axiom E : ℝ`` says a real number exists,
    which was already true. ``axiom bound : E ≥ 40`` is the one that assumes
    something.
    """
    facts: list[str] = []
    constants: list[str] = []
    for match in _TRUST_PATTERNS[prover].finditer(text):
        groups = [group for group in match.groups() if group is not None]
        name = next((group for group in groups if group.strip()), "")
        declared = groups[groups.index(name) + 1] if len(groups) > groups.index(name) + 1 else ""
        if name == "native_decide" or _PROPOSITIONAL.search(declared):
            facts.append(name)
        else:
            constants.append(name)
    if prover == "coq":
        # Section-local variables and hypotheses are discharged at ``End``;
        # only the ones outside every section assume anything.
        outside_sections = _COQ_SECTION.sub(" ", text)
        facts.extend(_COQ_SECTION_LOCAL.findall(outside_sections))
    return tuple(facts), tuple(constants)


@dataclass(frozen=True)
class FormalArtifact:
    path: str
    prover: str
    sha256: str
    lines: int
    holes: tuple[str, ...]
    hole_free: bool
    trust_inputs: tuple[str, ...]
    assumed_constants: tuple[str, ...]
    assumption_free: bool


@dataclass(frozen=True)
class FormalRegistry:
    artifact_count: int
    hole_free_count: int
    assumption_free_count: int
    trust_input_count: int
    artifacts_with_holes: tuple[str, ...]
    artifacts_with_trust_inputs: tuple[str, ...]
    artifacts: tuple[FormalArtifact, ...]

    def summary(self) -> dict[str, object]:
        return {
            "schema": "gaugegap.formal_registry.v2",
            "artifact_count": self.artifact_count,
            "hole_free_count": self.hole_free_count,
            "assumption_free_count": self.assumption_free_count,
            "trust_input_count": self.trust_input_count,
            "artifacts_with_holes": list(self.artifacts_with_holes),
            "artifacts_with_trust_inputs": list(self.artifacts_with_trust_inputs),
            "artifacts": [asdict(item) for item in self.artifacts],
            "claim_boundary": (
                "syntactic proof-artifact inventory only; hole-free source still requires "
                "successful checking by the declared prover. hole_free and "
                "assumption_free are different properties: a file whose conclusion is "
                "asserted by axiom is hole-free and not assumption-free, so read "
                "assumption_free_count, not hole_free_count, as the count of artifacts "
                "that establish their statements outright. trust_inputs lists assumed "
                "facts only; assumed_constants lists opaque constants of inhabited "
                "types, which are a conservative extension and assume nothing"
            ),
        }


def _iter_formal_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in FORMAL_SUFFIXES:
            continue
        # ``.lake``/``lake-packages`` hold Lean dependency checkouts (Mathlib's own
        # test files carry ``sorry`` deliberately), not artifacts of this project.
        if any(
            part in {".git", ".venv", "site", "dist", "build", ".lake", "lake-packages"}
            for part in path.parts
        ):
            continue
        yield path


def build_formal_registry(root: Path | str) -> FormalRegistry:
    root_path = Path(root).resolve()
    artifacts: list[FormalArtifact] = []
    for path in _iter_formal_files(root_path):
        prover = FORMAL_SUFFIXES[path.suffix.lower()]
        text = path.read_text(encoding="utf-8", errors="replace")
        code = _strip_comments(prover, text)
        pattern = _HOLE_PATTERNS[prover]
        holes = tuple(match.group(0).strip() for match in pattern.finditer(code))
        trust, constants = _trust_inputs(prover, code)
        artifacts.append(
            FormalArtifact(
                path=path.relative_to(root_path).as_posix(),
                prover=prover,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                lines=len(text.splitlines()),
                holes=holes,
                hole_free=not holes,
                trust_inputs=trust,
                assumed_constants=constants,
                assumption_free=not trust,
            )
        )
    with_holes = tuple(item.path for item in artifacts if not item.hole_free)
    with_trust = tuple(item.path for item in artifacts if not item.assumption_free)
    return FormalRegistry(
        artifact_count=len(artifacts),
        hole_free_count=sum(item.hole_free for item in artifacts),
        assumption_free_count=sum(item.assumption_free for item in artifacts),
        trust_input_count=sum(len(item.trust_inputs) for item in artifacts),
        artifacts_with_holes=with_holes,
        artifacts_with_trust_inputs=with_trust,
        artifacts=tuple(artifacts),
    )
