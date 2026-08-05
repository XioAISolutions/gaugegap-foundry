"""Artifact IO helpers shared by the demo and tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contracts import canonical_json


def dump_artifact(artifact: dict[str, Any], path: str | Path) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination


def load_artifact(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def artifact_digest(artifact: dict[str, Any]) -> str:
    from hashlib import sha256

    return "sha256:" + sha256(canonical_json(artifact).encode("utf-8")).hexdigest()
