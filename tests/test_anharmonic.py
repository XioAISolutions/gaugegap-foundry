"""Tests for certified variational bounds on the anharmonic oscillator."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pytest  # noqa: E402

from gaugegap.anharmonic import (  # noqa: E402
    REFERENCE_E0,
    anharmonic_hamiltonian_interval,
    certified_anharmonic_bounds,
    certified_ground_state_enclosure,
)

# Well-documented ground-state energy of H = 1/2 p^2 + 1/2 x^2 + x^4.
E0_REF = 0.8037706512


def test_harmonic_limit_is_exact():
    # lambda = 0 reduces to the harmonic oscillator: E_n = n + 1/2, exactly.
    b = certified_anharmonic_bounds(n_basis=6, lam=0.0, n_levels=5)
    for n, enc in enumerate(b.enclosures):
        assert enc.contains(n + 0.5)
        assert float(enc.width()) < 1e-9  # exact (zero-width up to rounding)


def test_certified_bound_is_an_upper_bound_on_true_energy():
    # Rayleigh-Ritz: the certified upper endpoint must lie at or above the true
    # ground-state energy (it bounds it from above).
    b = certified_anharmonic_bounds(n_basis=30, lam=1.0, n_levels=1)
    assert b.ground_upper_bound() >= E0_REF - 1e-9


def test_variational_bounds_decrease_with_truncation():
    # The variational upper bound is monotonically non-increasing in N.
    ub10 = certified_anharmonic_bounds(n_basis=10, lam=1.0, n_levels=1).ground_upper_bound()
    ub20 = certified_anharmonic_bounds(n_basis=20, lam=1.0, n_levels=1).ground_upper_bound()
    ub30 = certified_anharmonic_bounds(n_basis=30, lam=1.0, n_levels=1).ground_upper_bound()
    assert ub10 > ub20 > ub30 >= E0_REF - 1e-9


def test_bound_converges_to_reference():
    # At N=30 the certified upper bound is within 1e-4 of the known value.
    ub = certified_anharmonic_bounds(n_basis=30, lam=1.0, n_levels=1).ground_upper_bound()
    assert abs(ub - E0_REF) < 1e-4


def test_enclosures_are_tight():
    b = certified_anharmonic_bounds(n_basis=20, lam=1.0, n_levels=4)
    assert all(float(e.width()) < 1e-6 for e in b.enclosures)


def test_pad_must_keep_x4_block_exact():
    with pytest.raises(ValueError):
        anharmonic_hamiltonian_interval(n_basis=8, lam=1.0, pad=2)


def test_temple_two_sided_encloses_true_energy():
    # The Temple lower bound + Rayleigh-Ritz upper bound bracket the true E0
    # from BOTH sides (a genuine certified enclosure, not just an upper bound).
    enc = certified_ground_state_enclosure(n_basis=30, lam=1.0)
    assert enc.lower < enc.upper
    assert enc.lower <= E0_REF <= enc.upper
    # The lower bound is a real (Temple) lower bound, strictly below the truth.
    assert enc.lower < E0_REF


def test_temple_enclosure_tightens_with_truncation():
    w20 = certified_ground_state_enclosure(n_basis=20, lam=1.0).width
    w30 = certified_ground_state_enclosure(n_basis=30, lam=1.0).width
    assert w30 < w20  # variance shrinks, enclosure tightens


def test_temple_uses_rigorous_e1_lower_bound():
    enc = certified_ground_state_enclosure(n_basis=30, lam=1.0)
    # beta = 3/2 from the operator bound E1 >= 3/2 (lambda x^4 >= 0).
    assert enc.e1_lower_bound == 1.5
    assert float(enc.rayleigh.upper) < enc.e1_lower_bound  # Temple precondition
