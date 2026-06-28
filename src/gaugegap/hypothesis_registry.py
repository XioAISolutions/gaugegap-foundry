"""Validated loader for hypotheses/*.yaml and the legacy JSON record."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Mapping

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DIR = ROOT / "hypotheses"


class HypothesisError(RuntimeError):
    pass


@dataclass(frozen=True)
class Hypothesis:
    id: str
    track: str
    status: str
    scope: str
    claim_boundary: str | None
    path: Path
    raw: Mapping[str, object]


def _read(path: Path) -> dict[str, object]:
    try:
        text = path.read_text(encoding="utf-8")
        value = json.loads(text) if path.suffix == ".json" else yaml.safe_load(text)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        raise HypothesisError(f"invalid hypothesis file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise HypothesisError(f"hypothesis file must contain a mapping: {path}")
    return value


def load_registry(directory: Path | str = DEFAULT_DIR) -> dict[str, Hypothesis]:
    base = Path(directory)
    if not base.is_dir():
        raise HypothesisError(f"hypotheses directory not found: {base}")
    result: dict[str, Hypothesis] = {}
    for path in sorted(base.iterdir()):
        if path.suffix not in {".yaml", ".yml", ".json"}:
            continue
        raw = _read(path)
        identifier = raw.get("id", raw.get("hypothesis_id"))
        track = raw.get("track")
        if not isinstance(identifier, str) or identifier != path.stem:
            raise HypothesisError(f"hypothesis id must match filename: {path}")
        if not isinstance(track, str) or not track:
            raise HypothesisError(f"hypothesis {identifier} has no track")
        if identifier in result:
            raise HypothesisError(f"duplicate hypothesis id: {identifier}")
        result[identifier] = Hypothesis(
            identifier,
            track,
            str(raw.get("status", "unknown")),
            str(raw.get("scope", "")),
            raw.get("claim_boundary") if isinstance(raw.get("claim_boundary"), str) else None,
            path,
            raw,
        )
    if not result:
        raise HypothesisError("no hypothesis files found")
    return result


def get_hypothesis(identifier: str, registry: Mapping[str, Hypothesis] | None = None) -> Hypothesis:
    registry = registry or load_registry()
    try:
        return registry[identifier]
    except KeyError as exc:
        raise HypothesisError(f"unknown hypothesis: {identifier}") from exc
