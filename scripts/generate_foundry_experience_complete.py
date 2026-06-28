#!/usr/bin/env python3
"""Generate the complete Foundry Experience with all audited extension scenes.

The original generator remains the stable seven-scene engine. This canonical wrapper
extends its dataset and self-contained HTML through fail-closed layers so every existing
scene remains intact while Lagrangian Forge, Anomaly Forge, and InfoGap no-hiding are added.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.anomaly_scene import (  # noqa: E402
    enhance_dataset as enhance_anomaly_dataset,
    enhance_html as enhance_anomaly_html,
)
from gaugegap.lagrangian_scene import (  # noqa: E402
    enhance_dataset as enhance_lagrangian_dataset,
    enhance_html as enhance_lagrangian_html,
)
from gaugegap.no_hiding_scene import (  # noqa: E402
    enhance_dataset as enhance_no_hiding_dataset,
    enhance_html as enhance_no_hiding_html,
)

BASE_SCRIPT = ROOT / "scripts" / "generate_foundry_experience.py"
SPEC = importlib.util.spec_from_file_location("gaugegap_base_foundry_experience", BASE_SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load base Experience generator from {BASE_SCRIPT}")
BASE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = BASE
SPEC.loader.exec_module(BASE)

_BASE_BUILD_DATASET = BASE.build_dataset


def _complete_dataset():
    dataset = enhance_lagrangian_dataset(_BASE_BUILD_DATASET())
    dataset = enhance_anomaly_dataset(dataset)
    return enhance_no_hiding_dataset(dataset)


BASE.build_dataset = _complete_dataset
BASE._HTML = enhance_no_hiding_html(
    enhance_anomaly_html(enhance_lagrangian_html(BASE._HTML))
)


def build_dataset():
    """Expose the complete deterministic dataset for tests and other scripts."""
    return BASE.build_dataset()


def main() -> int:
    return int(BASE.main())


if __name__ == "__main__":
    raise SystemExit(main())
