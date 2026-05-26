from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from gaugegap.models.z2_plaquette import CLAIM_BOUNDARY

ROOT = Path(__file__).resolve().parents[1]


class Z2PlaquetteScriptTests(unittest.TestCase):
    def test_exact_script_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            stdout = _run_script("run_z2_plaquette.py", output)
            self.assertEqual(stdout["status"], "finite_system_verified")
            self.assertEqual(stdout["claim_boundary"], CLAIM_BOUNDARY)
            certificate = json.loads((output / "z2_plaquette_gap_certificate.json").read_text(encoding="utf-8"))
            self.assertEqual(certificate["claim_boundary"], CLAIM_BOUNDARY)

    def test_quantum_replica_script_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            stdout = _run_script("run_quantum_gap_replica.py", output)
            self.assertEqual(stdout["status"], "pass")
            self.assertEqual(stdout["matrix_delta"], 0.0)
            self.assertEqual(stdout["gap_delta"], 0.0)
            certificate = json.loads(
                (output / "z2_plaquette_quantum_replica_certificate.json").read_text(encoding="utf-8")
            )
            self.assertEqual(certificate["claim_boundary"], CLAIM_BOUNDARY)

    def test_vqe_script_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            stdout = _run_script("run_vqe_gap.py", output, "--samples", "8")
            self.assertIn(stdout["status"], {"pass", "warning_variational_gap_error"})
            self.assertEqual(stdout["claim_boundary"], CLAIM_BOUNDARY)
            self.assertTrue((output / "z2_plaquette_vqe_gap_certificate.json").exists())

    def test_sweep_script_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            stdout = _run_script(
                "run_z2_plaquette_sweep.py",
                output,
                "--n-plaquettes",
                "1,2",
                "--fields",
                "0.1,0.2",
                "--run-id",
                "test",
            )
            self.assertEqual(stdout["status"], "pass")
            self.assertEqual(stdout["records"], 4)
            rows = (output / "gaugegap-0002-z2-plaquette-sweep.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(rows), 4)
            first = json.loads(rows[0])
            self.assertEqual(first["claim_boundary"], CLAIM_BOUNDARY)
            self.assertEqual(first["pauli_replica"]["matrix_delta"], 0.0)


def _run_script(script_name: str, output_dir: Path, *extra: str) -> dict[str, object]:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script_name), "--output-dir", str(output_dir), *extra],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(proc.stdout)


if __name__ == "__main__":
    unittest.main()
