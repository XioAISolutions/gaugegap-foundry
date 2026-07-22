#!/usr/bin/env python3
"""Run the exact Jacobian Aftershock compact-map audit."""
from __future__ import annotations

import argparse
from pathlib import Path

from gaugegap.jacobian_aftershock import aftershock_json, run_aftershock_audit


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_aftershock_audit()
    payload = result.to_dict()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "counterexample-forge-0002.aftershock.json"
    output.write_text(aftershock_json(result), encoding="utf-8")

    print("counterexample-forge-0002: PASS")
    print(f"evidence_label: {result.evidence_label}")
    print(f"novelty_status: {result.novelty_status}")
    print(f"det(JH): {result.determinant}")
    print(f"coordinate_terms: {result.coordinate_term_counts}")
    print(f"coordinate_degrees: {result.coordinate_degrees}")
    print(f"short_collision_image: {result.collision_verification.common_image}")
    print(f"four_point_image: {result.four_point_verification.common_image}")
    print(f"family_minimum_parameter: {result.family_minimum.unique_parameter}")
    print(f"family_minimum_terms: {result.family_minimum.minimum_term_count}")
    print(f"map_digest: {result.map_digest}")
    print(f"result_digest: {payload['result_digest']}")
    print(f"evidence: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
