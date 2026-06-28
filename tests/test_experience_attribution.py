"""The Experience interface carries a concrete, bounded inspiration attribution.

The two-mode Experience/Experiment design is a conceptual nod to Ryoji Ikeda's
``supersymmetry``. This test pins that the attribution is (a) machine-readable in
the dataset payload, (b) rendered into the generated HTML, and (c) explicitly
bounded as inspiration-only with no assets used and no endorsement implied.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_foundry_experience.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("experience_attr_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_dataset_payload_carries_bounded_attribution():
    module = _load_generator()
    attribution = module.build_dataset()["attribution"]
    assert "Ryoji Ikeda" in attribution
    assert "supersymmetry" in attribution
    # Inspiration-only boundary must be explicit.
    assert "inspiration" in attribution.lower()
    assert "no affiliation or endorsement" in attribution.lower()
    assert "no artwork, audio, data, or code" in attribution.lower()


def test_generated_html_renders_the_attribution_element():
    module = _load_generator()
    html = module._HTML
    assert 'id="attribution"' in html
    assert "DATA.attribution" in html
