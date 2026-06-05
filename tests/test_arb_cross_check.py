"""Optional independent cross-check of the certified radii against Arb.

This test corroborates the ``mpmath.iv`` certified eigenvalue radii with a fully
independent rigorous arithmetic backend (Arb, via ``python-flint``). It is
skipped automatically when ``python-flint`` is not installed, so it is not a CI
dependency; install ``python-flint`` to exercise it during independent review.

See ``scripts/cross_check_arb.py`` for the standalone, multi-family version.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

flint = pytest.importorskip("flint")

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import mpmath as mp

from gaugegap.curverank_operators import (
    berry_keating_xp_interval,
    quantum_graph_laplacian_interval,
)
from gaugegap.rigorous.interval_arithmetic import (
    Interval,
    certified_residual_radius,
)

flint.ctx.prec = 256  # bits, tighter than mpmath's 50 decimal digits


def _arb_entry(iv: Interval):
    mid = (iv.lower + iv.upper) / 2
    rad = (iv.upper - iv.lower) / 2
    return flint.arb(mp.nstr(mid, 60), float(rad) if rad > 0 else 0.0)


def _arb_radius_bounds(matrix, theta, x_col):
    n = matrix.m
    A = [[_arb_entry(matrix.entries[i][j]) for j in range(n)] for i in range(n)]
    x = [flint.arb(float(x_col[k])) for k in range(n)]
    th = flint.arb(float(theta))
    res_sq = flint.arb(0)
    for row in range(n):
        acc = flint.arb(0)
        for col in range(n):
            acc = acc + A[row][col] * x[col]
        acc = acc - th * x[row]
        res_sq = res_sq + acc * acc
    norm_x_sq = flint.arb(0)
    for k in range(n):
        norm_x_sq = norm_x_sq + x[k] * x[k]
    ratio = res_sq.sqrt() / norm_x_sq.sqrt()
    lo = mp.mpf(ratio.lower().str(50, radius=False))
    hi = mp.mpf(ratio.upper().str(50, radius=False))
    return lo, hi


@pytest.mark.parametrize(
    "matrix",
    [
        berry_keating_xp_interval(8),  # degenerate (doubled) spectrum
        quantum_graph_laplacian_interval(
            [(0, 1), (0, 2), (0, 3)],
            [1.0, float(np.sqrt(2)), float(np.sqrt(3))],
            6,
        ),
    ],
)
def test_arb_corroborates_mpmath_radius(matrix):
    theta, X = np.linalg.eigh(matrix.to_numpy())
    for i in range(matrix.m):
        rho_mp = certified_residual_radius(matrix, float(theta[i]), X[:, i])
        r_lo, r_hi = _arb_radius_bounds(matrix, float(theta[i]), X[:, i])

        # Safety: mpmath's certified radius must not undercut Arb's rigorous
        # lower bound on the true radius (else the enclosure could miss lambda).
        assert rho_mp + mp.mpf("1e-40") >= r_lo
        # Agreement: the two independent rigorous backends compute the same
        # certified radius to many digits.
        denom = r_hi if r_hi > mp.mpf("1e-300") else mp.mpf("1e-300")
        assert abs(rho_mp - r_hi) / denom < mp.mpf("1e-30")
