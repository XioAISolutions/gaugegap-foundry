from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from gaugegap.flowgap_attractors import (
    SYSTEMS,
    analyze_attractor,
    emit_divergence_certificate,
    fixed_point_analysis,
    get_system,
    integrate,
    kaplan_yorke_dimension,
    lyapunov_spectrum,
    parameter_sweep,
    poincare_section,
    recurrence_and_correlation_estimates,
    rk4_step,
    step_halving_check,
)


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("name", sorted(SYSTEMS))
def test_registered_jacobians_match_finite_difference(name):
    system = get_system(name)
    params = system.parameters()
    state = np.asarray(system.default_state, dtype=float) + np.array([0.17, -0.11, 0.23])
    epsilon = 1e-7
    numeric = np.empty((3, 3))
    for column in range(3):
        delta = np.zeros(3)
        delta[column] = epsilon
        numeric[:, column] = (
            system.rhs(state + delta, params) - system.rhs(state - delta, params)
        ) / (2.0 * epsilon)
    np.testing.assert_allclose(system.jacobian(state, params), numeric, rtol=1e-6, atol=1e-7)


def test_rossler_fixed_points_satisfy_vector_field():
    system = get_system("rossler")
    records = fixed_point_analysis(system, system.parameters())
    assert len(records) == 2
    assert max(record["residual_norm"] for record in records) < 1e-11


def test_lorenz_fixed_points_and_global_divergence():
    system = get_system("lorenz")
    params = system.parameters()
    records = fixed_point_analysis(system, params)
    assert len(records) == 3
    assert max(record["residual_norm"] for record in records) < 1e-11
    assert system.divergence(np.array([99.0, -4.0, 7.0]), params) == pytest.approx(
        -(params["sigma"] + 1.0 + params["beta"])
    )


def test_rk4_and_integration_are_deterministic():
    system = get_system("rossler")
    params = system.parameters()
    first = rk4_step(system, system.default_state, 0.01, params)
    second = rk4_step(system, system.default_state, 0.01, params)
    np.testing.assert_array_equal(first, second)
    t1, x1 = integrate(system, params, system.default_state, dt=0.01, steps=1200, sample_every=3)
    t2, x2 = integrate(system, params, system.default_state, dt=0.01, steps=1200, sample_every=3)
    np.testing.assert_array_equal(t1, t2)
    np.testing.assert_array_equal(x1, x2)


def test_poincare_section_interpolates_crossings_deterministically():
    system = get_system("rossler")
    params = system.parameters()
    _, states = integrate(system, params, system.default_state, dt=0.01, steps=12000)
    first = poincare_section(states[2000:], axis=0, level=0.0, direction=1)
    second = poincare_section(states[2000:], axis=0, level=0.0, direction=1)
    assert len(first) > 5
    np.testing.assert_array_equal(first, second)
    np.testing.assert_allclose(first[:, 0], 0.0, atol=1e-12)


def test_step_halving_shows_rk4_consistency_on_short_horizon():
    system = get_system("lorenz")
    result = step_halving_check(
        system, system.parameters(), system.default_state, dt=0.01, horizon=0.2
    )
    assert result["error_half_vs_quarter"] < result["error_dt_vs_half"]
    assert result["observed_order"] > 3.0


def test_lorenz_variational_spectrum_has_correct_volume_sum():
    system = get_system("lorenz")
    params = system.parameters()
    exponents = lyapunov_spectrum(
        system,
        params,
        system.default_state,
        dt=0.01,
        steps=7000,
        transient_steps=1500,
        renormalize_every=10,
    )
    assert exponents.shape == (3,)
    assert np.all(np.isfinite(exponents))
    expected_sum = system.divergence(np.zeros(3), params)
    assert float(np.sum(exponents)) == pytest.approx(expected_sum, abs=0.35)


def test_kaplan_yorke_dimension_known_example():
    assert kaplan_yorke_dimension([0.1, 0.0, -2.0]) == pytest.approx(2.05)
    assert kaplan_yorke_dimension([-1.0, -2.0, -3.0]) == 0.0


@pytest.mark.parametrize("name", sorted(SYSTEMS))
def test_divergence_certificates_are_hole_free(name):
    lean, coq, statement = emit_divergence_certificate(name)
    assert statement
    assert "sorry" not in lean
    assert "Admitted" not in coq
    assert "theorem" in lean
    assert "Qed." in coq


def test_recurrence_and_dimension_are_bounded_as_numerical_estimates():
    system = get_system("rossler")
    _, states = integrate(system, system.parameters(), system.default_state, dt=0.01, steps=5000)
    estimate = recurrence_and_correlation_estimates(states[1000:], max_points=250)
    assert 0.0 < estimate["recurrence_rate"] < 1.0
    assert np.isfinite(estimate["correlation_dimension"])
    assert "not proofs" in estimate["claim_boundary"]


def test_parameter_sweep_returns_finite_maxima():
    system = get_system("rossler")
    points = parameter_sweep(
        system,
        system.parameters(),
        "c",
        [4.5, 5.7, 6.5],
        system.default_state,
        dt=0.02,
        steps=2500,
        transient_steps=1000,
        keep_maxima=8,
    )
    assert points
    assert all(np.isfinite(point) for pair in points for point in pair)


def test_analysis_separates_numerical_evidence_from_certificate():
    analysis = analyze_attractor(
        "rossler",
        steps=3500,
        transient_steps=500,
        sample_every=2,
        lyapunov_steps=3500,
    )
    payload = analysis.summary()
    assert payload["system"] == "rossler"
    assert payload["certificate_hole_free"] is True
    assert len(payload["lyapunov_exponents"]) == 3
    assert "not formal proofs" in payload["claim_boundary"]


def test_runner_writes_complete_artifact_bundle(tmp_path):
    output = tmp_path / "attractor"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_attractor_forge.py"),
            "--system",
            "rossler",
            "--steps",
            "1800",
            "--transient",
            "300",
            "--sample-every",
            "2",
            "--lyapunov-steps",
            "1800",
            "--output-dir",
            str(output),
            "--skip-audit",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    expected = {
        "pipeline.json",
        "ledger.jsonl",
        "trajectory.csv",
        "poincare.csv",
        "projection_xy.svg",
        "projection_xz.svg",
        "projection_yz.svg",
        "poincare_return_map.svg",
        "lyapunov_spectrum.svg",
        "attractor_explorer.html",
        "rossler_divergence.lean",
        "rossler_divergence.v",
        "REPORT.md",
    }
    assert expected <= {path.name for path in output.iterdir()}
    assert "Visual structure is not a formal proof of chaos" in (
        output / "attractor_explorer.html"
    ).read_text(encoding="utf-8")
