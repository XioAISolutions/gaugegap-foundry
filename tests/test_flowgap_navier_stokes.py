"""Tests for the finite 2D incompressible Navier-Stokes surrogate (flowgap-0005).

Thresholds are set from observed behavior of the deterministic Taylor-Green run.
The properties asserted are honest finite-grid statements: determinism, monotone
viscous energy decay, divergence control by the projection, recovery of the exact
analytic decay rate, and improvement under grid refinement.
"""
from __future__ import annotations

import numpy as np

from gaugegap.flowgap_burgers import divergence_2d, projection_step_2d
from gaugegap.flowgap_navier_stokes import (
    CLAIM_BOUNDARY,
    simulate_navier_stokes_2d,
    taylor_green,
)


def test_run_is_deterministic():
    a = simulate_navier_stokes_2d(nx=12, ny=12, n_steps=40)
    b = simulate_navier_stokes_2d(nx=12, ny=12, n_steps=40)
    assert a["energy_history"] == b["energy_history"]
    assert np.array_equal(a["ux_final"], b["ux_final"])


def test_energy_decays_monotonically_under_viscosity():
    result = simulate_navier_stokes_2d(nx=16, ny=16, nu=0.02, n_steps=120)
    assert result["energy_monotone_nonincreasing"]
    assert result["energy_history"][-1] < result["energy_history"][0]


def test_taylor_green_recovers_analytic_decay_rate():
    result = simulate_navier_stokes_2d(nx=16, ny=16, nu=0.02, dt=1e-3, n_steps=150)
    # Observed ~1.1% on a 16x16 grid; allow generous headroom.
    assert result["decay_rate_relative_error"] < 0.05
    assert result["measured_energy_decay_rate"] > 0.0


def test_grid_refinement_improves_accuracy():
    coarse = simulate_navier_stokes_2d(nx=12, ny=12, nu=0.02, dt=1e-3, n_steps=120)
    fine = simulate_navier_stokes_2d(nx=24, ny=24, nu=0.02, dt=1e-3, n_steps=120)
    assert fine["decay_rate_relative_error"] < coarse["decay_rate_relative_error"]


def test_divergence_stays_bounded_through_the_run():
    result = simulate_navier_stokes_2d(nx=16, ny=16, n_steps=120)
    # Collocated scheme does not reach machine zero, but stays well controlled.
    assert result["max_divergence"] < 0.2


def test_projection_reduces_a_divergent_field():
    ux, uy = taylor_green(16, 16)
    x = np.linspace(0.0, 1.0, 16, endpoint=False)
    ux = ux + 0.3 * np.cos(2.0 * np.pi * x)[None, :]  # inject divergence
    dx = 1.0 / 16
    before = float(np.linalg.norm(divergence_2d(ux, uy, dx, dx)))
    res = projection_step_2d(ux, uy, 1e-3)
    assert res["divergence_after"] < 0.1 * before


def test_claim_boundary_is_finite_and_explicit():
    result = simulate_navier_stokes_2d(nx=8, ny=8, n_steps=10)
    assert result["claim_boundary"] == CLAIM_BOUNDARY
    assert "not a continuum" in CLAIM_BOUNDARY
