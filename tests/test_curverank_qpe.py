"""Tests for CurveRank quantum phase estimation (QPE).

The phase<->eigenvalue arithmetic is tested without any quantum backend so the
core regression (no phase aliasing of the target eigenvalue) runs everywhere.
The end-to-end circuit tests are skipped unless the optional ``qiskit`` /
``qiskit-aer`` stack is installed.
"""
from __future__ import annotations

import sys
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.curverank_operators import berry_keating_xp
from gaugegap.curverank_qpe import (
    choose_evolution_time,
    choose_evolution_time_windowed,
    eigenvalue_to_phase,
    measured_phase_to_eigenvalue,
    pad_to_power_of_two,
    unwrap_phase_to_eigenvalue,
)


def _qiskit_available() -> bool:
    try:
        import qiskit  # noqa: F401
        import qiskit_aer  # noqa: F401
    except ImportError:
        return False
    return True


class TestEvolutionTime(unittest.TestCase):
    def test_safety_must_be_in_open_unit_interval(self):
        with self.assertRaises(ValueError):
            choose_evolution_time([1.0, 2.0], safety=0.0)
        with self.assertRaises(ValueError):
            choose_evolution_time([1.0, 2.0], safety=1.0)

    def test_zero_spectrum_rejected(self):
        with self.assertRaises(ValueError):
            choose_evolution_time([0.0, 0.0])

    def test_keeps_phases_inside_unit_window(self):
        # With tau = safety * pi / R every |phi| <= safety/2 < 0.5, so the whole
        # spectrum lives in a width-< 1 window and never wraps.
        evals = np.linalg.eigvalsh(berry_keating_xp(12))
        safety = 0.8
        tau = choose_evolution_time(evals, safety=safety)
        for e in evals:
            signed = (-e * tau / (2 * np.pi))
            self.assertLessEqual(abs(signed), safety / 2 + 1e-12)


class TestPhaseRoundTrip(unittest.TestCase):
    def test_phase_is_in_unit_interval(self):
        tau = 0.2
        for e in (-5.0, -0.3, 0.0, 0.7, 9.1):
            phi = eigenvalue_to_phase(e, tau)
            self.assertGreaterEqual(phi, 0.0)
            self.assertLess(phi, 1.0)

    def test_round_trip_recovers_eigenvalue(self):
        evals = np.linalg.eigvalsh(berry_keating_xp(16))
        tau = choose_evolution_time(evals)
        for e in evals:
            recovered = measured_phase_to_eigenvalue(eigenvalue_to_phase(e, tau), tau)
            self.assertAlmostEqual(recovered, float(e), places=9)

    def test_measured_phase_inversion_rejects_zero_tau(self):
        with self.assertRaises(ValueError):
            measured_phase_to_eigenvalue(0.25, 0.0)


class TestNoAliasing(unittest.TestCase):
    def test_distinct_eigenvalues_have_distinct_phases(self):
        evals = np.linalg.eigvalsh(berry_keating_xp(20))
        tau = choose_evolution_time(evals)
        phases = sorted(eigenvalue_to_phase(e, tau) for e in evals)
        gaps = np.diff(phases)
        self.assertTrue(np.all(gaps > 1e-9), "phases must be distinct (no aliasing)")

    def test_old_tau_aliases_target_to_zero_phase(self):
        # Regression for the original bug: tau = 2*pi / |E_1| sends the very
        # eigenvalue it tries to measure to phi = 1 == 0 (mod 1).
        evals = np.linalg.eigvalsh(berry_keating_xp(12))
        target = min(e for e in evals if e > 1e-9)

        tau_old = 2 * np.pi / abs(target)
        self.assertAlmostEqual(eigenvalue_to_phase(target, tau_old), 0.0, places=9)

        # The repaired choice keeps the target phase well clear of 0.
        tau_new = choose_evolution_time(evals)
        phi_new = eigenvalue_to_phase(target, tau_new)
        self.assertGreater(min(phi_new, 1.0 - phi_new), 1e-3)


