from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from gaugegap.models.z2_plaquette import hamiltonian_dense
from gaugegap.quantum.qiskit_validation import (
    QISKIT_CLAIM_BOUNDARY,
    QiskitValidationConfig,
    build_candidate_circuit,
    detect_qiskit_capabilities,
    validate_qiskit_candidate,
)
from gaugegap.quantum.ibm_runtime_adapter import RuntimeSubmissionConfig, build_runtime_submission_plan


class QiskitValidationOptionalTests(unittest.TestCase):
    def test_capability_probe_never_checks_credentials(self) -> None:
        capabilities = detect_qiskit_capabilities()
        self.assertIn("qiskit_available", capabilities)
        self.assertFalse(capabilities["credentials_checked"])

    def test_validation_degrades_gracefully_without_runtime_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = validate_qiskit_candidate(
                QiskitValidationConfig(n_plaquettes=1, shots=32, run_id="test-run"),
                output_dir=Path(tmp),
            )
        self.assertIn("status", report)
        self.assertEqual(report["claim_boundary"], QISKIT_CLAIM_BOUNDARY)
        self.assertFalse(report["hardware_submission"]["submitted"])

    def test_runtime_plan_dry_run_does_not_submit(self) -> None:
        plan = build_runtime_submission_plan(
            RuntimeSubmissionConfig(n_plaquettes=1, shots=32, dry_run=True, run_id="test-run")
        )
        self.assertTrue(plan["dry_run"])
        self.assertFalse(plan["job"]["submitted"])
        self.assertIn("no proof claim", " ".join(plan["warnings"]))

    def test_submit_requires_finite_system_confirmation(self) -> None:
        with self.assertRaises(ValueError):
            build_runtime_submission_plan(RuntimeSubmissionConfig(dry_run=False, submit_runtime=True))

    @unittest.skipUnless(detect_qiskit_capabilities()["qiskit_available"], "Qiskit optional dependency is not installed")
    def test_sparse_pauli_matches_direct_dense_when_qiskit_installed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            report = validate_qiskit_candidate(
                QiskitValidationConfig(n_plaquettes=1, shots=32, run_id="test-run"),
                output_dir=Path(tmp),
            )
            self.assertEqual(report["sparse_pauli_operator"]["status"], "pass")
            self.assertTrue(np.allclose(report["sparse_pauli_operator"]["matrix_delta"], 0.0))
            if report["qpy_manifest"].get("written"):
                self.assertTrue((Path(tmp) / "candidate_circuit.qpy").exists())

    @unittest.skipUnless(detect_qiskit_capabilities()["qiskit_available"], "Qiskit optional dependency is not installed")
    def test_candidate_circuit_has_expected_width(self) -> None:
        circuit = build_candidate_circuit(QiskitValidationConfig(n_plaquettes=1, shots=32))
        self.assertEqual(circuit.num_qubits, int(np.log2(hamiltonian_dense(1, 1.0, 0.2).shape[0])))
        self.assertIn("claim_boundary", circuit.metadata)


if __name__ == "__main__":
    unittest.main()
