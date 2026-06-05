#!/usr/bin/env python3
"""Self-contained regenerator for the certified spectral-screening table.

This is the single entry point an external reviewer can run to reproduce every
certified number in the preprint and the independent-review packet, *without*
trusting any pre-recorded result file. For each candidate family / truncation it

  1. builds the interval matrix,
  2. computes certified eigenvalue enclosures (residual / Weyl bound),
  3. computes the certified spectral mismatch against the first k Riemann zeros,
  4. AND reports the diagnostics the certificate's validity depends on:
       - the maximum eigenvalue-enclosure width (residual radius),
       - the minimum gap between consecutive enclosures, and
       - whether the enclosures are pairwise disjoint.

The disjointness diagnostic matters: the residual bound only certifies that each
enclosure contains *some* eigenvalue. The clean one-to-one correspondence between
the n sorted enclosures and the n sorted true eigenvalues is guaranteed by a
counting argument *only when the enclosures are pairwise disjoint*. This script
surfaces that condition explicitly instead of assuming it.

CLAIM BOUNDARY:
Everything here is a certified *finite-truncation* bound. Nothing in this script
addresses the truncation -> infinity limit, the Riemann Hypothesis, or the
Hilbert-Polya conjecture. See docs/independent-review-packet.md.

Usage:
    python3 scripts/certify_screening.py                 # default panel
    python3 scripts/certify_screening.py --json out.json  # also write JSON
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import mpmath as mp  # noqa: E402

from gaugegap.curverank_certified import (  # noqa: E402
    certified_dirac_rindler_spectrum,
    certified_quantum_graph_spectrum,
    certified_xp_spectrum,
)
from gaugegap.curverank_spectral import (  # noqa: E402
    certified_spectral_mismatch,
    riemann_zero_intervals,
)
from gaugegap.rigorous.interval_arithmetic import Interval  # noqa: E402

# Default review panel: (family, truncation, kwargs).
DEFAULT_PANEL = [
    ("xp", 10, {}),
    ("xp", 15, {}),
    ("xp", 20, {}),
    ("dirac_rindler", 8, {"acceleration": 1.0, "mass": 0.0}),
    ("quantum_graph", 8, {}),
]


def _spectrum(family: str, n: int, kwargs: dict) -> List[Interval]:
    if family == "xp":
        return certified_xp_spectrum(n, kwargs.get("L", 1.0))
    if family == "dirac_rindler":
        return certified_dirac_rindler_spectrum(
            n, kwargs.get("acceleration", 1.0), kwargs.get("mass", 0.0)
        )
    if family == "quantum_graph":
        import numpy as np

        edges = kwargs.get("edges", [(0, 1), (0, 2), (0, 3)])
        lengths = kwargs.get(
            "lengths", [1.0, float(np.sqrt(2)), float(np.sqrt(3))]
        )
        return certified_quantum_graph_spectrum(edges, lengths, n)
    raise ValueError(f"unknown family {family!r}")


def _disjointness(enclosures: List[Interval]) -> tuple:
    """Return (min_gap, all_disjoint) for enclosures sorted by midpoint.

    min_gap is the smallest (lower_{i+1} - upper_i) across consecutive
    enclosures; if it is > 0 the enclosures are pairwise disjoint and the
    counting argument gives a one-to-one correspondence with the true spectrum.
    """
    ordered = sorted(enclosures, key=lambda iv: iv.midpoint())
    min_gap = mp.inf
    for i in range(len(ordered) - 1):
        gap = ordered[i + 1].lower - ordered[i].upper
        min_gap = min(min_gap, gap)
    return min_gap, bool(min_gap > 0)


def certify_row(family: str, n: int, k_zeros: int, kwargs: dict) -> dict:
    eigs = _spectrum(family, n, kwargs)
    mismatch = certified_spectral_mismatch(eigs, riemann_zero_intervals(k_zeros))
    max_width = max((iv.width() for iv in eigs), default=mp.mpf(0))
    min_gap, disjoint = _disjointness(eigs)
    return {
        "family": family,
        "truncation": n,
        "dim": len(eigs),
        "k_zeros": k_zeros,
        "mismatch_lower": mp.nstr(mismatch.lower, 16),
        "mismatch_upper": mp.nstr(mismatch.upper, 16),
        "mismatch_width": mp.nstr(mismatch.width(), 4),
        "max_eig_enclosure_width": mp.nstr(max_width, 4),
        "min_enclosure_gap": mp.nstr(min_gap, 4),
        "enclosures_disjoint": disjoint,
    }


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
        ).strip()
    except Exception:
        return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--k-zeros", type=int, default=20)
    ap.add_argument("--json", type=str, default=None, help="optional JSON output path")
    args = ap.parse_args()

    print(f"# Certified spectral-screening regeneration")
    print(f"# commit: {git_commit()}")
    print(f"# mpmath working precision: {mp.mp.dps} decimal digits")
    print(f"# k_zeros: {args.k_zeros}\n")

    header = (
        f"{'family':<16} {'n':>4} {'dim':>4} "
        f"{'certified M_n >=':>18} {'M width':>10} "
        f"{'max eig width':>14} {'min gap':>12} {'disjoint':>9}"
    )
    print(header)
    print("-" * len(header))

    rows = []
    all_disjoint = True
    for family, n, kwargs in DEFAULT_PANEL:
        row = certify_row(family, n, args.k_zeros, kwargs)
        rows.append(row)
        all_disjoint = all_disjoint and row["enclosures_disjoint"]
        print(
            f"{row['family']:<16} {row['truncation']:>4} {row['dim']:>4} "
            f"{float(row['mismatch_lower']):>18.6f} {row['mismatch_width']:>10} "
            f"{row['max_eig_enclosure_width']:>14} {row['min_enclosure_gap']:>12} "
            f"{str(row['enclosures_disjoint']):>9}"
        )

    print()
    if all_disjoint:
        print("All eigenvalue enclosures are pairwise disjoint: the counting")
        print("argument gives a one-to-one correspondence with the true spectrum,")
        print("so the per-rank order-statistic mismatch is a valid certificate.")
    else:
        print("WARNING: some enclosures overlap. The order-statistic mismatch is")
        print("still a valid lower bound, but the one-to-one spectral correspondence")
        print("is not guaranteed by disjointness alone for those rows.")

    if args.json:
        out = {
            "commit": git_commit(),
            "mpmath_dps": mp.mp.dps,
            "k_zeros": args.k_zeros,
            "all_disjoint": all_disjoint,
            "rows": rows,
        }
        Path(args.json).write_text(json.dumps(out, indent=2))
        print(f"\nWrote {args.json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
