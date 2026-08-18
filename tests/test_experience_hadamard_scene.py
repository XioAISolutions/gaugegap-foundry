"""The Hadamard scene ships a witness the browser can re-verify from the packed rows.

The page recomputes ``H @ H.T`` client-side, so the embedded payload has to be a
complete, losslessly decodable witness -- not a picture of one. This test pins
that the scene's packed rows decode back to a matrix that passes the same exact
gates the Python verifier applies.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

from gaugegap.hadamard_forge import HadamardWitness, verify_hadamard

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_foundry_experience.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("experience_hadamard_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _scene():
    return _load_generator()._hadamard_dataset()


def test_scene_declares_a_verified_witness() -> None:
    scene = _scene()
    assert scene["kind"] == "hadamard"
    assert scene["order"] == 168
    assert scene["verified"] is True
    assert scene["gram_block"][0][0] == 168
    assert scene["gram_block"][0][1] == 0


def test_scene_rows_decode_to_a_matrix_that_passes_the_gates() -> None:
    scene = _scene()
    witness = HadamardWitness.from_packed_hex(
        scene["order"], scene["rows_hex"], name="scene", provenance="experience-scene"
    )
    assert witness.rows_digest() == scene["rows_sha256"]
    assert verify_hadamard(witness, expected_order=scene["order"]).passed


def test_scene_carries_its_own_claim_boundary() -> None:
    boundary = _scene()["claim_boundary"]
    assert "not a proof of the Hadamard conjecture" in boundary


def test_dataset_includes_the_scene() -> None:
    scenes = _load_generator().build_dataset()["scenes"]
    assert any(scene["id"] == "hadamard" for scene in scenes)
