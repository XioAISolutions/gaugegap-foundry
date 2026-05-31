from __future__ import annotations

import unittest

from gaugegap.validation.candidate_validation import ValidationConfig, validate_z2_candidate


class CandidateValidationTests(unittest.TestCase):
    def test_validation_returns_readiness_report(self) -> None:
        report = validate_z2_candidate(
            ValidationConfig(
                n_plaquettes=1,
                plaquette_coupling=1.0,
                transverse_field=0.2,
                shots=128,
                run_id="test-run",
                enable_qiskit_probe=False,
            )
        )
        self.assertEqual(report["hypothesis_id"], "gaugegap-0004")
        self.assertIn("hardware_readiness", report)
        self.assertIn("workflow_mapping", report)
        self.assertIn("no continuum Yang-Mills mass-gap claim", report["claim_boundary"])
        self.assertEqual(report["pauli_replica"]["status"], "pass")
        self.assertIn("qpy_export_available", report["qiskit_probe"])
        self.assertIn("aer_available", report["qiskit_probe"])
        self.assertIn("ibm_runtime_available", report["qiskit_probe"])
        self.assertFalse(report["qiskit_probe"]["credentials_checked"])

    def test_invalid_noise_strength_rejected(self) -> None:
        with self.assertRaises(ValueError):
            validate_z2_candidate(ValidationConfig(noise_strength=2.0))


if __name__ == "__main__":
    unittest.main()
