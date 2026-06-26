from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.claim_boundary_audit import scan


class ClaimBoundaryAuditTests(unittest.TestCase):
    def test_detects_unbounded_overclaim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("We solved the Yang-Mills problem.\n", encoding="utf-8")
            findings = scan(root, ("README.md",))
            self.assertTrue(any(item.severity == "high" for item in findings))

    def test_bounded_finite_system_context_is_low_severity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text(
                "Claim boundary: finite-system benchmark only.\n"
                "This is not a Yang-Mills proof.\n",
                encoding="utf-8",
            )
            findings = scan(root, ("README.md",))
            self.assertTrue(findings)
            self.assertTrue(all(item.severity == "low" for item in findings))

    def test_markdown_boundary_label_bounds_certainty_language(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text(
                "> 🧭 **Boundary:** exact cancellation is proved only for a declared finite field inventory. "
                "It does not establish a continuum theorem.\n",
                encoding="utf-8",
            )
            findings = scan(root, ("README.md",))
            certainty = [item for item in findings if item.kind == "certainty_overclaim"]
            self.assertTrue(certainty)
            self.assertTrue(all(item.severity == "low" for item in certainty))

    def test_unbounded_certainty_language_remains_high(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text(
                "This theorem is proved and definitive.\n",
                encoding="utf-8",
            )
            findings = scan(root, ("README.md",))
            certainty = [item for item in findings if item.kind == "certainty_overclaim"]
            self.assertTrue(certainty)
            self.assertTrue(all(item.severity == "high" for item in certainty))


if __name__ == "__main__":
    unittest.main()
