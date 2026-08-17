#!/usr/bin/env python3
"""Certified coverage screening of a candidate operator against Riemann zeros.

Emits, for each requested truncation, exact rational bounds on the fraction of
the first ``k`` zero enclosures matched within a tolerance, plus the certified
spectral mismatch and a verdict against a supplied comparison threshold.

The threshold is an input. A run that lands below it emits a negative-result
certificate for that finite truncation -- not a statement about the zeta zeros.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from gaugegap.curverank_coverage import (
    CLAIM_BOUNDARY,
    FAMILIES,
    CurveRankCoverageError,
    canonical_json,
    emit_coverage_coq,
    screen_family,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", choices=FAMILIES, default="xp")
    parser.add_argument(
        "--n-basis",
        type=int,
        nargs="+",
        default=[16, 24, 32],
        help="truncation sizes to screen (one certificate each)",
    )
    parser.add_argument("--k-zeros", type=int, default=12)
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.5,
        help="a zero counts as matched when an eigenvalue enclosure lies within this distance",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.6725,
        help="comparison threshold for the matched fraction (an input, not a result)",
    )
    parser.add_argument(
        "--zeros-method",
        choices=("auto", "arb", "zetazero"),
        default="auto",
        help="source of the certified zero enclosures",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--label",
        default="curverank-0002",
        help="identifier recorded in the bundle and used for the output filename",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    threshold = Fraction(args.threshold).limit_denominator(10**9)

    screens = []
    for n_basis in args.n_basis:
        try:
            screens.append(
                screen_family(
                    args.family,
                    n_basis,
                    args.k_zeros,
                    tolerance=args.tolerance,
                    threshold=threshold,
                    zeros_method=args.zeros_method,
                )
            )
        except CurveRankCoverageError as exc:
            raise SystemExit(f"curverank-coverage: screening request rejected: {exc}")

    bundle: dict[str, object] = {
        "schema": "gaugegap.curverank_coverage_bundle.v1",
        "label": args.label,
        "family": args.family,
        "k_zeros": args.k_zeros,
        "tolerance": args.tolerance,
        "threshold": {
            "numerator": threshold.numerator,
            "denominator": threshold.denominator,
            "float": float(threshold),
        },
        "screens": screens,
        "verdicts": {str(screen["parameters"]["n_basis"]): screen["verdict"] for screen in screens},
        "claim_boundary": CLAIM_BOUNDARY,
    }
    canonical = json.dumps(bundle, sort_keys=True, separators=(",", ":"))
    bundle["bundle_digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    path = args.output_dir / f"{args.label}-coverage.json"
    path.write_text(canonical_json(bundle), encoding="utf-8")

    # Coq derives a module name from the filename, so it must be a valid
    # identifier: no hyphens.
    coq_path = args.output_dir / f"{args.label.replace('-', '_')}_coverage.coq"
    coq_path.write_text(emit_coverage_coq(screens), encoding="utf-8")

    print(f"{args.label}: certified coverage screen ({args.family})")
    print(f"k_zeros: {args.k_zeros}  tolerance: {args.tolerance}  threshold: {float(threshold)}")
    for screen in screens:
        coverage = screen["coverage"]
        mismatch = screen["certified_mismatch"]
        print(
            f"  n={screen['parameters']['n_basis']:>4}  "
            f"coverage in [{coverage['coverage_lower_float']:.4f}, {coverage['coverage_upper_float']:.4f}]  "
            f"(covered {coverage['certainly_covered']}, uncovered {coverage['certainly_uncovered']}, "
            f"undetermined {coverage['undetermined']})  "
            f"M_n in [{mismatch['lower']:.4f}, {mismatch['upper']:.4f}]  "
            f"{screen['verdict']}"
        )
        print(f"        certificate_digest: {screen['certificate_digest']}")
    print(f"bundle_digest: {bundle['bundle_digest']}")
    print(f"bundle: {path}")
    print(f"coq certificate: {coq_path}")
    print(f"claim boundary: {CLAIM_BOUNDARY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
