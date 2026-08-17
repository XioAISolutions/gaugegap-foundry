#!/usr/bin/env python3
"""Verify a Hadamard witness with exact integer arithmetic and emit a proofpack.

Two lanes share one verifier:

* ``--order N``      build the witness from this repository's constructor set;
* ``--witness FILE`` ingest an external witness and trust nothing about it.

Both lanes fail closed: no gate, no certificate.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from gaugegap.hadamard_forge import (
    HadamardForgeError,
    build_hadamard_proofpack,
    canonical_json,
    construct_witness,
    constructible_orders,
    gram_summary,
    orders_awaiting_witness,
    load_witness,
    verify_hadamard,
    write_witness,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--order", type=int, help="build a witness of this order")
    source.add_argument("--witness", type=Path, help="verify an external witness file")
    source.add_argument(
        "--survey",
        type=int,
        metavar="LIMIT",
        help="emit the constructor-coverage survey for admissible orders up to LIMIT",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--problem-id",
        default=None,
        help="hypothesis-facing identifier recorded in the proofpack (default: hadamard-forge-<order>)",
    )
    parser.add_argument(
        "--expected-order",
        type=int,
        default=None,
        help="fail closed unless the ingested witness has this order",
    )
    parser.add_argument(
        "--expected-rows-sha256",
        default=None,
        help="fail closed unless the packed rows hash to this digest",
    )
    parser.add_argument(
        "--release-label",
        choices=("REPRODUCED", "REDISCOVERED", "DISCOVERED"),
        default="REPRODUCED",
    )
    parser.add_argument(
        "--skip-column-check",
        action="store_true",
        help="skip the redundant H.T @ H recomputation (row orthogonality already implies it)",
    )
    return parser.parse_args()


def run_survey(limit: int, output_dir: Path) -> int:
    """Record which admissible orders this constructor set covers."""

    covered = constructible_orders(limit)
    awaiting = orders_awaiting_witness(limit)
    payload = {
        "schema": "gaugegap.hadamard_order_survey.v1",
        "limit": limit,
        "constructors": [
            "sylvester(2^k)",
            "paley_type_i(prime q = 3 mod 4)",
            "paley_type_ii(prime q = 1 mod 4)",
            "kronecker(constructible, constructible)",
        ],
        "constructible_orders": list(covered),
        "orders_awaiting_witness": list(awaiting),
        "claim_boundary": (
            "This survey describes the constructor set implemented in this repository. "
            "An order listed as awaiting a witness is one Hadamard Forge cannot build "
            "itself; it is not a claim that the order is open in the literature."
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"hadamard-order-survey-{limit:04d}.json"
    path.write_text(canonical_json(payload), encoding="utf-8")
    print(f"hadamard-forge survey: limit {limit}")
    print(f"constructible orders: {len(covered)}")
    print(f"orders awaiting an external witness: {list(awaiting)}")
    print(f"survey: {path}")
    return 0


def main() -> int:
    args = parse_args()

    if args.survey is not None:
        return run_survey(args.survey, args.output_dir)

    try:
        if args.order is not None:
            witness = construct_witness(args.order)
        else:
            witness = load_witness(args.witness)
    except HadamardForgeError as exc:
        raise SystemExit(f"hadamard-forge: witness ingestion failed closed: {exc}")

    expected_order = args.expected_order if args.expected_order is not None else args.order
    verification = verify_hadamard(
        witness,
        expected_order=expected_order,
        expected_rows_digest=args.expected_rows_sha256,
        check_columns=not args.skip_column_check,
    )
    if not verification.passed:
        failed = ", ".join(verification.failed_gates())
        raise SystemExit(f"hadamard-forge: verification failed closed: {failed}")

    problem_id = args.problem_id or f"hadamard-forge-{witness.order:04d}"
    proofpack = build_hadamard_proofpack(
        witness,
        verification,
        release_label=args.release_label,
        problem_id=problem_id,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"hadamard-{witness.order:04d}"
    witness_path = write_witness(witness, args.output_dir / f"{stem}.witness.json")
    proofpack_path = args.output_dir / f"{stem}.proofpack.json"
    proofpack_path.write_text(canonical_json(proofpack), encoding="utf-8")

    print(f"{problem_id}: PASS")
    print(f"order: {witness.order}")
    print(f"provenance: {witness.provenance}")
    print(f"release_label: {args.release_label}")
    print(f"gram: H @ H.T == {witness.order} * I (max |off-diagonal| = 0)")
    print(f"gram_block[:4]: {gram_summary(witness, sample=4)}")
    print(f"rows_sha256: {witness.rows_digest()}")
    print(f"witness_digest: {witness.digest()}")
    print(f"proofpack_digest: {proofpack['proofpack_digest']}")
    print(f"witness: {witness_path}")
    print(f"proofpack: {proofpack_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
