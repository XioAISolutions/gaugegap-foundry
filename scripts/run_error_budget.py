#!/usr/bin/env python3
"""Hardened error budget (work order A6): repeated-seed runs + confidence
intervals + separated error sources, assembled with the ErrorBudget API.

Estimates the magnitude of the smallest-|.| eigenvalue of the Berry-Keating xp
truncation from the QCELS quantum signal under modelled shot noise + dephasing,
repeated over independent child seeds to get a statistical confidence interval,
then combines it with the certified-enclosure (truncation) bound and a numerical-
precision bound into a single, source-separated error budget.

CLAIM BOUNDARY: the confidence interval is the statistical spread of the estimator
at a FIXED finite truncation; it implies nothing about the continuum/thermodynamic
limit and is not a continuum mass-gap statement. Systematic sources (truncation,
numerical precision) are separate, explicitly bounded components.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.curverank_operators import berry_keating_xp
from gaugegap.curverank_registry import get_operator
from gaugegap.curverank_signal import qcels
from gaugegap.seeding import make_rng
from gaugegap.repeated_runs import repeated_run
from gaugegap.error_budget import ErrorBudget

CLAIM_BOUNDARY = (
    "statistical CI is the estimator spread at a fixed finite truncation; no "
    "continuum/thermodynamic-limit implication; truncation and numerical bounds "
    "are separate components; not a proof of any Millennium Prize problem"
)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n-basis", type=int, default=8)
    ap.add_argument("--n-runs", type=int, default=20)
    ap.add_argument("--shots", type=int, default=1500)
    ap.add_argument("--dephasing", type=float, default=0.01)
    ap.add_argument("--parent-seed", type=int, default=1234)
    ap.add_argument("--ci-level", type=float, default=0.95)
    ap.add_argument("--output-dir", type=Path, default=ROOT / "results" / "error-budget")
    args = ap.parse_args()

    H = berry_keating_xp(args.n_basis).astype(complex)
    H = (H + H.conj().T) / 2.0
    evals = np.linalg.eigvalsh(H)
    # Target: the smallest-magnitude eigenvalue (the ~0.996 level for xp).
    target = float(min(evals, key=abs))
    target_mag = abs(target)

    # Certified enclosure for that eigenvalue -> the truncation/numerical bound.
    enclosures = get_operator("berry_keating_xp").certified(args.n_basis)
    encl = min(enclosures, key=lambda iv: abs((iv.lower + iv.upper) / 2 - target))
    lo, hi = float(encl.lower), float(encl.upper)
    enclosure_halfwidth = (hi - lo) / 2.0

    psi = np.ones(args.n_basis) / np.sqrt(args.n_basis)

    def estimator(seed: int) -> float:
        # Magnitude of the dominant-overlap eigenvalue under shot noise+dephasing.
        return abs(float(qcels(H, psi, total_time=60.0, levels=4,
                               shots=args.shots, dephasing=args.dephasing,
                               rng=make_rng(seed)).eigenvalue))

    stats = repeated_run(estimator, parent_seed=args.parent_seed,
                         n_runs=args.n_runs, level=args.ci_level)

    budget = ErrorBudget(quantity=f"|lambda_min| of xp(n={args.n_basis})")
    budget.add("sampling_shot_noise", stats.ci_halfwidth, "statistical", "stochastic")
    budget.add("certified_truncation_enclosure", enclosure_halfwidth, "truncation", "bound")
    budget.add("numerical_precision", 1e-12 * max(1.0, target_mag), "numerical", "bound")

    dominant = budget.dominant()
    payload = {
        "quantity": budget.quantity,
        "claim_boundary": CLAIM_BOUNDARY,
        "target_magnitude_classical": target_mag,
        "repeated_runs": stats.to_dict(),
        "error_budget": budget.as_dict(),
        "by_category": budget.by_category(),
        "total": budget.total(),
        "dominant_source": dominant.name if dominant else None,
    }

    print("=" * 72)
    print(f"Error budget — {budget.quantity}")
    print("=" * 72)
    print(f"  repeated runs: n={stats.n_runs}, mean={stats.mean:.6f}, "
          f"{int(args.ci_level*100)}% CI=[{stats.ci_low:.6f}, {stats.ci_high:.6f}] "
          f"(half {stats.ci_halfwidth:.2e})")
    print(f"  classical target |lambda|={target_mag:.6f}")
    print(budget.report())
    print(f"  conservative total: {budget.total():.3e} | dominant: "
          f"{dominant.name if dominant else 'n/a'}")

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / "error-budget.json").write_text(json.dumps(payload, indent=2, sort_keys=True))
    _write_markdown(out / "error-budget.md", payload)
    print(f"\nReport: {out / 'error-budget.json'} + {out / 'error-budget.md'}")
    return 0


def _write_markdown(path: Path, p: dict) -> None:
    rr = p["repeated_runs"]
    lines = [
        "# Error budget (repeated-seed runs + confidence intervals)",
        "",
        f"Quantity: `{p['quantity']}`. **Claim boundary:** the confidence interval "
        "is the statistical spread of the estimator at a fixed finite truncation; it "
        "implies nothing about the continuum / thermodynamic limit and is a "
        "certified negative-result-style finite statement, not a proof of any "
        "Millennium Prize problem.",
        "",
        f"- Classical target |λ| = **{p['target_magnitude_classical']:.6f}**",
        f"- Repeated runs: n = **{rr['n_runs']}**, mean = **{rr['mean']:.6f}**, "
        f"{int(rr['ci_level']*100)}% CI = **[{rr['ci'][0]:.6f}, {rr['ci'][1]:.6f}]** "
        f"(half-width {rr['ci_halfwidth']:.2e})",
        "",
        "## Source-separated budget",
        "",
        "| Source | Category | Kind | Magnitude |",
        "|---|---|---|---|",
    ]
    for c in p["error_budget"]["components"]:
        lines.append(f"| {c['name']} | {c['category']} | {c['kind']} | {c['value']:.3e} |")
    lines += [
        "",
        f"Conservative total: **{p['total']:.3e}** · dominant source: "
        f"**{p['dominant_source']}**.",
        "",
        "**What the CI does not imply:** it is a fixed-truncation statistical "
        "interval. It does not bound the truncation error (that is the separate "
        "certified-enclosure component) and makes no continuum claim.",
        "",
        "_Generated by `scripts/run_error_budget.py`._",
    ]
    path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
