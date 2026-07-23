#!/usr/bin/env python3
"""Derive and verify the exact degree-2 plane-frontier certificate."""
from __future__ import annotations

import argparse
from pathlib import Path

from gaugegap.plane_frontier_degree2 import (
    canonical_json,
    derive_degree2_exact_certificate,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    certificate = derive_degree2_exact_certificate()
    payload = certificate.to_dict()
    if not certificate.verified:
        raise SystemExit("plane-frontier-0002 failed closed")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "plane-frontier-0002.degree2-exact.json"
    output.write_text(canonical_json(payload), encoding="utf-8")

    print("plane-frontier-0002: PASS")
    print("evidence_label: DERIVED_EXACT")
    print("novelty_status: UNESTABLISHED")
    print(f"support: {certificate.support}")
    print(f"total_system: {certificate.total_equations}x{certificate.total_unknowns}")
    print(f"selected_rows: {certificate.selected_rows}")
    print(f"active_columns: {certificate.active_columns}")
    print(f"exact_rank_before_contradiction: {certificate.exact_rank_before_contradiction}")
    print(f"certificate_nonzero_rows: {len(certificate.certificate_rows)}")
    print(f"rhs_pairing: {certificate.rhs_pairing}")
    print(f"certificate_digest: {payload['certificate_digest']}")
    print(f"evidence: {output}")
    print(f"claim_boundary: {certificate.claim_boundary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
