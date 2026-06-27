"""Programmatic loader for the finite-system hypothesis registry.

The repository registers every benchmark as a small declarative file under
``hypotheses/`` (YAML, plus one historical JSON). Until now those files had no
loader: scripts hard-coded hypothesis IDs as bare strings and ``config/foundry.yaml``
tagged each unit with a ``hypothesis:`` field that nothing validated. This module
turns the directory into a validated registry so the ``HREG`` node in
``docs/ARCHITECTURE.md`` is real and the foundry CLI can fail closed when a unit
points at a hypothesis that does not exist.

Design mirrors ``gaugegap.cli``: a frozen dataclass record and a fail-closed
``RuntimeError`` (``HypothesisError``) rather than silent ``None`` returns.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Mapping

import yaml


PACKAGE_ROOT = Path(__file__).resolve().parents[2]


def _default_root() -> Path:
    """Prefer the current checkout when installed from a wheel (matches cli.py)."""
    cwd = Path.cwd().resolve()
    if (cwd / "hypotheses").is_dir():
        return cwd
    return PACKAGE_ROOT


ROOT = _default_root()
DEFAULT_DIR = ROOT / "hypotheses"


class HypothesisError(RuntimeError):
    """Raised when the hypothesis registry is malformed or queried for an unknown ID."""


@dataclass(frozen=True)
class Hypothesis:
    """One registered finite-system benchmark."""

    id: str
    track: str
    scope: str = ""
    status: str = "unknown"
    claim_boundary: str | None = None
    path: Path | None = None
    raw: Mapping[str, Any] = field(default_factory=dict)


def _identifier(payload: Mapping[str, Any]) -> Any:
    """The registry accepts both ``id`` (YAML) and ``hypothesis_id`` (legacy JSON)."""
    return payload.get("id", payload.get("hypothesis_id"))


def _parse_file(path: Path) -> Mapping[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - filesystem race
        raise HypothesisError(f"cannot read hypothesis file: {path}") from exc
    try:
        if path.suffix == ".json":
            payload = json.loads(text)
        else:
            payload = yaml.safe_load(text)
    except (yaml.YAMLError, json.JSONDecodeError) as exc:
        raise HypothesisError(f"invalid hypothesis file {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise HypothesisError(f"hypothesis file {path} must contain a mapping")
    return payload


def _build(path: Path) -> Hypothesis:
    payload = _parse_file(path)
    identifier = _identifier(payload)
    if not isinstance(identifier, str) or not identifier.strip():
        raise HypothesisError(f"hypothesis file {path} is missing a non-empty id")
    if identifier != path.stem:
        raise HypothesisError(
            f"hypothesis id {identifier!r} does not match filename {path.name!r}"
        )
    track = payload.get("track")
    if not isinstance(track, str) or not track.strip():
        raise HypothesisError(f"hypothesis {identifier!r} is missing a non-empty track")
    return Hypothesis(
        id=identifier,
        track=track,
        scope=str(payload.get("scope", "")),
        status=str(payload.get("status", "unknown")),
        claim_boundary=payload.get("claim_boundary"),
        path=path,
        raw=payload,
    )


def load_registry(directory: Path | str = DEFAULT_DIR) -> dict[str, Hypothesis]:
    """Load and validate every hypothesis file, failing closed on any defect."""
    base = Path(directory).resolve()
    if not base.is_dir():
        raise HypothesisError(f"hypotheses directory not found: {base}")
    registry: dict[str, Hypothesis] = {}
    for path in sorted(base.iterdir()):
        if path.suffix not in {".yaml", ".yml", ".json"} or not path.is_file():
            continue
        hypothesis = _build(path)
        if hypothesis.id in registry:
            raise HypothesisError(f"duplicate hypothesis id: {hypothesis.id}")
        registry[hypothesis.id] = hypothesis
    if not registry:
        raise HypothesisError(f"no hypothesis files found in {base}")
    return registry


def get_hypothesis(
    identifier: str, registry: Mapping[str, Hypothesis] | None = None
) -> Hypothesis:
    """Return one hypothesis by ID, failing closed when it is not registered."""
    registry = registry if registry is not None else load_registry()
    try:
        return registry[identifier]
    except KeyError as exc:
        raise HypothesisError(f"unknown hypothesis: {identifier}") from exc


def list_hypotheses(
    registry: Mapping[str, Hypothesis] | None = None,
) -> list[Hypothesis]:
    """Return all registered hypotheses sorted by (track, id)."""
    registry = registry if registry is not None else load_registry()
    return sorted(registry.values(), key=lambda h: (h.track, h.id))
