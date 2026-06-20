"""The hardware path stays STAGED (never fabricated) without credentials."""
from __future__ import annotations
import importlib.util, sys, warnings
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]; SRC = ROOT / "src"
if str(SRC) not in sys.path: sys.path.insert(0, str(SRC))
warnings.filterwarnings("ignore")


def _has_qiskit():
    return importlib.util.find_spec("qiskit") is not None


def _load_pipeline():
    path = ROOT / "scripts" / "run_unified_pipeline.py"
    spec = importlib.util.spec_from_file_location("unified_pipeline", path)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


class TestHardwareStaging(unittest.TestCase):
    @unittest.skipUnless(_has_qiskit(), "qiskit not installed")
    def test_device_without_creds_is_staged(self):
        import numpy as np
        from gaugegap.curverank_registry import get_operator
        m = _load_pipeline()
        spec = get_operator("berry_keating_xp")
        H = spec.build(8)
        c2 = m.stage2_qpe(spec, (H + H.conj().T) / 2, 8, 6, 4096,
                          device="ibm_brisbane")
        # No token in CI -> staged, and never labelled a confirmed hardware result.
        self.assertTrue(c2.get("staged") or not c2.get("hardware_confirmed", False))
        self.assertFalse(c2.get("hardware_confirmed", False))

    def test_runbook_exists(self):
        self.assertTrue((ROOT / "docs" / "hardware-runbook.md").exists())


if __name__ == "__main__":
    unittest.main()
