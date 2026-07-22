#!/usr/bin/env python3
"""Run Counterexample Forge structured reconstruction benchmark."""
from __future__ import annotations

import argparse
from pathlib import Path

from gaugegap.counterexample_reconstruct import (
    reconstruct_jacobian_benchmark,
    reconstruction_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--minimum", type=int, default=-8)
    parser.add_argument("--maximum", type=int, default=8)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.minimum > args.maximum:
        raise SystemExit("minimum must be <= maximum")
    values = range(args.minimum, args.maximum + 1)
    result = reconstruct_jacobian_benchmark(values)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "counterexample-forge-0001.reconstruction.json"
    output.write_text(reconstruction_json(result), encoding="utf-8")

    print("counterexample-forge-0001 structured reconstruction")
    print(f"attempted: {result.attempted}")
    print(f"solutions: {len(result.solutions)}")
    print(f"release_label: {result.release_label}")
    print(f"claim_boundary: {result.claim_boundary}")
    print(f"report: {output}")

    solution = result.unique_solution
    if solution is None:
        print("status: NEGATIVE_RESULT")
        return 1

    successful_trial = next(trial for trial in result.trials if trial.verified)
    coefficients = successful_trial.coefficients
    verification = result.verifications[0]
    print("status: PASS")
    print(
        "recovered_coefficients: "
        f"a={coefficients.a}, b={coefficients.b}, c={coefficients.c}, "
        f"d={coefficients.d}, e={coefficients.e}"
    )
    print(f"det(JF): {verification.determinant}")
    print(f"common_image: {verification.common_image}")
    print(f"candidate_digest: {solution.digest()}")
    print(f"reconstruction_digest: {result.to_dict()['reconstruction_digest']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
