"""Test the reviewer-packet generator (issue #12, A7)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_reviewer_packet.py"


def test_reviewer_packet_assembles(tmp_path):
    out = tmp_path / "packet"
    env = dict(os.environ, SOURCE_DATE_EPOCH="1700000000")
    proc = subprocess.run(
        [sys.executable, str(BUILDER), "--output-dir", str(out)],
        cwd=ROOT, env=env, text=True, capture_output=True, check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    result = json.loads(proc.stdout)
    assert result["status"] == "pass"
    assert result["claim_boundary_audit"] == "pass"
    assert result["missing_docs"] == []

    # INDEX plus the curated docs and audit reports are present.
    index = (out / "INDEX.md").read_text()
    assert "Reviewer Packet" in index
    assert "Claim boundary" in index
    assert "Reviewer checklist" in index
    for fname in (
        "01-independent-review-packet.md",
        "03-eightfold-certified.md",
        "claim-boundary-audit.md",
        "research-maturity-audit.md",
    ):
        assert (out / fname).exists(), fname

    # The intermediate audit output dirs are cleaned up.
    assert not (out / "_claim-boundary-audit").exists()
