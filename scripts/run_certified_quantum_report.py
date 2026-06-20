#!/usr/bin/env python3
"""Capstone: run every certified-quantum primitive on one operator and emit a single
consolidated, claim-boundary-audited report.

Ties together the whole Certified-Quantum program (Phases 1-5):
  * certified energy bracket  (interval lower  + Krylov-Ritz upper)         [P1]
  * Temple-Kato bracket       (Temple lower    + variational upper)         [P5]
  * quantum-validation        (QPE/ESPRIT/QCELS/Krylov vs certified)        [P2/3]
  * certified shadows         (median-of-means CIs on observables)          [P2]
  * QSVT transform            (P(spectrum), certified vs interval P([lo,hi]))[P4]
  * quantum error budget      (shot-noise CI + truncation + numerical)      [P3/5]
  * open-system steady state  (Lindbladian, cross-validated)                [P5]

CLAIM BOUNDARY: finite-system, simulation-level. Every quantum result is bracketed,
cross-validated, or certified against the interval kernel. Not a continuum/Yang-Mills/
Millennium claim; hardware stays staged behind the hardware_confirmed gate.
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
from gaugegap.certified_bracket import certified_ground_bracket, bracket_contains_exact
from gaugegap.quantum.temple_kato import certified_temple_bracket
from gaugegap.quantum_validation import validate_operator, quantum_error_budget
from gaugegap.quantum.certified_shadows import certified_shadow_estimate
from gaugegap.quantum.qsvt import qsvt_eigenvalue_transform
from gaugegap.quantum.open_system import solve_open_system

_X = np.array([[0, 1], [1, 0]], dtype=complex)
_Z = np.array([[1, 0], [0, -1]], dtype=complex)
_SM = np.array([[0, 1], [0, 0]], dtype=complex)
_I = np.eye(2, dtype=complex)


def _op(local, site, n):
    out = np.array([[1.0 + 0j]])
    for q in range(n):
        out = np.kron(out, local if q == site else _I)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--operator", default="berry_keating_xp")
    ap.add_argument("--n-basis", type=int, default=8)
    ap.add_argument("--output-dir", type=Path,
                    default=ROOT / "results" / "certified-quantum")
    ap.add_argument("--skip-audit", action="store_true")
    args = ap.parse_args()

    spec = get_operator(args.operator)
    H = spec.build(args.n_basis)
    Hh = (H + H.conj().T) / 2.0
    ev = np.linalg.eigvalsh(Hh)
    checks = []   # (name, ok)

    print("=" * 72)
    print(f"Certified-Quantum capstone — {spec.name} (n_basis={args.n_basis})")
    print("=" * 72)

    # P1 interval bracket
    b = certified_ground_bracket(H)
    b_ok = bracket_contains_exact(H, b)
    checks.append(("interval_bracket_contains_E0", b_ok))
    print(f"  [P1] interval bracket  E0 in [{b.lower:.6f},{b.upper:.6f}]  ok={b_ok}")

    # P5 Temple bracket
    t = certified_temple_bracket(H)
    checks.append(("temple_bracket_contains_E0", t.contains_exact))
    print(f"  [P5] Temple bracket    E0 in [{t.lower:.6f},{t.upper:.6f}]  "
          f"ok={t.contains_exact}")

    # P2/3 validation (numpy methods)
    reports = validate_operator(spec.name, args.n_basis, methods=("esprit", "krylov"))
    val_ok = reports["esprit"].all_certified and reports["krylov"].all_certified
    checks.append(("validation_esprit_krylov_certified", val_ok))
    print(f"  [P2] validation        esprit {reports['esprit'].n_in_enclosure}, "
          f"krylov {reports['krylov'].n_in_enclosure}  ok={val_ok}")

    # P2 certified shadows on the ground state (qubit view)
    shadows = None
    n_qubits = int(round(np.log2(Hh.shape[0])))
    if (1 << n_qubits) == Hh.shape[0]:
        psi0 = np.linalg.eigh(Hh)[1][:, 0]
        obs = {f"Z{q}": _op(_Z, q, n_qubits) for q in range(n_qubits)}
        sh = certified_shadow_estimate(psi0, obs, n_snapshots=400, n_batches=8, seed=0)
        sh_ok = all(e.covered for e in sh.values())
        checks.append(("shadow_CIs_cover_exact", sh_ok))
        shadows = {k: v.to_dict() for k, v in sh.items()}
        print(f"  [P2] certified shadows {sum(e.covered for e in sh.values())}/"
              f"{len(sh)} CIs cover exact  ok={sh_ok}")

    # P4 QSVT transform (P = x^2)
    q = qsvt_eigenvalue_transform(H, [0.0, 0.0, 1.0])
    checks.append(("qsvt_transform_certified", q.all_inside))
    print(f"  [P4] QSVT P(x)=x^2     all inside certified  ok={q.all_inside}")

    # P3/5 quantum error budget (qcels)
    eb = quantum_error_budget(spec.name, args.n_basis, method="qcels",
                              n_runs=8, shots=600)
    checks.append(("error_budget_positive_total", eb["total"] > 0))
    print(f"  [P5] error budget      total {eb['total']:.2e}, "
          f"dominant {eb['dominant_source']}")

    # P5 open system (fixed 2-site dissipative TFIM)
    Ho = _op(_X, 0, 2) + _op(_X, 1, 2) + _op(_Z, 0, 2) @ _op(_Z, 1, 2)
    osr = solve_open_system(Ho, [np.sqrt(0.3) * _op(_SM, 0, 2),
                                 np.sqrt(0.3) * _op(_SM, 1, 2)])
    checks.append(("open_system_valid_steady_state", osr.is_valid_density_matrix))
    print(f"  [P5] open system       valid steady state  ok="
          f"{osr.is_valid_density_matrix} (gap {osr.relaxation_gap:.3f})")

    all_ok = all(ok for _, ok in checks)
    print("-" * 72)
    print(f"  ALL CERTIFIED-QUANTUM CHECKS PASS: {all_ok}  "
          f"({sum(ok for _,ok in checks)}/{len(checks)})")

    payload = {
        "operator": spec.name, "n_basis": args.n_basis,
        "exact_E0": float(ev[0]), "exact_gap": float(ev[1] - ev[0]),
        "all_checks_pass": all_ok,
        "checks": {name: ok for name, ok in checks},
        "interval_bracket": b.to_dict(), "temple_bracket": t.to_dict(),
        "validation": {m: r.to_dict() for m, r in reports.items()},
        "shadows": shadows, "qsvt": q.to_dict(), "error_budget": eb,
        "open_system": osr.to_dict(),
        "claim_boundary": ("every quantum result is bracketed/cross-validated/"
                           "certified against the interval kernel; finite-system, "
                           "simulation-level; not a continuum/Millennium claim"),
    }
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / "certified-quantum.json").write_text(json.dumps(payload, indent=2, sort_keys=True))
    _write_md(out / "certified-quantum.md", payload, checks)
    print(f"\nReport: {out / 'certified-quantum.json'} (+ .md)")

    if not args.skip_audit:
        import subprocess
        rel = (out / "certified-quantum.md").resolve().relative_to(ROOT)
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "claim_boundary_audit.py"),
             "--include", str(rel), "--strict"], capture_output=True, text=True)
        print(f"  claim-boundary audit on report: "
              f"{'PASS (0 high)' if proc.returncode == 0 else 'FAIL'}")
        if proc.returncode != 0:
            sys.stderr.write(proc.stdout + proc.stderr)
            return 1
    return 0 if all_ok else 1


def _write_md(path, p, checks):
    lines = [
        "# Certified-Quantum capstone report",
        "",
        f"Operator `{p['operator']}` (n_basis {p['n_basis']}). One run of every "
        "certified-quantum primitive (Phases 1-5). **Claim boundary:** every quantum "
        "result is bracketed, cross-validated, or certified against the interval "
        "kernel; finite-system, simulation-level; not a continuum/Millennium claim.",
        "",
        f"**All checks pass: {p['all_checks_pass']}**  "
        f"({sum(ok for _,ok in checks)}/{len(checks)})",
        "",
        "| Check | Pass |",
        "|---|---|",
    ]
    for name, ok in checks:
        lines.append(f"| {name} | {ok} |")
    lines += [
        "",
        f"- Interval bracket: E0 ∈ [{p['interval_bracket']['lower']:.6f}, "
        f"{p['interval_bracket']['upper']:.6f}]",
        f"- Temple bracket: E0 ∈ [{p['temple_bracket']['lower']:.6f}, "
        f"{p['temple_bracket']['upper']:.6f}]",
        f"- Exact E0 = {p['exact_E0']:.6f}, gap = {p['exact_gap']:.6f}",
        "",
        "_Generated by `scripts/run_certified_quantum_report.py`._",
    ]
    path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
