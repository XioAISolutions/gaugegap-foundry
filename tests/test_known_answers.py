"""Known-answer regression tests (issue #12, A5).

Each test pins a computed quantity to an *independently known exact answer* —
derived analytically or from a textbook identity, not from a prior run of this
code. These guard against silent numerical regressions in the finite-system
benchmarks (Z2 plaquette, compact U(1), CurveRank operators) and the SU(3)
prototype's Gell-Mann algebra.

CLAIM BOUNDARY: these are exact checks on finite toy operators; they make no
continuum or first-principles claim.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


# ===========================================================================
# Z2 single plaquette.  H = -J * (Z0 Z1 Z2 Z3) - h * (X0+X1+X2+X3).
# Each Xi anticommutes with the parity P = ZZZZ, and B = sum Xi has the exact
# spectrum {-4,-2,0,2,4} with multiplicities {1,4,6,4,1}.  Because {P, B} = 0,
# H block-diagonalizes into 2x2 blocks with eigenvalues +/- sqrt(J^2 + (h b)^2)
# for each B-eigenvalue b.  Hence the full 16-level spectrum is known in closed
# form, with ground energy -sqrt(J^2 + 16 h^2).
# ===========================================================================

def _z2_analytic_spectrum(J: float, h: float) -> np.ndarray:
    # B = sum Xi has |b| in {4, 2, 0} contributing {1, 4, 3} +/- pairs
    # (16 levels total); each pair has energies +/- sqrt(J^2 + (h|b|)^2).
    levels = []
    for absb, npairs in ((4, 1), (2, 4), (0, 3)):
        e = math.sqrt(J * J + (h * absb) ** 2)
        for _ in range(npairs):
            levels.extend([-e, e])
    return np.array(sorted(levels))


def test_z2_single_plaquette_exact_spectrum():
    from gaugegap.models.z2_plaquette import spectrum

    J, h = 1.0, 0.2
    numeric = spectrum(n_plaquettes=1, plaquette_coupling=J, transverse_field=h)
    analytic = _z2_analytic_spectrum(J, h)
    assert numeric.shape == (16,)
    np.testing.assert_allclose(numeric, analytic, atol=1e-10)


def test_z2_ground_energy_and_gap_closed_form():
    from gaugegap.models.z2_plaquette import mass_gap

    J, h = 1.0, 0.2
    gap, ground, first = mass_gap(n_plaquettes=1, plaquette_coupling=J, transverse_field=h)
    assert math.isclose(ground, -math.sqrt(J**2 + 16 * h**2), abs_tol=1e-10)
    assert math.isclose(first, -math.sqrt(J**2 + 4 * h**2), abs_tol=1e-10)
    assert math.isclose(gap, math.sqrt(J**2 + 16 * h**2) - math.sqrt(J**2 + 4 * h**2), abs_tol=1e-10)


def test_z2_limiting_cases():
    from gaugegap.models.z2_plaquette import mass_gap, spectrum

    # field = 0: H = -J*ZZZZ has eigenvalues -J (8-fold) and +J (8-fold).
    eig = spectrum(n_plaquettes=1, plaquette_coupling=1.0, transverse_field=0.0)
    np.testing.assert_allclose(eig, [-1.0] * 8 + [1.0] * 8, atol=1e-10)
    # coupling -> 0: H = -h*sum Xi, gap between ground (-4h) and first (-2h) is 2h.
    gap, _, _ = mass_gap(n_plaquettes=1, plaquette_coupling=1e-12, transverse_field=0.2)
    assert math.isclose(gap, 2 * 0.2, abs_tol=1e-6)


# ===========================================================================
# Compact U(1) link algebra and the electric-only limit.
# ===========================================================================

def test_u1_link_operators_algebra():
    from gaugegap.gaugegap_u1 import u1_link_operators

    t = 3
    E, U_plus, U_minus = u1_link_operators(t)
    dim = 2 * t + 1
    # Electric operator is diagonal with integer eigenvalues -t..t.
    np.testing.assert_array_equal(np.diag(E), np.arange(-t, t + 1))
    # U_minus is the adjoint of U_plus, and U_plus is unitary (a cyclic shift).
    np.testing.assert_allclose(U_minus, U_plus.conj().T)
    np.testing.assert_allclose(U_plus @ U_minus, np.eye(dim), atol=1e-12)
    np.testing.assert_allclose(U_minus @ U_plus, np.eye(dim), atol=1e-12)


def test_u1_electric_only_spectrum():
    from gaugegap.gaugegap_u1 import u1_mass_gap, u1_spectrum

    # g_magnetic = 0: H = (g_e^2/2) sum_l E_l^2, minimized by all m=0 (E=0);
    # the first excitation raises one link to m=+-1, costing g_e^2/2.
    g_e = 1.3
    eig = u1_spectrum(n_links=2, g_electric=g_e, g_magnetic=0.0, truncation=2)
    assert math.isclose(eig[0], 0.0, abs_tol=1e-10)
    gap, _, _ = u1_mass_gap(n_links=2, g_electric=g_e, g_magnetic=0.0, truncation=2)
    assert math.isclose(gap, g_e**2 / 2.0, abs_tol=1e-10)


# ===========================================================================
# CurveRank operators and the certified eigensolver.
# ===========================================================================

def test_curverank_xp_is_hermitian_with_symmetric_spectrum():
    from gaugegap.curverank_operators import berry_keating_xp

    H = berry_keating_xp(n_basis=12)
    np.testing.assert_allclose(H, H.conj().T, atol=1e-12)
    eig = np.linalg.eigvalsh(H)
    # The symmetrized xp operator is odd under reflection, so its spectrum is
    # symmetric about 0: the sorted eigenvalues equal the negated, reversed set.
    np.testing.assert_allclose(np.sort(eig), -np.sort(eig)[::-1], atol=1e-10)


def test_certified_eigensolver_known_2x2():
    from gaugegap.rigorous.interval_arithmetic import (
        IntervalMatrix,
        verified_hermitian_eigenvalues,
    )

    # [[2,1],[1,2]] has exact eigenvalues 1 and 3.
    M = IntervalMatrix.from_floats([[2.0, 1.0], [1.0, 2.0]])
    encs = verified_hermitian_eigenvalues(M)
    assert encs[0].contains(1.0) and encs[1].contains(3.0)
    # Enclosures are tight (residual ~1e-13, far below 1).
    assert all(float(e.width()) < 1e-9 for e in encs)


def test_curverank_reference_constants():
    from gaugegap.curverank_spectral import riemann_zero_targets, spectral_mismatch

    # First non-trivial Riemann zero (known to ~12 digits).
    assert math.isclose(riemann_zero_targets(1)[0], 14.134725141734693, abs_tol=1e-9)
    # A spectrum compared against itself has exactly zero mismatch.
    z = riemann_zero_targets(5)
    assert spectral_mismatch(z, z) == 0.0


# ===========================================================================
# SU(3) prototype: the Gell-Mann generator algebra (textbook identities).
# ===========================================================================

def test_su3_gell_mann_identities():
    from gaugegap.gaugegap_su3_pure import SU3PureGaugeConfig, SU3PureGaugeLattice

    lattice = SU3PureGaugeLattice(SU3PureGaugeConfig(2, 2, 1.0, 1.0, 0.5))
    G = lattice.generators
    assert len(G) == 8 and all(g.shape == (3, 3) for g in G)

    for g in G:
        np.testing.assert_allclose(g, g.conj().T, atol=1e-12)      # Hermitian
        assert abs(np.trace(g)) < 1e-12                            # traceless

    # Orthonormality: Tr(lambda_a lambda_b) = 2 delta_ab.
    gram = np.array([[np.trace(G[a] @ G[b]).real for b in range(8)] for a in range(8)])
    np.testing.assert_allclose(gram, 2.0 * np.eye(8), atol=1e-12)

    # Fundamental Casimir: sum_a lambda_a^2 = (16/3) I  (i.e. C2 = 4/3 for T=lambda/2).
    casimir = sum(g @ g for g in G)
    np.testing.assert_allclose(casimir, (16.0 / 3.0) * np.eye(3), atol=1e-12)


def test_su3_structure_constant_f123():
    from gaugegap.gaugegap_su3_pure import SU3PureGaugeConfig, SU3PureGaugeLattice

    G = SU3PureGaugeLattice(SU3PureGaugeConfig(2, 2, 1.0, 1.0, 0.5)).generators
    # [lambda_a, lambda_b] = 2 i f_abc lambda_c; the totally antisymmetric
    # structure constant f_123 = 1, extracted via Tr([l1,l2] l3) = 2 i f_123 * 2.
    comm = G[0] @ G[1] - G[1] @ G[0]
    f123 = (np.trace(comm @ G[2]) / (4j)).real
    assert math.isclose(f123, 1.0, abs_tol=1e-12)
