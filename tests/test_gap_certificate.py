from __future__ import annotations

import unittest

from gaugegap.models.z2_plaquette import CLAIM_BOUNDARY
from gaugegap.verification.gap_certificate import make_gap_certificate


class GapCertificateTests(unittest.TestCase):
    def test_certificate_contains_claim_boundary(self) -> None:
        certificate = make_gap_certificate(
            hypothesis_id="gaugegap-0002",
            model="z2_open_plaquette_chain",
            n_qubits=4,
            parameters={"claim_boundary": CLAIM_BOUNDARY},
            backend={"provider": "local"},
            ground_energy=-1.0,
            first_excited_energy=-0.5,
            gap=0.5,
        )
        self.assertEqual(certificate["claim_boundary"], CLAIM_BOUNDARY)
        self.assertIn("no continuum Yang-Mills", certificate["claim_boundary"])

    def test_certificate_rejects_negative_gap(self) -> None:
        with self.assertRaises(ValueError):
            make_gap_certificate(
                hypothesis_id="gaugegap-0002",
                model="z2_open_plaquette_chain",
                n_qubits=4,
                parameters={},
                backend={"provider": "local"},
                ground_energy=-1.0,
                first_excited_energy=-0.5,
                gap=-0.1,
            )


if __name__ == "__main__":
    unittest.main()
