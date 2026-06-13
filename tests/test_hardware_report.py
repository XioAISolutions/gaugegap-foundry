"""Tests for the CurveRank QPE hardware-feasibility report.

Skipped unless qiskit is installed (the report transpiles real circuits).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _qiskit_available() -> bool:
    try:
        import qiskit  # noqa: F401
    except ImportError:
        return False
    return True


def _load_report_module():
    path = ROOT / "scripts" / "run_curverank_hardware_report.py"
    spec = importlib.util.spec_from_file_location("curverank_hw_report", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(_qiskit_available(), "qiskit not installed")
class TestHardwareReport(unittest.TestCase):
    def test_build_report_rows(self):
        mod = _load_report_module()
        rows = mod.build_report([2, 4], n_precision=3, reps=2)
        self.assertEqual(len(rows), 2)
        for r in rows:
            # Iterative is single-ancilla: strictly narrower than the register
            # variants, which use system + n_precision qubits.
            self.assertEqual(r["iterative_qubits"], r["n_system_qubits"] + 1)
            self.assertLess(r["iterative_qubits"], r["dense_qubits"])
            # Every family must report a positive CX count.
            self.assertGreater(r["dense_cx"], 0)
            self.assertGreater(r["trotter_cx"], 0)
            self.assertGreater(r["iterative_cx"], 0)

    def test_write_outputs_emits_all_artifacts(self):
        import tempfile

        mod = _load_report_module()
        rows = mod.build_report([2], n_precision=3, reps=2)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            mod.write_outputs(rows, out, n_precision=3)
            for name in (
                "hardware_report.json",
                "hardware_report.csv",
                "hardware_report.md",
                "hardware_cx_counts.svg",
            ):
                self.assertTrue((out / name).exists(), name)
            # SVG must be well-formed XML.
            import xml.dom.minidom

            xml.dom.minidom.parse(str(out / "hardware_cx_counts.svg"))


if __name__ == "__main__":
    unittest.main()
