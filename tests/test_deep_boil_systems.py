from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from gaugegap.flowgap_attractors import get_system, rk4_step
from gaugegap.hamiltonian_factory import audit_hamiltonian, build_hamiltonian
from gaugegap.koopman import exact_dmd, hankel_embed, reconstruct
from gaugegap.research_manifest import ClaimLevel, ResearchClaim, validate_claim
from gaugegap.validated_dynamics import IntervalBox, picard_enclosure_step


ROOT = Path(__file__).resolve().parents[1]


def test_exact_dmd_recovers_planar_rotation():
    theta = 0.17
    matrix = np.array(
        [[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]],
        dtype=float,
    )
    state = np.array([1.0, 0.2])
    samples = [state.copy()]
    for _ in range(159):
        state = matrix @ state
        samples.append(state.copy())
    result = exact_dmd(np.asarray(samples), dt=1.0, rank=2)
    assert result.reconstruction_error < 1e-10
    np.testing.assert_allclose(np.sort(np.abs(result.eigenvalues)), [1.0, 1.0], atol=1e-10)
    reconstructed = reconstruct(result, 12)
    np.testing.assert_allclose(reconstructed.real, np.asarray(samples[:12]), atol=1e-9)


def test_hankel_embedding_shape_and_validation():
    embedded = hankel_embed(np.arange(20, dtype=float), delays=4, stride=2)
    assert embedded.shape == (14, 4)
    with pytest.raises(ValueError):
        hankel_embed([1.0, 2.0], delays=4)


def test_validated_rossler_step_contains_high_resolution_rk4_endpoint():
    system = get_system("rossler")
    params = system.parameters()
    initial = IntervalBox.from_point(system.default_state, radius=1e-15)
    record = picard_enclosure_step("rossler", initial, params, dt=0.001)
    assert record.validated, record.reason
    state = np.asarray(system.default_state, dtype=float)
    sub_dt = 0.001 / 20
    for _ in range(20):
        state = rk4_step(system, state, sub_dt, params)
    assert record.endpoint.contains_point(state)


@pytest.mark.parametrize("name", ["rossler", "lorenz", "thomas"])
def test_registered_interval_steps_validate_at_small_dt(name):
    system = get_system(name)
    record = picard_enclosure_step(
        name,
        IntervalBox.from_point(system.default_state, radius=1e-15),
        system.parameters(),
        dt=1e-4,
    )
    assert record.validated, record.summary()
    assert record.maximum_endpoint_width > 0.0


def test_canonical_hamiltonian_factory_builds_hermitian_reference_models():
    requests = [
        ("z2-plaquette", {"n_plaquettes": 1, "plaquette_coupling": 1.0, "transverse_field": 0.3}),
        ("u1-plaquette", {"n_links": 2, "g_electric": 1.0, "g_magnetic": 0.4, "truncation": 1}),
    ]
    for model, params in requests:
        artifact = build_hamiltonian(model, **params)
        audit = audit_hamiltonian(artifact)
        assert audit.hermitian
        assert audit.spectral_gap is not None
        assert audit.spectral_gap >= -1e-12
        assert len(audit.matrix_digest) == 64
        assert artifact.digest() == audit.matrix_digest


def test_continuum_theorem_manifest_fails_closed_without_review_and_formal_evidence():
    claim = ResearchClaim(
        claim_id="unsafe",
        title="Unsafe promotion",
        statement="A continuum theorem has been proved.",
        level=ClaimLevel.CONTINUUM_THEOREM,
        finite_scope="none",
        assumptions=("unspecified",),
        exclusions=("none",),
        methods=("finite numerical experiment",),
    )
    validation = validate_claim(claim)
    assert not validation.valid
    joined = " ".join(validation.errors)
    assert "external reviews" in joined
    assert "formal proof" in joined
    assert "peer-reviewed" in joined


def test_foundry_experience_generator_writes_self_contained_bundle(tmp_path):
    output = tmp_path / "experience"
    preview = tmp_path / "preview.svg"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "generate_foundry_experience.py"),
            "--output-dir",
            str(output),
            "--preview",
            str(preview),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    html = (output / "index.html").read_text(encoding="utf-8")
    data = json.loads((output / "data.json").read_text(encoding="utf-8"))
    manifest = json.loads((output / "research_manifest.json").read_text(encoding="utf-8"))
    assert "Experience" in html and "Experiment" in html
    assert "AudioContext" in html
    assert "cdn" not in html.lower()
    assert len(data["scenes"]) == 7
    assert {scene["id"] for scene in data["scenes"]} >= {
        "rossler",
        "lorenz",
        "thomas",
        "lattice",
        "su3",
        "spectra",
        "limits",
    }
    assert manifest["claims"][0]["level"] == "reproducible_finite_result"
    assert preview.exists()


def test_deep_boil_smoke_command(tmp_path):
    output = tmp_path / "deep-boil"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_deep_boil.py"),
            "--smoke",
            "--output-dir",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads((output / "deep_boil.json").read_text(encoding="utf-8"))
    assert payload["status"] == "pass"
    assert all(payload["checks"].values())
    assert (output / "research_manifest.json").exists()
