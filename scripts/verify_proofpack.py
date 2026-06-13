#!/usr/bin/env python3
"""Verify the reproducibility proofpack is deterministic from a fresh build.

Generates the proofpack twice into separate temp directories under a fixed
SOURCE_DATE_EPOCH and asserts the two ``reproducible_digest`` values match (and
that every scientific output file is byte-identical). This is the executable
check behind issue #12 A4: "make proofpack deterministic from a fresh clone."

Usage:
    python3 scripts/verify_proofpack.py            # uses a fixed default epoch
    python3 scripts/verify_proofpack.py --epoch N  # pin a specific epoch

Exit code 0 if reproducible, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "scripts" / "generate_reproducibility_proofpack.py"
DEFAULT_EPOCH = 1700000000  # fixed reference instant for reproducible builds


def _build(output_dir: Path, epoch: int) -> dict:
    env = dict(os.environ, SOURCE_DATE_EPOCH=str(epoch))
    proc = subprocess.run(
        [sys.executable, str(GENERATOR), "--output-dir", str(output_dir)],
        cwd=ROOT, env=env, text=True, capture_output=True, check=False,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout + proc.stderr)
        raise SystemExit(f"proofpack generation failed (rc={proc.returncode})")
    return json.loads((output_dir / "proofpack_manifest.json").read_text())


def _science_hashes(manifest: dict) -> dict[str, str]:
    return {
        f["path"]: f["sha256"]
        for f in manifest["files"]
        if not str(f["path"]).startswith("commands/")
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--epoch", type=int, default=DEFAULT_EPOCH)
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        a = _build(Path(tmp) / "a", args.epoch)
        b = _build(Path(tmp) / "b", args.epoch)

    digest_ok = a["reproducible_digest"] == b["reproducible_digest"]
    ha, hb = _science_hashes(a), _science_hashes(b)
    differing = sorted(k for k in set(ha) | set(hb) if ha.get(k) != hb.get(k))

    result = {
        "reproducible": digest_ok and not differing,
        "reproducible_digest": a["reproducible_digest"],
        "epoch": args.epoch,
        "science_files": len(ha),
        "differing_files": differing,
    }
    print(json.dumps(result, indent=2))
    return 0 if result["reproducible"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
