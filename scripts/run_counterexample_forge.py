#!/usr/bin/env python3
"""Generate the Counterexample Forge v1 exact verification bundle."""
from __future__ import annotations

import argparse
from pathlib import Path

from gaugegap.counterexample_forge import (
    build_counterexample_proofpack,
    canonical_json,
    jacobian_benchmark_map,
    jacobian_benchmark_witnesses,
    verify_polynomial_counterexample,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--release-label",
        choices=("REPRODUCED", "REDISCOVERED", "DISCOVERED"),
        default="REPRODUCED",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidate = jacobian_benchmark_map()
    witnesses = jacobian_benchmark_witnesses()
    verification = verify_polynomial_counterexample(
        candidate,
        witnesses,
        expected_determinant=-2,
    )
    if not verification.passed:
        failed = ", ".join(gate.name for gate in verification.gates if not gate.passed)
        raise SystemExit(f"Counterexample verification failed closed: {failed}")

    proofpack = build_counterexample_proofpack(
        candidate,
        witnesses,
        verification,
        release_label=args.release_label,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "counterexample-forge-0001.proofpack.json"
    output.write_text(canonical_json(proofpack), encoding="utf-8")

    determinant = verification.determinant
    image = verification.common_image
    print("counterexample-forge-0001: PASS")
    print(f"release_label: {args.release_label}")
    print(f"candidate_digest: {candidate.digest()}")
    print(f"proofpack_digest: {proofpack['proofpack_digest']}")
    print(f"det(JF): {determinant}")
    print(f"common_image: {image}")
    print(f"proofpack: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
