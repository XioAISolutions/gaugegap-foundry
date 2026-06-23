"""Lock in the research-maturity burn-down: no unbounded prototype/placeholder claims.

Every flagged placeholder/simplified/not-implemented site in the scientific code must
sit near a stated boundary clause (prototype / scaffold / known limitation / roadmap),
so ``research_maturity_audit --strict`` exits 0 (high_unbounded == 0). This is a CI gate.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestResearchMaturityAudit(unittest.TestCase):
    def test_strict_audit_passes(self):
        with tempfile.TemporaryDirectory() as d:
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "research_maturity_audit.py"),
                 "--strict", "--output-dir", d],
                capture_output=True, text=True)
            report = json.loads((Path(d) / "research_maturity_audit.json").read_text())
            high_unbounded = [i for i in report
                              if i["severity"] == "high" and not i["bounded"]]
            self.assertEqual(high_unbounded, [], f"unbounded: {high_unbounded}")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
