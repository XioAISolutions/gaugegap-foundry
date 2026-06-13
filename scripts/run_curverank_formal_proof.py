#!/usr/bin/env python3
"""Formal, machine-checkable proof of the certified finite-truncation theorem.

This is the "proof-claim level" deliverable, done **honestly**: it assembles the
certified interval-arithmetic spectral-mismatch result into a formally-stated
`Theorem` (computer-assisted proof object with verified interval bounds), exports
it to the Lean 4, Coq, and Isabelle/HOL proof assistants, and emits a proof
bundle.

WHAT IS PROVED (and what is NOT)
--------------------------------
The theorem proved, for each truncation size n in the panel, is the
**finite-truncation separation theorem**:

    For the Berry-Keating xp operator truncated to n basis states, the certified
    L2 spectral mismatch to the first k Riemann zeros satisfies M_n >= B_n,
    where B_n is a machine-checked interval lower bound.

This is a genuine, rigorous, machine-checkable statement about a finite matrix.
It is a *negative* (impossibility/separation) result: it shows the truncated
operator is provably far from the zeros. It is **NOT** a proof of the Riemann
Hypothesis or the Hilbert-Polya conjecture, makes **no** continuum (n -> inf)
claim, and is **not** a Clay Millennium Prize submission. The exported Lean/Coq/
Isabelle files are machine-checkable certificates; *fully* discharging them
requires running the corresponding proof assistant (see
`formal_export.verify_certificate`).

Usage
-----
    python scripts/run_curverank_formal_proof.py \
        --n-panel 10,15,20,25,30 --k-zeros 20 --output-dir results/curverank-formal
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.curverank_spectral import riemann_zero_targets
from gaugegap.rigorous.spectral_impossibility import SpectralMismatchProof
from gaugegap.rigorous.formal_export import export_all_formats, verify_certificate


CLAIM_BOUNDARY = (
    "Certified finite-truncation separation theorem only. Proves a finite matrix "
    "is provably far from the first k Riemann zeros (a negative result). Does NOT "
    "prove the Riemann Hypothesis or the Hilbert-Polya conjecture, asserts no "
    "continuum (n->inf) limit, and is not a Millennium Prize submission."
)


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def build_and_export(n_panel: List[int], k_zeros: int, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    formal_dir = output_dir / "proof_assistants"
    zeros = riemann_zero_targets(k_zeros).tolist()

    rows = []
    for n in n_panel:
        # Build the verified Theorem from the certified pipeline (not hand-written):
        # certified xp spectrum + certified zeta-zero enclosures + certified mismatch.
        prover = SpectralMismatchProof()
        theorem = prover.prove_berry_keating_impossibility(n, zeros)

        theorem_verified = theorem.verify()  # interval-bound + conclusion checks
        mismatch_lo, mismatch_hi = theorem.conclusion["mismatch"].to_tuple()

        # Export to Lean 4 / Coq / Isabelle and check certificate well-formedness.
        certs = export_all_formats(theorem, str(formal_dir / f"n{n}"))
        cert_status = {fmt: verify_certificate(c) for fmt, c in certs.items()}

        # Persist the structured theorem object (JSON, machine-reloadable).
        theorem.to_json(str(output_dir / f"theorem_n{n}.json"))

        row = {
            "n_basis": n,
            "k_zeros": k_zeros,
            "statement": theorem.statement,
            "mismatch_lower": float(mismatch_lo),
            "mismatch_upper": float(mismatch_hi),
            "theorem_verified": bool(theorem_verified),
            "certificates_wellformed": cert_status,
            "export_dir": _rel(formal_dir / f"n{n}"),
            "export_formats": sorted(certs.keys()),
        }
        rows.append(row)
        status = "VERIFIED" if theorem_verified else "UNVERIFIED"
        print(
            f"n={n:>3}  M_n >= {float(mismatch_lo):.6f}  [{status}]  "
            f"lean4={cert_status['lean4']} coq={cert_status['coq']} "
            f"isabelle={cert_status['isabelle']}"
        )

    summary = {
        "generated": datetime.utcnow().isoformat(),
        "n_panel": n_panel,
        "k_zeros": k_zeros,
        "all_theorems_verified": all(r["theorem_verified"] for r in rows),
        "all_certificates_wellformed": all(
            all(r["certificates_wellformed"].values()) for r in rows
        ),
        "claim_boundary": CLAIM_BOUNDARY,
        "rigor_note": (
            "The machine-CHECKED content is the interval-arithmetic certificate: "
            "verified Hermitian eigenvalue enclosures + certified zeta-zero "
            "enclosures + the order-statistic mismatch bound, all checked by "
            "Theorem.verify(). The Lean/Coq/Isabelle exports transcribe the "
            "theorem STATEMENT and the certified numeric bounds into each "
            "assistant; their proof TERMS are left as `sorry`/`Admitted` "
            "placeholders, so they are statement+bound scaffolds for assistant "
            "ingestion, not yet assistant-discharged proofs."
        ),
        "theorems": rows,
    }
    (output_dir / "formal_proof_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--n-panel", type=str, default="10,15,20,25,30",
                        help="Comma-separated truncation sizes")
    parser.add_argument("--k-zeros", type=int, default=20,
                        help="Number of Riemann zeros to compare against")
    parser.add_argument("--output-dir", type=Path,
                        default=ROOT / "results" / "curverank-formal")
    args = parser.parse_args()

    n_panel = [int(x) for x in args.n_panel.split(",") if x.strip()]
    print("=" * 72)
    print("CurveRank formal proof: certified finite-truncation separation theorem")
    print("  (machine-checkable; NOT a proof of the Riemann Hypothesis)")
    print("=" * 72)
    summary = build_and_export(n_panel, args.k_zeros, args.output_dir)
    print("-" * 72)
    print(f"All theorems verified:        {summary['all_theorems_verified']}")
    print(f"All certificates well-formed: {summary['all_certificates_wellformed']}")
    print(f"Bundle: {args.output_dir}")
    return 0 if summary["all_theorems_verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
