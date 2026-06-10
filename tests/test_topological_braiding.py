"""Regression tests for Fibonacci anyon braiding correctness.

The original `fibonacci_braiding_matrix` divided the R-matrix by sqrt(phi) and
returned a non-unitary matrix; its test "passed" only by asserting the bug
(|det| = 1/phi). Anyon braiding must be unitary and satisfy the braid
(Yang-Baxter) relation. These tests pin the correct physics so it cannot
silently regress.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.quantum import topological_quantum as tq  # noqa: E402

PHI = (1 + np.sqrt(5)) / 2


def _unitary(M: np.ndarray) -> bool:
    M = np.asarray(M)
    return np.allclose(M @ M.conj().T, np.eye(M.shape[0]), atol=1e-12)


def test_fibonacci_f_matrix_is_unitary_and_involutory():
    F = tq.fibonacci_f_matrix()
    assert _unitary(F)
    assert np.allclose(F @ F, np.eye(2), atol=1e-12)  # F^2 = I
    # Standard form F = [[1/phi, 1/sqrt(phi)], [1/sqrt(phi), -1/phi]].
    assert np.isclose(F[0, 0].real, 1 / PHI)
    assert np.isclose(F[0, 1].real, 1 / np.sqrt(PHI))


def test_fibonacci_braid_generators_unitary():
    sigma1 = tq.fibonacci_braiding_matrix(0, 1)
    sigma2 = tq.fibonacci_braiding_matrix(1, 2)
    assert _unitary(sigma1)
    assert _unitary(sigma2)


def test_fibonacci_r_matrix_phases():
    sigma1 = tq.fibonacci_braiding_matrix(0, 1)
    phases = sorted(np.angle(np.linalg.eigvals(sigma1)) / np.pi)
    # R eigenvalue phases are -4pi/5 and 3pi/5.
    assert np.allclose(phases, [-4 / 5, 3 / 5], atol=1e-12)


def test_fibonacci_braid_relation_yang_baxter():
    s1 = tq.fibonacci_braiding_matrix(0, 1)
    s2 = tq.fibonacci_braiding_matrix(1, 2)
    # The defining braid-group relation s1 s2 s1 = s2 s1 s2.
    assert np.allclose(s1 @ s2 @ s1, s2 @ s1 @ s2, atol=1e-12)
    # And the module's own checker agrees (non-trivially: sigma2 mixes channels).
    yb = tq.yang_baxter_check("fibonacci")
    assert yb["yang_baxter_satisfied"]
    assert yb["difference_norm"] < 1e-10


def test_ising_braiding_is_unitary():
    # Sanity: the Ising generator was already correct (e^{i pi/8} diag(1, i)).
    assert _unitary(tq.ising_braiding_matrix(0, 1))
