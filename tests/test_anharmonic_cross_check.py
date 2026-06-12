"""Third-library cross-checks of the certified anharmonic enclosure.

The certified ground-state eigenvalue enclosure (mpmath.iv directed rounding +
residual bound) is independently corroborated by:
  1. numpy.linalg.eigvalsh (float64),
  2. mpmath.eigsy (high-precision symmetric eigensolver, a different code path),
  3. Arb ball arithmetic (python-flint) -- the residual radius recomputed in a
     wholly separate rigorous library (skipped if python-flint is absent).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.anharmonic import (  # noqa: E402
    anharmonic_hamiltonian_interval,
    certified_anharmonic_bounds,
    mpmath_ground_eigenvalue,
)

N, LAM = 20, 1.0


def _certified_ground():
    return certified_anharmonic_bounds(n_basis=N, lam=LAM, n_levels=1).enclosures[0]


def test_numpy_eigval_inside_certified_enclosure():
    enc = _certified_ground()
    A = anharmonic_hamiltonian_interval(N, LAM).to_numpy()
    e0 = float(np.sort(np.linalg.eigvalsh(A))[0])
    assert float(enc.lower) <= e0 <= float(enc.upper)


def test_mpmath_eigsy_inside_certified_enclosure():
    enc = _certified_ground()
    e0 = mpmath_ground_eigenvalue(n_basis=N, lam=LAM, dps=40)
    assert float(enc.lower) <= e0 <= float(enc.upper)


def test_arb_residual_corroborates_certified_radius():
    flint = pytest.importorskip("flint")
    flint.ctx.prec = 256

    enc = _certified_ground()
    matrix = anharmonic_hamiltonian_interval(N, LAM)
    A = matrix.to_numpy()
    theta, V = np.linalg.eigh(A)
    j = int(np.argmin(theta))
    x = V[:, j]
    th = float(theta[j])

    # Residual ||A x - theta x|| / ||x|| in Arb ball arithmetic (independent of mpmath).
    def arb_entry(iv):
        mid = (iv.lower + iv.upper) / 2
        rad = (iv.upper - iv.lower) / 2
        import mpmath as mp
        return flint.arb(mp.nstr(mid, 60), float(rad) if rad > 0 else 0.0)

    n = matrix.m
    Aarb = [[arb_entry(matrix.entries[i][k]) for k in range(n)] for i in range(n)]
    xarb = [flint.arb(float(x[k])) for k in range(n)]
    tharb = flint.arb(th)
    res_sq = flint.arb(0)
    for row in range(n):
        acc = flint.arb(0)
        for col in range(n):
            acc = acc + Aarb[row][col] * xarb[col]
        acc = acc - tharb * xarb[row]
        res_sq = res_sq + acc * acc
    norm_sq = flint.arb(0)
    for k in range(n):
        norm_sq = norm_sq + xarb[k] * xarb[k]
    import mpmath as mp
    r_hi = mp.mpf((res_sq.sqrt() / norm_sq.sqrt()).upper().str(40, radius=False))

    rho_mp = float(enc.width() / 2)  # certified residual radius (mpmath.iv)
    # Both libraries bound the same ||A x - theta x|| / ||x|| from identical
    # float inputs, so the certified radius and Arb's residual agree to high
    # relative precision (~machine epsilon here).
    assert abs(rho_mp - float(r_hi)) <= 1e-9 * max(float(r_hi), 1e-30) + 1e-18
    # The certified enclosure contains the numpy eigenvalue.
    assert float(enc.lower) <= th <= float(enc.upper)
