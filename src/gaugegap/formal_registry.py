"""Inventory machine-checkable proof artifacts and expose possible holes."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path
import re
from typing import Iterable


FORMAL_SUFFIXES = {".lean": "lean4", ".v": "coq", ".thy": "isabelle", ".smt2": "smtlib"}
_HOLE_PATTERNS = {
    "lean4": re.compile(r"(?m)^\s*(?:sorry|admit)\b"),
    "coq": re.compile(r"(?m)^\s*(?:Admitted\.|admit\.)"),
    "isabelle": re.compile(r"(?m)^\s*(?:sorry|oops)\b"),
    "smtlib": re.compile(r"a^"),
}


@dataclass(frozen=True)
class FormalArtifact:
    path: str
    prover: str
    sha256: str
    lines: int
    holes: tuple[str, ...]
    hole_free: bool


@dataclass(frozen=True)
class FormalRegistry:
    artifact_count: int
    hole_free_count: int
    artifacts_with_holes: tuple[str, ...]
    artifacts: tuple[FormalArtifact, ...]

    def summary(self) -> dict[str, object]:
        return {
            "schema": "gaugegap.formal_registry.v1",
            "artifact_count": self.artifact_count,
            "hole_free_count": self.hole_free_count,
            "artifacts_with_holes": list(self.artifacts_with_holes),
            "artifacts": [asdict(item) for item in self.artifacts],
            "claim_boundary": (
                "syntactic proof-artifact inventory only; hole-free source still requires "
                "successful checking by the declared prover"
            ),
        }


def _iter_formal_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in FORMAL_SUFFIXES:
            continue
        if any(part in {".git", ".venv", "site", "dist", "build"} for part in path.parts):
            continue
        yield path


def build_formal_registry(root: Path | str) -> FormalRegistry:
    root_path = Path(root).resolve()
    artifacts: list[FormalArtifact] = []
    for path in _iter_formal_files(root_path):
        prover = FORMAL_SUFFIXES[path.suffix.lower()]
        text = path.read_text(encoding="utf-8", errors="replace")
        pattern = _HOLE_PATTERNS[prover]
        holes = tuple(match.group(0).strip() for match in pattern.finditer(text))
        artifacts.append(
            FormalArtifact(
                path=path.relative_to(root_path).as_posix(),
                prover=prover,
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                lines=len(text.splitlines()),
                holes=holes,
                hole_free=not holes,
            )
        )
    with_holes = tuple(item.path for item in artifacts if not item.hole_free)
    return FormalRegistry(
        artifact_count=len(artifacts),
        hole_free_count=sum(item.hole_free for item in artifacts),
        artifacts_with_holes=with_holes,
        artifacts=tuple(artifacts),
    )
