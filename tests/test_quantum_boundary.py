from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.quantum_boundary import (
    ibm_runtime_readiness,
    quantum_summary,
    quantum_usage_map,
    render_quantum_usage_markdown,
)


class QuantumBoundaryTests(unittest.TestCase):
    def test_summary_distinguishes_simulation_from_hardware(self) -> None:
        summary = quantum_summary()
        self.assertEqual(summary["max_active_level"], 2)
        self.assertFalse(summary["actual_hardware_runs_present"])

    def test_summary_reports_hardware_ready(self) -> None:
        summary = quantum_summary()
        self.assertEqual(summary["max_ready_level"], 3)
        self.assertGreater(summary["hardware_ready_count"], 0)

    def test_usage_map_contains_runtime_boundary(self) -> None:
        surfaces = quantum_usage_map()
        ids = {surface["id"] for surface in surfaces}
        self.assertIn("qiskit_statevector_dynamics", ids)
        self.assertIn("ibm_runtime_sampler", ids)
        self.assertIn("braket_local_simulator", ids)
        self.assertIn("braket_cloud_devices", ids)

    def test_ibm_readiness_without_probe_is_non_failing(self) -> None:
        readiness = ibm_runtime_readiness(probe=False)
        self.assertIn("dependency_present", readiness)
        self.assertEqual(readiness["status"], "not_probed")

    def test_markdown_renderer_produces_output(self) -> None:
        payload = {
            "summary": quantum_summary(),
            "surfaces": quantum_usage_map(),
            "ibm_runtime": ibm_runtime_readiness(probe=False),
        }
        rendered = render_quantum_usage_markdown(payload)
        self.assertIn("Quantum Usage Map", rendered)
        self.assertIn("braket_local_simulator", rendered)


if __name__ == "__main__":
    unittest.main()
