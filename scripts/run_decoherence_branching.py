#!/usr/bin/env python3
"""Decoherence and branching: how a quantum superposition (a web of weighted
possibilities) becomes a set of effectively-classical branches through entanglement
with an environment (Zurek einselection / the Everett branching mechanism).

Shows the l1 coherence decaying and the effective branch count N_eff = 1/Tr(rho^2)
running from 1 (one coherent quantum state) to d (d decohered branches), and emits a
discharged Lean 4 / Coq certificate that 1 <= N_eff <= d.

CLAIM BOUNDARY: a finite, exact model of a physical MECHANISM. It makes NO
metaphysical claim and says nothing about the existence or nature of any creator /
deity / "the universe as a whole" -- only how classical branch structure emerges from
entanglement with an environment.
"""
from __future__ import annotations
import argparse, json, sys, warnings
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]; SRC = ROOT / "src"
if str(SRC) not in sys.path: sys.path.insert(0, str(SRC))
warnings.filterwarnings("ignore")
from gaugegap.quantum.decoherence_branching import (
    analyze_branching, decoherence_sweep, verify_reduced_state)
from gaugegap.visualization.svg import SVGCanvas


def _plot(path, ns, coh, neff, d):
    W = H = 520; pad = 64
    c = SVGCanvas(W, H)
    nmax = max(ns) or 1
    cohmax = max(coh) or 1.0
    c.line(pad, H - pad, W - pad, H - pad, stroke="#30363d")
    c.line(pad, pad, pad, H - pad, stroke="#30363d")
    def tf_coh(n, v):
        return (pad + n / nmax * (W - 2 * pad), (H - pad) - v / cohmax * (H - 2 * pad))
    def tf_neff(n, v):
        return (pad + n / nmax * (W - 2 * pad), (H - pad) - (v / d) * (H - 2 * pad))
    # N_eff -> d asymptote
    yd = (H - pad) - (H - 2 * pad)
    c.line(pad, yd, W - pad, yd, stroke="#8b949e", stroke_width=1.0, opacity=0.5)
    c.polyline([tf_coh(n, v) for n, v in zip(ns, coh)], stroke="#58a6ff", stroke_width=2.0)
    c.polyline([tf_neff(n, v) for n, v in zip(ns, neff)], stroke="#f0c674", stroke_width=2.0)
    c.text(W / 2, 28, "Decoherence -> branching", size=15)
    c.text(W / 2, H - 22, "environment size n_env", size=11, fill="#8b949e")
    c.text(pad + 6, pad + 4, f"gold: N_eff -> d={d}", size=10, fill="#f0c674", anchor="start")
    c.text(pad + 6, pad + 20, "blue: l1 coherence -> 0", size=10, fill="#58a6ff", anchor="start")
    c.write(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--d", type=int, default=3, help="pointer-system dimension")
    ap.add_argument("--overlap", type=float, default=0.6,
                    help="per-register environment overlap between pointer values")
    ap.add_argument("--n-env", type=int, default=12, help="environment registers")
    ap.add_argument("--n-env-max", type=int, default=20, help="sweep upper bound")
    ap.add_argument("--output-dir", type=Path,
                    default=ROOT / "results" / "decoherence-branching")
    ap.add_argument("--skip-audit", action="store_true")
    args = ap.parse_args()

    disc = verify_reduced_state(n_env=4, theta=0.7)
    r = analyze_branching(d=args.d, n_env=args.n_env, overlap=args.overlap)
    ns, coh, neff = decoherence_sweep(d=args.d, overlap=args.overlap,
                                      n_env_max=args.n_env_max)

    print("=" * 72)
    print("Decoherence and branching (finite einselection model)")
    print("=" * 72)
    print(f"  pointer dimension d        : {args.d}")
    print(f"  reduced-state check        : max|analytic - exact| = {disc:.1e} (exact)")
    print(f"  at n_env={args.n_env}: l1 coherence = {r.coherence:.4e}, "
          f"purity = {r.purity:.4f}")
    print(f"  Born weights sum           : {r.weights_sum:.6f} (probability conserved)")
    print(f"  effective branches N_eff   : {r.effective_branches:.4f}  "
          f"(1 = coherent state, d = decohered)")
    print(f"  certified 1 <= N_eff <= d  : {r.branch_bracket_valid}")
    print("  branch count grows as the environment records the pointer:")
    for n in (0, 2, 5, 10, args.n_env_max):
        if n <= args.n_env_max:
            print(f"    n_env={n:2d}: coherence={coh[n]:.3e}  N_eff={neff[n]:.4f}")

    out = args.output_dir; out.mkdir(parents=True, exist_ok=True)
    payload = dict(r.to_dict())
    payload["reduced_state_discrepancy"] = disc
    payload["sweep_n_env"] = ns
    payload["sweep_coherence"] = coh
    payload["sweep_effective_branches"] = neff
    payload["lean4_certificate"] = r.lean4
    payload["coq_certificate"] = r.coq
    (out / "decoherence-branching.json").write_text(json.dumps(payload, indent=2, sort_keys=True))
    (out / "branch_count.lean").write_text(r.lean4)
    (out / "branch_count.coq").write_text(r.coq)
    _plot(out / "decoherence_branching.svg", ns, coh, neff, args.d)

    holes = ("sorry" in r.lean4) or ("Admitted" in r.coq)
    (out / "decoherence-branching.md").write_text(
        "# Decoherence and branching\n\n"
        "A quantum superposition is a single coherent state -- a web of weighted "
        "possibilities (the Born weights). When an environment records which pointer "
        "state the system is in, the off-diagonal coherences decay (decoherence) and "
        "the system behaves like a set of classical branches (einselection). Here a "
        f"d={args.d} pointer decoheres as `n_env` environment registers record it: the "
        "l1 coherence falls to ~0 and the effective branch count "
        "`N_eff = 1/Tr(rho^2)` rises from 1 (one coherent state) to d (d branches), "
        "with a discharged Lean 4 / Coq certificate that `1 <= N_eff <= d`. The "
        "analytic reduced state is validated against an explicit statevector partial "
        f"trace (max difference {disc:.1e}). **Claim boundary:** a finite exact model "
        "of a physical *mechanism*; it makes NO metaphysical claim and says nothing "
        "about the existence or nature of any creator / deity / 'the universe as a "
        "whole'. Dependency-light (numpy). Not a continuum/Millennium claim.\n\n"
        f"- effective branches N_eff = **{r.effective_branches:.4f}** "
        f"(certified in [1, {args.d}] = **{r.branch_bracket_valid}**)\n"
        f"- l1 coherence at n_env={args.n_env} = **{r.coherence:.4e}**, "
        f"Born weights sum = **{r.weights_sum:.6f}**\n"
        f"- certificate hole-free = **{not holes}**\n\n"
        "![decoherence](decoherence_branching.svg)\n\n"
        "_Generated by `scripts/run_decoherence_branching.py`._\n")
    print(f"\nReport: {out / 'decoherence-branching.json'} (+ .md, .svg, .lean, .coq)")
    print(f"  certificate hole-free: {not holes}")

    if not args.skip_audit:
        import subprocess
        rel = (out / "decoherence-branching.md").resolve().relative_to(ROOT)
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "claim_boundary_audit.py"),
             "--include", str(rel), "--strict"], capture_output=True, text=True)
        print(f"  claim-boundary audit: "
              f"{'PASS (0 high)' if proc.returncode == 0 else 'FAIL'}")
        if proc.returncode != 0:
            sys.stderr.write(proc.stdout + proc.stderr)
            return 1
    return 0 if (r.branch_bracket_valid and not holes and disc < 1e-9) else 1


if __name__ == "__main__":
    raise SystemExit(main())
