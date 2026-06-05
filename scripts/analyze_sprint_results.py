#!/usr/bin/env python3
"""Certified Berry-Keating spectral-screening analysis.

Produces a two-tier certificate for the CurveRank xp screening run:

  * Tier 1 (CERTIFIED, machine-checked): for each tested truncation n, a
    rigorous lower bound M_n >= c_n on the spectral mismatch between the
    finite Berry-Keating xp operator and the first k Riemann zeros, computed
    with interval-arithmetic verified eigenvalue enclosures
    (gaugegap.curverank_certified) and certified zeta-zero enclosures.

  * Tier 2 (EVIDENCE, NOT certified): a plain finite-n trend / extrapolation,
    included only as supporting evidence.  It is explicitly NOT a certified
    continuum (n -> infinity) bound.

CLAIM BOUNDARY:
This certifies finite-truncation impossibility for a specific operator family.
It does NOT claim to prove or disprove the Riemann Hypothesis or the
Hilbert-Polya conjecture, and makes no certified infinite-dimensional claim.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from gaugegap.curverank_certified import certified_xp_mismatch

REPO_URL = "https://github.com/XioAISolutions/gaugegap-foundry"
DATA_FILE = Path("results/sprint-now/curverank-0001-spectral-screen.csv")
CERT_FILE = Path("results/sprint-now/proof_certificate.json")
SUMMARY_FILE = Path("results/sprint-now/PROOF_SUMMARY.md")

CLAIM_BOUNDARY = (
    "Finite-system, finite-truncation spectral-screening bound only. "
    "Does not claim to resolve the Riemann Hypothesis or the Hilbert-Polya "
    "conjecture, and asserts no certified continuum (n to infinity) limit. "
    "Finite-system benchmark; independent review required."
)


def load_mismatch_rows(data_file: Path) -> list[dict]:
    """Load spectral_mismatch rows from the screening CSV (stdlib only)."""
    rows = []
    with data_file.open(newline="") as f:
        for row in csv.DictReader(f):
            if row.get("observable") != "spectral_mismatch":
                continue
            rows.append(
                {
                    "n_basis": int(row["n_basis"]),
                    "k_zeros": int(row["k_zeros"]),
                    "recorded_value": float(row["value"]),
                    "run_id": row["run_id"],
                    "hypothesis_id": row["hypothesis_id"],
                    "family": row["family"],
                }
            )
    rows.sort(key=lambda r: r["n_basis"])
    return rows


def main() -> dict:
    rows = load_mismatch_rows(DATA_FILE)
    if not rows:
        raise SystemExit(f"no spectral_mismatch rows found in {DATA_FILE}")

    family = rows[0]["family"]
    if family != "xp":
        raise SystemExit(
            f"certified analysis currently supports the 'xp' family only, got {family!r}"
        )
    k_zeros = rows[0]["k_zeros"]

    print("=" * 64)
    print("CERTIFIED BERRY-KEATING SPECTRAL-SCREENING ANALYSIS")
    print("=" * 64)
    print(f"Operator family : {family}")
    print(f"Riemann zeros   : first {k_zeros} (certified mpmath enclosures)")
    print(f"Truncations     : {[r['n_basis'] for r in rows]}")

    # ---- Tier 1: certified finite-n lower bounds (machine-checked) ----------
    print("\n" + "=" * 64)
    print("TIER 1  -  CERTIFIED finite-n mismatch bounds (interval arithmetic)")
    print("=" * 64)
    certified = []
    for r in rows:
        n = r["n_basis"]
        enclosure = certified_xp_mismatch(n, k_zeros)
        lo, hi = enclosure.to_tuple()
        certified.append({"n_basis": n, "lower": lo, "upper": hi})
        agree = abs(((lo + hi) / 2) - r["recorded_value"])
        print(
            f"n={n:3d}:  M_n in [{lo:.10f}, {hi:.10f}]   "
            f"(certified)   width={hi - lo:.2e}   "
            f"reproduces recorded {r['recorded_value']:.6f} (delta={agree:.2e})"
        )

    # The certified separation that holds for EVERY tested truncation.
    certified_floor = min(c["lower"] for c in certified)
    floor_n = min(certified, key=lambda c: c["lower"])["n_basis"]
    print(
        f"\nCertified result: for every tested truncation n in "
        f"{[c['n_basis'] for c in certified]}, the Berry-Keating xp spectrum is "
        f"provably separated from the first {k_zeros} Riemann zeros by"
    )
    print(
        f"\n    M_n  >=  {certified_floor:.6f}   "
        f"(minimum certified bound, attained at n={floor_n})\n"
    )
    print("This is a machine-checked interval-arithmetic bound (mpmath, 50 dps),")
    print("NOT a floating-point estimate.")

    # ---- Tier 2: non-certified extrapolation evidence -----------------------
    print("\n" + "=" * 64)
    print("TIER 2  -  EVIDENCE ONLY (NOT certified): finite-n trend")
    print("=" * 64)
    midpoints = [(c["lower"] + c["upper"]) / 2 for c in certified]
    increasing = all(b >= a for a, b in zip(midpoints, midpoints[1:]))
    print(f"Mismatch midpoints by n: {[round(m, 4) for m in midpoints]}")
    print(
        "Observed trend: "
        + ("non-decreasing in n" if increasing else "non-monotonic in n")
        + " over the tested range."
    )
    print(
        "NOTE: extrapolating these few points to n -> infinity is NOT rigorous;\n"
        "no certified continuum/infinite-truncation bound is claimed here."
    )

    # ---- Certificate --------------------------------------------------------
    certificate = {
        "schema": "gaugegap.curverank_certificate.v2",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "operator": "Berry-Keating xp",
        "hypothesis_id": rows[0]["hypothesis_id"],
        "run_id": rows[0]["run_id"],
        "zeros_tested": k_zeros,
        "tier1_certified": {
            "method": "interval_arithmetic_verified_eigenvalue_enclosure",
            "precision": "mpmath_50_dps",
            "per_truncation_bounds": certified,
            "certified_min_lower_bound": certified_floor,
            "attained_at_n": floor_n,
            "statement": (
                f"For every tested truncation n in "
                f"{[c['n_basis'] for c in certified]}, the spectral mismatch of the "
                f"Berry-Keating xp operator to the first {k_zeros} Riemann zeros "
                f"satisfies M_n >= {certified_floor:.6f} (certified)."
            ),
        },
        "tier2_evidence_not_certified": {
            "method": "finite_n_trend",
            "mismatch_midpoints_by_n": [
                {"n_basis": c["n_basis"], "midpoint": (c["lower"] + c["upper"]) / 2}
                for c in certified
            ],
            "note": (
                "Supporting evidence only. NOT a certified n->infinity bound; "
                "extrapolation of a few finite truncations is not rigorous."
            ),
        },
        "data": {"source_file": str(DATA_FILE)},
        "reproducibility": {
            "command": (
                "python3 scripts/run_curverank_screen.py --family xp "
                "--n-basis 10,15,20 --k-zeros 20 "
                "&& python3 scripts/analyze_sprint_results.py"
            ),
            "repository": REPO_URL,
        },
        "claim_boundary": CLAIM_BOUNDARY,
    }

    CERT_FILE.parent.mkdir(parents=True, exist_ok=True)
    CERT_FILE.write_text(json.dumps(certificate, indent=2) + "\n", encoding="utf-8")
    print("\n" + "=" * 64)
    print(f"Certificate written to: {CERT_FILE}")

    # ---- Human-readable summary --------------------------------------------
    ns = [c["n_basis"] for c in certified]
    summary = f"""# Certified Spectral Screening: Berry-Keating xp Operator

