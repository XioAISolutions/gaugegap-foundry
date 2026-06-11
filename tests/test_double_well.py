"""Tests for certified symmetric double-well enclosures."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.double_well import (  # noqa: E402
    certified_double_well_levels,
    certified_level_lower_bound,
    certified_tunnelling_splitting,
    double_well_hamiltonian_interval,
)


def _true_levels(lam: float, M: int = 160, pad: int = 8, k: int = 4) -> np.ndarray:
    K = M + pad
    n = np.arange(1, K)
    x = np.zeros((K, K))
    x[np.arange(K - 1), np.arange(1, K)] = np.sqrt(n / 2)
    x = x + x.T
    x2 = (x @ x)[:M, :M]
    x4 = (x @ x @ x @ x)[:M, :M]
    H = np.diag(np.arange(M) + 0.5) - x2 + lam * x4
    return np.sort(np.linalg.eigvalsh(H))[:k]


def test_double_well_levels_bracket_true_levels():
    lam = 0.1
    true = _true_levels(lam)
    for L in certified_double_well_levels(n_basis=40, lam=lam, n_levels=4):
        assert L.lower <= true[L.n] <= L.upper      # genuine two-sided bracket
        assert L.lower < L.upper


def test_comparison_lower_bounds_are_valid():
    lam = 0.1
    true = _true_levels(lam)
    for n in range(3):
        assert certified_level_lower_bound(n, lam) <= true[n] + 1e-9


def test_splitting_encloses_same_truncation_float():
    # The certified enclosure rigorously contains the truncated matrix's splitting.
    s = certified_tunnelling_splitting(n_basis=40, lam=0.1)
    A = double_well_hamiltonian_interval(40, 0.1).to_numpy()
    ev = np.sort(np.linalg.eigvalsh(A))
    float_split = ev[1] - ev[0]
    assert s.lower <= float_split <= s.upper
    assert s.lower > 0  # the doublet is split (positive) at this truncation


def test_splitting_is_converged():
    # The truncated splitting is stable in N (evidence it equals the true value).
    s40 = certified_tunnelling_splitting(n_basis=40, lam=0.1).midpoint
    s50 = certified_tunnelling_splitting(n_basis=50, lam=0.1).midpoint
    assert abs(s40 - s50) < 1e-8


def test_barrier_height_and_input_guards():
    s = certified_tunnelling_splitting(n_basis=30, lam=0.1)
    assert np.isclose(s.barrier_height, 1.0 / (16 * 0.1))
    with pytest.raises(ValueError):
        double_well_hamiltonian_interval(n_basis=20, lam=0.1, pad=2)
    with pytest.raises(ValueError):
        double_well_hamiltonian_interval(n_basis=20, lam=-1.0)
