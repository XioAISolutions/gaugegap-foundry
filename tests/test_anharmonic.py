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
    certified_level_lower_bound,
    certified_two_sided_spectrum,
)

# Well-documented ground-state energy of H = 1/2 p^2 + 1/2 x^2 + x^4.
E0_REF = 0.8037706512
# High-precision true low-lying levels (lambda = 1), large-N diagonalization.
TRUE_LEVELS_LAM1 = [0.8037706512, 2.7378922600, 5.1792916925]


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


def test_temple_uses_sharpened_e1_lower_bound():
    enc = certified_ground_state_enclosure(n_basis=30, lam=1.0)
    # The comparison-oscillator beta is much sharper than the operator bound 3/2.
    assert enc.e1_lower_bound > 1.5
    assert enc.e1_lower_bound <= TRUE_LEVELS_LAM1[1] + 1e-9   # still a valid lower bound on E1
    assert float(enc.rayleigh.upper) < enc.e1_lower_bound     # Temple precondition


def test_comparison_oscillator_lower_bounds_are_valid():
    # E_n(H) >= comparison-oscillator bound, for every level (rigorous lower bound).
    for n in range(3):
        lb = certified_level_lower_bound(n, lam=1.0)
        assert lb <= TRUE_LEVELS_LAM1[n] + 1e-9
    # And they are nontrivial (above the harmonic values for the excited states).
    assert certified_level_lower_bound(1, lam=1.0) > 1.5


def test_two_sided_spectrum_brackets_true_levels():
    spectrum = certified_two_sided_spectrum(n_basis=30, lam=1.0, n_levels=3)
    assert len(spectrum) == 3
    for L in spectrum:
        assert L.lower <= TRUE_LEVELS_LAM1[L.n] <= L.upper   # genuine two-sided bracket
        assert L.lower < L.upper
    # The ground state is sharpened by Temple and is far tighter than E1/E2.
    assert spectrum[0].method == "Temple"
    assert spectrum[0].width < 1e-4


def test_e0_enclosure_brackets_reference_across_lambda():
    # The reference constants are only ~10-digit; allow that much slack (some
    # enclosures are tighter than the references are quoted).
    tol = 1e-9
    for lam, ref in REFERENCE_E0.items():
        enc = certified_ground_state_enclosure(n_basis=30, lam=lam)
        assert enc.lower - tol <= ref <= enc.upper + tol