class TestPadding(unittest.TestCase):
    def test_no_padding_when_already_power_of_two(self):
        H = np.eye(8, dtype=complex)
        v = np.ones(8, dtype=complex)
        Hp, vp = pad_to_power_of_two(H, v)
        self.assertEqual(Hp.shape, (8, 8))
        self.assertIs(Hp, H)
        np.testing.assert_array_equal(vp, v)

    def test_pads_to_next_power_of_two_with_zero_block(self):
        H = np.diag(np.arange(1.0, 11.0)).astype(complex)  # dim 10 -> 16
        v = np.zeros(10, dtype=complex)
        v[3] = 1.0
        Hp, vp = pad_to_power_of_two(H, v)
        self.assertEqual(Hp.shape, (16, 16))
        # Original block preserved, padded eigenvalues are exactly 0.
        np.testing.assert_array_equal(Hp[:10, :10], H)
        self.assertEqual(np.count_nonzero(Hp[10:, :]), 0)
        self.assertEqual(vp.shape, (16,))
        self.assertEqual(vp[3], 1.0)
        self.assertEqual(np.count_nonzero(vp[10:]), 0)


@unittest.skipUnless(_qiskit_available(), "qiskit/qiskit-aer optional dependency not installed")
class TestQPEEndToEnd(unittest.TestCase):
    def test_recovers_exact_dyadic_phase(self):
        # With safety=0.75 the maximum-magnitude eigenvalue gets signed phase
        # exactly -0.375 -> phi = 0.625 = 0.101b, which is exact in 3 counting
        # qubits. QPE must read it back exactly and recover the eigenvalue with
        # zero discretization error.
        from gaugegap.curverank_qpe import estimate_eigenvalue_qpe

        target = 2.5  # the (single) largest-magnitude eigenvalue
        H = np.diag([0.0, target]).astype(complex)
        vec = np.array([0.0, 1.0], dtype=complex)

        res = estimate_eigenvalue_qpe(
            H, vec, n_precision=3, shots=2048, safety=0.75,
            eigenvalues=np.array([0.0, target]),
        )
        self.assertEqual(res["measured_phase"], 0.625)
        self.assertAlmostEqual(res["estimated_eigenvalue"], target, places=9)

    def test_recovers_berry_keating_eigenvalue(self):
        # End-to-end on a real candidate operator: prepare the eigenstate of the
        # smallest positive eigenvalue and confirm QPE recovers it to within the
        # phase resolution.
        from gaugegap.curverank_qpe import estimate_eigenvalue_qpe

        H = berry_keating_xp(8)
        evals, evecs = np.linalg.eigh(H)
        idx = int(np.argmin(np.where(evals > 1e-9, evals, np.inf)))
        target = float(evals[idx])

        n_precision = 8
        res = estimate_eigenvalue_qpe(
            H, evecs[:, idx], n_precision=n_precision, shots=4096, eigenvalues=evals
        )
        resolution = (2 * np.pi / res["evolution_time"]) / (2 ** n_precision)
        self.assertLessEqual(abs(res["estimated_eigenvalue"] - target), 2 * resolution)


class TestWindowing(unittest.TestCase):
    def test_windowed_tau_is_larger_than_global(self):
        # A tight window (small radius) yields a larger tau than the global
        # spectral-radius choice -> finer eigenvalue resolution.
        evals = np.linalg.eigvalsh(berry_keating_xp(12))
        radius = float(np.max(np.abs(evals)))
        tau_global = choose_evolution_time(evals)
        tau_window = choose_evolution_time_windowed(0.5)
        self.assertGreater(tau_window, tau_global)
        # Resolution improvement equals the radius ratio.
        self.assertAlmostEqual(tau_window / tau_global, radius / 0.5, places=6)

    def test_window_radius_validation(self):
        with self.assertRaises(ValueError):
            choose_evolution_time_windowed(0.0)
        with self.assertRaises(ValueError):
            choose_evolution_time_windowed(1.0, safety=1.5)

    def test_unwrap_selects_in_window_candidate(self):
        # tau scaled to a window of radius 0.5 about center 5.0; a phase that
        # naively inverts far outside the window must be unwrapped back into it.
        tau = choose_evolution_time_windowed(0.5)
        center = 5.0
        true_E = 5.2
        phase = eigenvalue_to_phase(true_E, tau)  # in [0,1), wraps many times
        recovered = unwrap_phase_to_eigenvalue(phase, tau, center)
        self.assertAlmostEqual(recovered, true_E, places=9)

    def test_unwrap_rejects_zero_tau(self):
        with self.assertRaises(ValueError):
            unwrap_phase_to_eigenvalue(0.25, 0.0, 1.0)


