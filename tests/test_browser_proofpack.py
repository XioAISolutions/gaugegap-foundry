"""The Experience interface ships an in-browser proofpack export.

The "Export proofpack" button bundles the live slider parameters, RK4 solver
settings, a trajectory digest, and the claim boundary into a downloadable
content-hashed JSON file (schema ``gaugegap.browser_attractor_proofpack.v1``).

These tests pin that (a) the base template renders the button and the export
logic, and (b) the complete multi-scene generator — which patches the base
template through fail-closed exact-substring anchors — still loads and builds,
proving the insertion did not break any patch marker.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE_SCRIPT = ROOT / "scripts" / "generate_foundry_experience.py"
COMPLETE_SCRIPT = ROOT / "scripts" / "generate_foundry_experience_complete.py"

PROOFPACK_SCHEMA = "gaugegap.browser_attractor_proofpack.v1"


def _load(script: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_base_template_renders_the_proofpack_export():
    module = _load(BASE_SCRIPT, "browser_proofpack_base_test")
    html = module._HTML
    assert 'id="proofpack"' in html
    assert PROOFPACK_SCHEMA in html
    # Hashing must go through WebCrypto with an explicit fallback marker.
    assert "crypto.subtle" in html
    assert "unavailable-no-webcrypto" in html
    # The pack must carry solver settings and the claim boundary.
    assert "claim_boundary:{scene:sc.claim_boundary||null,global:DATA.claim_boundary}" in html
    assert "method:'RK4'" in html


def test_complete_generator_still_patches_and_builds():
    # Loading the complete generator exercises every fail-closed
    # _replace_once anchor against the modified base template.
    module = _load(COMPLETE_SCRIPT, "browser_proofpack_complete_test")
    assert 'id="proofpack"' in module.BASE._HTML
    dataset = module.build_dataset()
    scenes = dataset["scenes"]
    assert len(scenes) >= 15
    attractors = [scene for scene in scenes if scene.get("kind") == "attractor"]
    assert len(attractors) >= 3
    # The export reads these fields from each attractor scene.
    for scene in attractors:
        assert "dt" in scene and "defaults" in scene and "parameters" in scene
