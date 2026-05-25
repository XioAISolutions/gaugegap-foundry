from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    from gaugegap.ibm_runtime_runner import _check_runtime
    _check_runtime()
    IBM_AVAILABLE = True
except ImportError:
    IBM_AVAILABLE = False


@unittest.skipUnless(IBM_AVAILABLE, "qiskit-ibm-runtime not installed")
class TestIBMRuntimeImports(unittest.TestCase):
    def test_sampler_v2_importable(self):
        from qiskit_ibm_runtime import SamplerV2
        self.assertTrue(callable(SamplerV2))

    def test_estimator_v2_importable(self):
        from qiskit_ibm_runtime import EstimatorV2
        self.assertTrue(callable(EstimatorV2))

    def test_service_importable(self):
        from qiskit_ibm_runtime import QiskitRuntimeService
        self.assertTrue(callable(QiskitRuntimeService))


@unittest.skipUnless(IBM_AVAILABLE, "qiskit-ibm-runtime not installed")
class TestIBMRunnerModule(unittest.TestCase):
    def test_module_functions_exist(self):
        from gaugegap.ibm_runtime_runner import (
            list_backends,
            run_sampler,
            run_estimator,
            backend_metadata,
        )
        self.assertTrue(callable(list_backends))
        self.assertTrue(callable(run_sampler))
        self.assertTrue(callable(run_estimator))
        self.assertTrue(callable(backend_metadata))


if __name__ == "__main__":
    unittest.main()