@unittest.skipUnless(_qiskit_available(), "qiskit/qiskit-aer optional dependency not installed")
class TestWindowedQPEEndToEnd(unittest.TestCase):
    def test_windowing_beats_global_resolution(self):
        from gaugegap.curverank_qpe import estimate_eigenvalue_qpe

        H = berry_keating_xp(8)
        evals, evecs = np.linalg.eigh(H)
        idx = int(np.argmin(np.where(evals > 1e-9, evals, np.inf)))
        target = float(evals[idx])

        g = estimate_eigenvalue_qpe(
            H, evecs[:, idx], n_precision=6, shots=4096, eigenvalues=evals,
        )
        w = estimate_eigenvalue_qpe(
            H, evecs[:, idx], n_precision=6, shots=4096, eigenvalues=evals,
            window=(target, 0.5),
        )
        self.assertTrue(w["windowed"])
        self.assertGreater(w["evolution_time"], g["evolution_time"])
        self.assertLessEqual(
            abs(w["estimated_eigenvalue"] - target),
            abs(g["estimated_eigenvalue"] - target) + 1e-9,
        )


@unittest.skipUnless(_qiskit_available(), "qiskit/qiskit-aer optional dependency not installed")
class TestTrotterAndIterativeQPE(unittest.TestCase):
    def test_pauli_decomposition_reconstructs_matrix(self):
        from gaugegap.curverank_qpe import hamiltonian_to_sparse_pauli

        H = berry_keating_xp(8)  # 3-qubit Hermitian
        op = hamiltonian_to_sparse_pauli(H)
        self.assertEqual(op.num_qubits, 3)
        np.testing.assert_allclose(np.asarray(op.to_matrix()), H, atol=1e-9)

    def test_trotter_recovers_exact_dyadic_phase(self):
        # A diagonal Hamiltonian is a sum of commuting Z-strings, so Lie-Trotter
        # is exact -> the trotter path must reproduce the dense dyadic result.
        from gaugegap.curverank_qpe import estimate_eigenvalue_qpe

        target = 2.5
        H = np.diag([0.0, target]).astype(complex)
        vec = np.array([0.0, 1.0], dtype=complex)
        res = estimate_eigenvalue_qpe(
            H, vec, n_precision=3, shots=2048, safety=0.75,
            eigenvalues=np.array([0.0, target]), method="trotter", reps=2,
        )
        self.assertEqual(res["method"], "trotter")
        self.assertEqual(res["measured_phase"], 0.625)
        self.assertAlmostEqual(res["estimated_eigenvalue"], target, places=9)

    def test_iterative_recovers_exact_dyadic_phase(self):
        # Iterative QPE on a diagonal (commuting) Hamiltonian is also exact.
        from gaugegap.curverank_qpe import estimate_eigenvalue_iterative_qpe

        target = 2.5
        H = np.diag([0.0, target]).astype(complex)
        vec = np.array([0.0, 1.0], dtype=complex)
        res = estimate_eigenvalue_iterative_qpe(
            H, vec, n_iterations=3, shots=2048, safety=0.75,
            eigenvalues=np.array([0.0, target]), reps=2,
        )
        self.assertEqual(res["method"], "iterative")
        self.assertEqual(res["n_qubits"], 2)  # 1 system + 1 ancilla
        self.assertEqual(res["measured_phase"], 0.625)
        self.assertAlmostEqual(res["estimated_eigenvalue"], target, places=9)

    def test_iterative_uses_single_ancilla(self):
        # The headline NISQ benefit: width is system + 1 regardless of precision.
        from gaugegap.curverank_qpe import estimate_eigenvalue_iterative_qpe

        H = berry_keating_xp(4)  # 2-qubit system
        evals, evecs = np.linalg.eigh(H)
        idx = int(np.argmin(np.where(evals > 1e-9, evals, np.inf)))
        res = estimate_eigenvalue_iterative_qpe(
            H, evecs[:, idx], n_iterations=4, shots=1024, eigenvalues=evals, reps=2,
        )
        self.assertEqual(res["n_qubits"], 3)  # 2 system + 1 ancilla
        self.assertEqual(len(res["phase_bits"]), 4)


if __name__ == "__main__":
    unittest.main()
