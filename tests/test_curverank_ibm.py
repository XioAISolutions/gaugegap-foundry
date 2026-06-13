"""Tests for the CurveRank IBM QPE sweep script.

Runs the local IBM/Aer emulator path (no credentials) and checks that windowed
dense QPE recovers the targeted eigenvalues within the phase resolution and emits
the results bundle. Skipped unless qiskit/qiskit-aer is installed.
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _qiskit_available() -> bool:
    try:
        import qiskit  # noqa: F401
        import qiskit_aer  # noqa: F401
    except ImportError:
        return False
    return True


def _load():
    path = ROOT / "scripts" / "run_curverank_ibm.py"
    spec = importlib.util.spec_from_file_location("cr_ibm", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@unittest.skipUnless(_qiskit_available(), "qiskit/qiskit-aer not installed")
class TestCurveRankIBM(unittest.TestCase):
    def test_dense_emulator_recovers_within_resolution(self):
        mod = _load()
        row = mod.run_one(
            n_basis=8, n_precision=6, shots=4096, reps=2, window_radius=0.5,
            use_emulator=True, device="aer_simulator", method="dense",
        )
        self.assertEqual(row["backend"], "aer_simulator")
        self.assertTrue(row["within_resolution"])
        self.assertLessEqual(row["absolute_error"], 2 * row["phase_resolution"])

    def test_windowing_beats_global_resolution_scale(self):
        # Windowed tau (radius 0.5) gives a much finer per-bin resolution than the
        # global spectral radius (~31) would: bin << 0.1.
        mod = _load()
        row = mod.run_one(
            n_basis=8, n_precision=6, shots=2048, reps=2, window_radius=0.5,
            use_emulator=True, device="aer_simulator", method="dense",
        )
        self.assertLess(row["phase_resolution"], 0.1)


if __name__ == "__main__":
    unittest.main()
