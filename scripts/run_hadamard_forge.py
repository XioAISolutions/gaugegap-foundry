#!/usr/bin/env python3
"""Verify a Hadamard witness with exact integer arithmetic and emit a proofpack.

Three lanes share one verifier:

* ``--order N``      build the witness from this repository's constructor set;
* ``--williamson N`` search the symmetric Williamson family for order ``4N``;
* ``--witness FILE`` ingest an external witness and trust nothing about it.

Every lane fails closed: no gate, no certificate. The search lane additionally
records what it examined, and reports an exhausted family as a negative result
rather than as silence.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from gaugegap.hadamard_williamson import (
    OUTCOME_FOUND,
    search_williamson_quadruple,
    williamson_search_orders,
    williamson_witness,
)
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
        "--williamson",
        type=int,
        metavar="N",
        help="search the symmetric Williamson family for a witness of order 4N (N odd)",
    )
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
        "--candidate-budget",
        type=int,
        default=None,
        help="maximum symmetric rows a Williamson search may enumerate before reporting a budget stop",
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
    uncovered = orders_awaiting_witness(limit)
    searchable = set(williamson_search_orders(limit))
    search_reachable = tuple(order for order in uncovered if order in searchable)
    awaiting = tuple(order for order in uncovered if order not in searchable)
    payload = {
        "schema": "gaugegap.hadamard_order_survey.v2",
        "limit": limit,
        "constructors": [
            "sylvester(2^k)",
            "paley_type_i(prime q = 3 mod 4)",
            "paley_type_ii(prime q = 1 mod 4)",
            "kronecker(constructible, constructible)",
        ],
        "searches": ["williamson(symmetric circulant quadruples, order 4n)"],
        "constructible_orders": list(covered),
        "search_reachable_orders": list(search_reachable),
        "orders_awaiting_witness": list(awaiting),
        "claim_boundary": (
            "This survey describes the constructor and search set implemented in this "
            "repository. A search-reachable order is one whose Williamson enumeration fits "
            "the candidate budget; the search may still return no quadruple, because the "
            "family is genuinely empty for some orders, or stop on its pair budget, which "
            "certifies nothing. Reachable is therefore an invitation to run the search, not "
            "a prediction of its outcome. An order listed as awaiting a witness is one "
            "Hadamard Forge cannot settle itself; it is not a claim that the order is open "
            "in the literature."
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"hadamard-order-survey-{limit:04d}.json"
    path.write_text(canonical_json(payload), encoding="utf-8")
    print(f"hadamard-forge survey: limit {limit}")
    print(f"constructible orders: {len(covered)}")
    print(f"search-reachable orders (Williamson): {len(search_reachable)}")
    print(f"orders awaiting an external witness: {list(awaiting)}")
    print(f"survey: {path}")
    return 0


def run_search(args: argparse.Namespace) -> tuple[object, dict[str, object]]:
    """Search the Williamson family; return the witness and the search record.

    An exhausted family is a result, not a failure: the record is written as a
    negative-result certificate and no witness is returned.
    """

    kwargs = {}
    if args.candidate_budget is not None:
        kwargs["candidate_budget"] = args.candidate_budget
    try:
        search = search_williamson_quadruple(args.williamson, **kwargs)
    except HadamardForgeError as exc:
        raise SystemExit(f"hadamard-forge: search request rejected: {exc}")
    record = search.to_dict()

    if search.outcome != OUTCOME_FOUND:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        path = args.output_dir / f"hadamard-{search.order:04d}.search.json"
        path.write_text(canonical_json(record), encoding="utf-8")
        print(f"hadamard-forge williamson search: n={search.n} order={search.order}")
        print(f"outcome: {search.outcome}")
        print(f"rows enumerated: {search.enumerated} (space {search.space_size})")
        print(f"rows surviving the density bound: {search.psd_survivors}")
        print(f"admissible row-sum partitions: {[list(p) for p in search.partitions]}")
        print(f"negative-result certificate: {path}")
        print(f"claim boundary: {search.claim_boundary}")
        return None, record

    return williamson_witness(search.quadruple), record


def main() -> int:
    args = parse_args()

    if args.survey is not None:
        return run_survey(args.survey, args.output_dir)

    search_record: dict[str, object] | None = None
    try:
        if args.order is not None:
            witness = construct_witness(args.order)
        elif args.williamson is not None:
            witness, search_record = run_search(args)
            if witness is None:
                return 0
        else:
            witness = load_witness(args.witness)
    except HadamardForgeError as exc:
        raise SystemExit(f"hadamard-forge: witness ingestion failed closed: {exc}")

    expected_order = args.expected_order if args.expected_order is not None else args.order
    if expected_order is None and args.williamson is not None:
        expected_order = 4 * args.williamson
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
        search_record=search_record,
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
    if search_record is not None:
        space = search_record["search_space"]
        print(f"search: {search_record['outcome']} over {space['family']}")
        print(
            f"        rows enumerated {space['rows_enumerated']} "
            f"(space {space['symmetric_rows_with_leading_plus_one']}), "
            f"surviving the density bound {space['rows_surviving_psd_bound']}"
        )
    print(f"witness: {witness_path}")
    print(f"proofpack: {proofpack_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
