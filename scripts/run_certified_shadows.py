#!/usr/bin/env python3
"""Certified classical shadows: estimate observables on a state with median-of-means
confidence bands, cross-validated against exact expectations, and fold the
statistical spread into an error budget.

Default demo: the ground state of the Berry-Keating xp truncation, estimating a few
Pauli observables (qubit view). CLAIM BOUNDARY: a statistical confidence band on a
finite-state observable at a fixed shot budget; not a continuum/Millennium claim.
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

warnings.filterwarnings("ignore")

from gaugegap.curverank_registry import get_operator
from gaugegap.quantum.certified_shadows import certified_shadow_estimate
from gaugegap.error_budget import ErrorBudget

_Z = np.diag([1, -1]).astype(complex)
_X = np.array([[0, 1], [1, 0]], dtype=complex)
_I = np.eye(2, dtype=complex)


def _kron(ops):
    out = np.array([[1.0 + 0j]])
    for o in ops:
        out = np.kron(out, o)
    return out


def _pauli_observables(n_qubits: int) -> dict:
    obs = {}
    # single-site Z on each qubit + a couple of two-site correlators
    for q in range(n_qubits):
        ops = [_Z if i == q else _I for i in range(n_qubits)]
        obs[f"Z{q}"] = _kron(ops)
    if n_qubits >= 2:
        obs["Z0Z1"] = _kron([_Z, _Z] + [_I] * (n_qubits - 2))
        obs["X0X1"] = _kron([_X, _X] + [_I] * (n_qubits - 2))
    return obs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--operator", default="berry_keating_xp")
    ap.add_argument("--n-basis", type=int, default=8)
    ap.add_argument("--n-snapshots", type=int, default=800)
    ap.add_argument("--n-batches", type=int, default=16)
    ap.add_argument("--level", type=float, default=0.95)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--output-dir", type=Path, default=ROOT / "results" / "certified-shadows")
    args = ap.parse_args()

    spec = get_operator(args.operator)
    H = spec.build(args.n_basis)
    Hh = (H + H.conj().T) / 2.0
    n_qubits = int(round(np.log2(Hh.shape[0])))
    if (1 << n_qubits) != Hh.shape[0]:
        raise SystemExit("operator dimension must be a power of two for the qubit view")
    psi = np.linalg.eigh(Hh)[1][:, 0]   # ground state

    obs = _pauli_observables(n_qubits)
    res = certified_shadow_estimate(psi, obs, n_snapshots=args.n_snapshots,
                                    n_batches=args.n_batches, level=args.level,
                                    seed=args.seed)

    print("=" * 72)
    print(f"Certified shadows — {spec.name} ground state ({n_qubits} qubits)")
    print("=" * 72)
    n_cov = 0
    for name, e in res.items():
        n_cov += int(e.covered)
        print(f"  {name:5}: {e.estimate:+.4f}  CI=[{e.ci_low:+.4f},{e.ci_high:+.4f}] "
              f"exact={e.exact:+.4f}  covered={e.covered}")
    print(f"  coverage: {n_cov}/{len(res)} CIs contain the exact value "
          f"({int(args.level*100)}% level)")

    # Fold the largest CI half-width into an error budget (statistical component).
    max_half = max((e.ci_high - e.ci_low) / 2 for e in res.values())
    budget = ErrorBudget(quantity=f"shadow_observables({spec.name})")
    budget.add("shadow_statistical_ci", max_half, "statistical", "stochastic")
    budget.add("numerical_precision", 1e-12, "numerical", "bound")

    payload = {
        "operator": spec.name, "n_basis": args.n_basis, "n_qubits": n_qubits,
        "level": args.level, "n_snapshots": args.n_snapshots, "n_batches": args.n_batches,
        "coverage": f"{n_cov}/{len(res)}",
        "observables": {k: v.to_dict() for k, v in res.items()},
        "error_budget": budget.as_dict(),
        "claim_boundary": ("median-of-means classical-shadow confidence bands on "
                           "finite-state observables; statistical, fixed shot budget; "
                           "not a continuum/Millennium claim"),
    }
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / "certified-shadows.json").write_text(json.dumps(payload, indent=2, sort_keys=True))
    lines = [
        "# Certified classical shadows",
        "",
        f"Operator `{spec.name}` ground state ({n_qubits} qubits), "
        f"{args.n_batches} batches × {args.n_snapshots} snapshots, "
        f"{int(args.level*100)}% CIs. **Claim boundary:** median-of-means shadow "
        "confidence bands on finite-state observables; statistical at a fixed shot "
        "budget; not a continuum/Millennium claim.",
        "",
        f"Coverage: **{n_cov}/{len(res)}** CIs contain the exact value.",
        "",
        "| Observable | estimate | CI | exact | covered |",
        "|---|---|---|---|---|",
    ]
    for name, e in res.items():
        lines.append(f"| {name} | {e.estimate:+.4f} | "
                     f"[{e.ci_low:+.4f}, {e.ci_high:+.4f}] | {e.exact:+.4f} | "
                     f"{e.covered} |")
    lines += ["", "_Generated by `scripts/run_certified_shadows.py`._"]
    (out / "certified-shadows.md").write_text("\n".join(lines) + "\n")
    print(f"\nReport: {out / 'certified-shadows.json'} (+ .md)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
