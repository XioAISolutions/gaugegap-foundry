#!/usr/bin/env python3
"""Verify a Lottery Forge proofpack hash and claim-boundary schema."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from gaugegap.lottery_forge import verify_proofpack


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Verify a GaugeGap Lottery Forge proofpack.")
    parser.add_argument("proofpack", type=Path)
    args = parser.parse_args(argv)
    payload = json.loads(args.proofpack.read_text(encoding="utf-8"))
    ok = verify_proofpack(payload)
    print(json.dumps({"proofpack": str(args.proofpack), "verified": ok}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
