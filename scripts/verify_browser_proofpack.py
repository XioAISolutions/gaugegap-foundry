#!/usr/bin/env python3
"""Verify browser-exported proofpack JSON files offline.

Recomputes the SHA-256 content hash over the canonical serialization used by
the in-browser "Export proofpack" button and checks schema and claim boundary.

Usage:
    python3 scripts/verify_browser_proofpack.py pack.json [pack2.json ...]

Exit code 0 if every pack verifies, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.browser_proofpack import verify_pack  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("packs", nargs="+", type=Path, help="browser proofpack JSON files")
    args = ap.parse_args()

    results = []
    for path in args.packs:
        try:
            pack = json.loads(path.read_text(encoding="utf-8"))
            verdict = verify_pack(pack)
        except (OSError, json.JSONDecodeError) as error:
            verdict = {"verified": False, "problems": [f"unreadable pack: {error}"]}
        results.append({"pack": str(path), **verdict})

    print(json.dumps({"results": results, "all_verified": all(r["verified"] for r in results)}, indent=2))
    return 0 if all(r["verified"] for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
