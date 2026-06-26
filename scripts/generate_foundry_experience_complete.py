#!/usr/bin/env python3
"""Generate the complete Foundry Experience, including Lagrangian Forge.

The original generator remains the stable seven-scene engine.  This canonical wrapper
extends its dataset and self-contained HTML through audited, fail-closed patch markers,
so all existing scenes and controls are preserved while the Standard Model scene is added.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.lagrangian_scene import enhance_dataset, enhance_html  # noqa: E402

BASE_SCRIPT = ROOT / "scripts" / "generate_foundry_experience.py"
SPEC = importlib.util.spec_from_file_location("gaugegap_base_foundry_experience", BASE_SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load base Experience generator from {BASE_SCRIPT}")
BASE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = BASE
SPEC.loader.exec_module(BASE)

_BASE_BUILD_DATASET = BASE.build_dataset
BASE.build_dataset = lambda: enhance_dataset(_BASE_BUILD_DATASET())
BASE._HTML = enhance_html(BASE._HTML)


def build_dataset():
    """Expose the complete deterministic dataset for tests and other scripts."""
    return BASE.build_dataset()


def main() -> int:
    return int(BASE.main())


if __name__ == "__main__":
    raise SystemExit(main())