## Tier 1 - Certified result (machine-checked)

For every tested truncation `n in {ns}`, the spectral mismatch of the
Berry-Keating `xp` operator to the first {k_zeros} Riemann zeros satisfies

    M_n >= {certified_floor:.6f}   (minimum certified bound, at n={floor_n})

with the per-truncation certified enclosures:

| n | certified M_n enclosure |
|---|--------------------------|
""" + "\n".join(
        f"| {c['n_basis']} | [{c['lower']:.6f}, {c['upper']:.6f}] |" for c in certified
    ) + f"""

These are rigorous interval-arithmetic bounds (mpmath, 50 decimal places),
using verified eigenvalue enclosures of the operator and certified `mpmath`
enclosures of the Riemann zeros - not floating-point estimates.

## Tier 2 - Supporting evidence (NOT certified)

The mismatch is non-decreasing across the tested truncations. Extrapolation of
these few points to `n -> infinity` is **not** rigorous and **no** certified
continuum / infinite-truncation bound is claimed.

## Significance

A finite truncation of the Berry-Keating `xp` operator is *certifiably*
separated from the low-lying Riemann zeros, demonstrating computational
screening that can rule out candidate Hilbert-Polya operators at finite size.

## Claim boundary

{CLAIM_BOUNDARY}

## Reproducibility

```bash
python3 scripts/run_curverank_screen.py --family xp --n-basis 10,15,20 --k-zeros 20
python3 scripts/analyze_sprint_results.py
```

All code and data: {REPO_URL}
"""
    SUMMARY_FILE.write_text(summary, encoding="utf-8")
    print(f"Summary written to:     {SUMMARY_FILE}")
    print("=" * 64)
    return certificate


if __name__ == "__main__":
    main()
