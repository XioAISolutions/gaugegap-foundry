"""Regression test for proofpack determinism (issue #12, A4).

Builds the reproducibility proofpack twice into separate directories under a
fixed SOURCE_DATE_EPOCH and asserts the scientific payload is byte-for-byte
identical (same reproducible_digest, same per-file hashes). This guards the
"make proofpack deterministic from a fresh clone" guarantee.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "generate_reproducibility_proofpack.py"
EPOCH = "1700000000"


def _build(output_dir: Path) -> dict:
    env = dict(os.environ, SOURCE_DATE_EPOCH=EPOCH)
    proc = subprocess.run(
        [sys.executable, str(GENERATOR), "--output-dir", str(output_dir)],
        cwd=ROOT, env=env, text=True, capture_output=True, check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return json.loads((output_dir / "proofpack_manifest.json").read_text())


def _science(manifest: dict) -> dict[str, str]:
    return {
        f["path"]: f["sha256"]
        for f in manifest["files"]
        if not str(f["path"]).startswith("commands/")
    }


def test_proofpack_is_reproducible(tmp_path):
    a = _build(tmp_path / "a")
    b = _build(tmp_path / "b")

    # The content digest of the scientific payload is stable.
    assert a["reproducible_digest"] == b["reproducible_digest"]
    assert a["reproducible_digest"]  # non-empty

    # Every scientific output file is byte-identical between the two builds.
    ha, hb = _science(a), _science(b)
    assert ha == hb
    assert len(ha) >= 3  # at least the default benchmark outputs


def test_proofpack_verify_script_passes(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "verify_proofpack.py")],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert json.loads(proc.stdout)["reproducible"] is True
