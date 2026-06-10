"""Known-answer tests for the single-link SU(3) electric Hamiltonian (A3).

The electric Kogut-Susskind link energy is the quadratic Casimir, so every
quantity here is an exact, textbook-known SU(3) value.
"""
from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.gaugegap_su3_link import (  # noqa: E402
    SU3LinkElectric,
    SU3LinkElectricConfig,
    electric_gap_closed_form,
    enumerate_irreps,
    su3_casimir,
    su3_dim,
)


def test_su3_dimensions_and_casimirs():
    # Textbook SU(3) irrep dimensions and quadratic Casimirs.
    assert su3_dim(0, 0) == 1 and su3_casimir(0, 0) == 0
    assert su3_dim(1, 0) == 3 and su3_casimir(1, 0) == Fraction(4, 3)
    assert su3_dim(0, 1) == 3 and su3_casimir(0, 1) == Fraction(4, 3)
    assert su3_dim(1, 1) == 8 and su3_casimir(1, 1) == 3
    assert su3_dim(2, 0) == 6 and su3_casimir(2, 0) == Fraction(10, 3)
    assert su3_dim(3, 0) == 10 and su3_casimir(3, 0) == 6


def test_enumerate_irreps_sorted_by_casimir():
    irreps = enumerate_irreps(cutoff=2)
    # (0,0) singlet first, then the degenerate 3 / 3bar pair.
    assert (irreps[0].p, irreps[0].q) == (0, 0)
    assert {(irreps[1].p, irreps[1].q), (irreps[2].p, irreps[2].q)} == {(1, 0), (0, 1)}
    casimirs = [r.casimir for r in irreps]
    assert casimirs == sorted(casimirs)


def test_ground_state_is_the_colour_singlet():
    m = SU3LinkElectric(SU3LinkElectricConfig(g_electric=1.0, cutoff=2))
    gap = m.compute_gap()
    assert gap["ground_energy"] == 0.0
    assert gap["ground_degeneracy"] == 1  # singlet, dim^2 = 1
    assert gap["method"] == "exact_diagonalization"


def test_electric_gap_closed_form():
    for g in (0.5, 1.0, 1.7):
        m = SU3LinkElectric(SU3LinkElectricConfig(g_electric=g, cutoff=2))
        gap = m.compute_gap()["gap"]
        # Gap to the fundamental: (g^2/2) * 4/3 = 2 g^2 / 3.
        assert np.isclose(gap, 2.0 * g**2 / 3.0)
        assert np.isclose(gap, electric_gap_closed_form(g))


def test_level_degeneracies():
    m = SU3LinkElectric(SU3LinkElectricConfig(g_electric=1.0, cutoff=2))
    levels = m.levels()
    # Fundamental level: 3 (+) 3bar => 3^2 + 3^2 = 18-fold degenerate.
    fund = levels[1]
    assert np.isclose(fund["energy"], 2.0 / 3.0)
    assert fund["degeneracy"] == 18
    # Adjoint level: 8^2 = 64-fold.
    adj = next(L for L in levels if np.isclose(L["casimir"], 3.0))
    assert adj["degeneracy"] == 64


def test_hamiltonian_is_diagonal_and_dimension_matches():
    m = SU3LinkElectric(SU3LinkElectricConfig(g_electric=1.0, cutoff=2))
    H = m.hamiltonian_dense()
    assert np.allclose(H, H.T)
    assert np.allclose(H, np.diag(np.diag(H)))
    # Hilbert dimension is the sum of dim(R)^2 over the truncated irreps.
    expected = sum(su3_dim(p, q) ** 2 for p in range(3) for q in range(3))
    assert m.hilbert_dim == expected


def test_gap_scales_quadratically_with_coupling():
    g1 = SU3LinkElectric(SU3LinkElectricConfig(g_electric=1.0, cutoff=1)).compute_gap()["gap"]
    g2 = SU3LinkElectric(SU3LinkElectricConfig(g_electric=2.0, cutoff=1)).compute_gap()["gap"]
    assert np.isclose(g2 / g1, 4.0)  # gap ~ g^2
