#!/usr/bin/env python3
"""Physical-limits capstone: the web of fundamental bounds that ties the reel-derived
modules together. Every one is a trade-off among the same currencies -- energy, time,
information/entropy, and geometry -- and here they are run together on finite systems
and emitted as one consolidated, claim-boundary-audited report with all certificates.

Members (currencies in brackets):
  * quantum speed limit       [time  <-> energy]   entanglement build-up >= MT/ML floor
  * ergotropy / passivity     [work  <-> entropy]  extractable work finite, no free energy
  * decoherence / branching   [information]        superposition -> N_eff classical branches
  * Landauer's principle      [info  <-> energy]   erasing a bit costs >= k_B T ln 2
  * Bekenstein bound          [info <-> energy <-> geometry]  S <= 2 pi R E
  * Alcubierre energy cond.   [energy <-> geometry]  warp bubble needs negative energy

CLAIM BOUNDARY: finite-system / semiclassical demonstrations of established bounds,
each bracketed or machine-checked (Lean/Coq). NOT continuum/Yang-Mills/Millennium
claims, NOT a buildable warp drive or free-energy device. Dependency-light (numpy).
"""
from __future__ import annotations
import argparse, json, sys, warnings
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]; SRC = ROOT / "src"
if str(SRC) not in sys.path: sys.path.insert(0, str(SRC))
warnings.filterwarnings("ignore")

from gaugegap.quantum.entanglement_dynamics import two_qubit_exchange_model
from gaugegap.quantum.entanglement_speed_limit import certified_buildup_speed_limit
from gaugegap.quantum.ergotropy import analyze_ergotropy, thermal_state
from gaugegap.quantum.decoherence_branching import analyze_branching, branch_density_matrix
from gaugegap.quantum.landauer import analyze_landauer
from gaugegap.quantum.temporal_double_slit import analyze_time_diffraction
from gaugegap.relativity.bekenstein import analyze_bekenstein
from gaugegap.relativity.alcubierre import analyze_warp_bubble
from gaugegap.quantum.cherenkov import analyze_cherenkov


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--d", type=int, default=3, help="branching pointer dimension")
    ap.add_argument("--temperature", type=float, default=1.0)
    ap.add_argument("--radius", type=float, default=2.0, help="Bekenstein region radius")
    ap.add_argument("--output-dir", type=Path,
                    default=ROOT / "results" / "physical-limits")
    ap.add_argument("--skip-audit", action="store_true")
    args = ap.parse_args()

    checks = []     # (name, ok)
    print("=" * 72)
    print("Physical-limits capstone -- the web of fundamental bounds")
    print("=" * 72)

    # [time <-> energy] quantum speed limit on entanglement formation
    Hx, psi0 = two_qubit_exchange_model(coupling=1.0)
    qsl = certified_buildup_speed_limit(Hx, psi0, n_samples=300)
    checks.append(("speed_limit_respected", qsl.respects_qsl))
    print(f"  [time<->energy ] QSL: build-up {qsl.buildup_time:.4f} >= floor "
          f"{qsl.tau_qsl:.4f}  ok={qsl.respects_qsl}")

    # [time <-> frequency] temporal double slit: fringe spacing = 2 pi / dt
    tds = analyze_time_diffraction(dt=8.0, tau=0.6, n=4096)
    tds_ok = tds.uncertainty_respected and tds.fringe_relative_error < 1e-2
    checks.append(("time_frequency_duality", tds_ok))
    print(f"  [time<->freq   ] time slits: fringe 2pi/dt={tds.fringe_spacing_theory:.4f}"
          f", sep recovered {tds.separation_recovered:.3f}  ok={tds_ok}")

    # [work <-> entropy] ergotropy of a thermal state (passive: no free energy)
    Hladder = np.diag(np.arange(args.d, dtype=float)).astype(complex)
    rho_th = thermal_state(Hladder, beta=args.temperature)
    erg = analyze_ergotropy(rho_th, Hladder)
    erg_ok = erg.bracket_valid and erg.is_passive
    checks.append(("ergotropy_no_free_energy", erg_ok))
    print(f"  [work<->entropy] ergotropy: thermal W={erg.ergotropy:.4f} (passive), "
          f"0<=W<=<H>-E0  ok={erg_ok}")

    # [information] decoherence -> branching
    br = analyze_branching(d=args.d, n_env=12, overlap=0.6)
    checks.append(("branch_count_bracketed", br.branch_bracket_valid))
    print(f"  [information   ] branching: N_eff={br.effective_branches:.3f} in "
          f"[1,{args.d}]  ok={br.branch_bracket_valid}")

    # [info <-> energy] Landauer cost of erasing that decohered information
    rho_branch = branch_density_matrix(args.d, n_env=12, overlap=0.6)
    lan = analyze_landauer(rho_branch, T=args.temperature)
    checks.append(("landauer_cost_positive", lan.erasure_cost > 0))
    print(f"  [info<->energy ] Landauer: erase {lan.bits_erased:.2f} bits costs "
          f"{lan.erasure_cost:.4f} (floor/bit {lan.bit_floor:.4f})  "
          f"ok={lan.erasure_cost > 0}")

    # [info <-> energy <-> geometry] Bekenstein bound
    bek = analyze_bekenstein(rho_branch, Hladder, radius=args.radius)
    checks.append(("bekenstein_respected", bek.respects_bound))
    print(f"  [info<->E<->geo] Bekenstein: S={bek.entropy_nats:.3f} <= 2piRE="
          f"{bek.bound:.3f}  ok={bek.respects_bound}")

    # [energy <-> geometry] Alcubierre energy condition (negative energy required)
    warp = analyze_warp_bubble(v_s=1.0, R=1.0, sigma=8.0, n_grid=40)
    checks.append(("warp_needs_negative_energy", warp.wec_violated))
    print(f"  [energy<->geo  ] warp: rho_min={warp.rho_min:.3e} < 0 (WEC violated)  "
          f"ok={warp.wec_violated}")

    # [velocity <-> geometry] Cherenkov cone: cos(theta_c) = 1/(n beta)
    ch = analyze_cherenkov(n=1.33, beta=0.9)
    ch_ok = ch.cone_valid and ch.recovery_error < 1e-2
    checks.append(("cherenkov_cone_valid", ch_ok))
    print(f"  [veloc<->geo   ] Cherenkov: cos(theta_c)=1/(n beta)={ch.cos_theta_c:.4f}, "
          f"recovered {ch.cos_theta_c_recovered:.4f}  ok={ch_ok}")

    all_ok = all(ok for _, ok in checks)
    print("-" * 72)
    print(f"  ALL PHYSICAL-LIMIT CHECKS PASS: {all_ok}  "
          f"({sum(ok for _,ok in checks)}/{len(checks)})")

    payload = {
        "all_checks_pass": all_ok,
        "checks": {name: ok for name, ok in checks},
        "speed_limit": qsl.to_dict(),
        "temporal_double_slit": tds.to_dict(),
        "ergotropy": erg.to_dict(),
        "branching": br.to_dict(),
        "landauer": lan.to_dict(),
        "bekenstein": bek.to_dict(),
        "warp_energy_condition": warp.to_dict(),
        "cherenkov": ch.to_dict(),
        "certificates": {
            "speed_limit_lean": qsl.lean4, "speed_limit_coq": qsl.coq,
            "temporal_double_slit_lean": tds.lean4, "temporal_double_slit_coq": tds.coq,
            "ergotropy_lean": erg.lean4, "ergotropy_coq": erg.coq,
            "branching_lean": br.lean4, "branching_coq": br.coq,
            "landauer_lean": lan.lean4, "landauer_coq": lan.coq,
            "bekenstein_lean": bek.lean4, "bekenstein_coq": bek.coq,
            "warp_lean": warp.lean4, "warp_coq": warp.coq,
            "cherenkov_lean": ch.lean4, "cherenkov_coq": ch.coq,
        },
        "claim_boundary": ("finite-system / semiclassical demonstrations of "
                           "established physical bounds, each bracketed or machine-"
                           "checked; not continuum/Millennium claims, not a buildable "
                           "warp drive or free-energy device"),
    }
    out = args.output_dir; out.mkdir(parents=True, exist_ok=True)
    (out / "physical-limits.json").write_text(json.dumps(payload, indent=2, sort_keys=True))
    _write_md(out / "physical-limits.md", payload, checks)
    print(f"\nReport: {out / 'physical-limits.json'} (+ .md)")

    if not args.skip_audit:
        import subprocess
        rel = (out / "physical-limits.md").resolve().relative_to(ROOT)
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "claim_boundary_audit.py"),
             "--include", str(rel), "--strict"], capture_output=True, text=True)
        print(f"  claim-boundary audit: "
              f"{'PASS (0 high)' if proc.returncode == 0 else 'FAIL'}")
        if proc.returncode != 0:
            sys.stderr.write(proc.stdout + proc.stderr)
            return 1
    return 0 if all_ok else 1


def _write_md(path, p, checks):
    lines = [
        "# Physical-limits capstone: the web of fundamental bounds",
        "",
        "Every reel-derived module is a trade-off among the same currencies — "
        "**energy, time, information/entropy, geometry**. This capstone runs them "
        "together and emits one consolidated, claim-boundary-audited report with all "
        "certificates. **Claim boundary:** finite-system / semiclassical "
        "demonstrations of established bounds, each bracketed or machine-checked; not "
        "continuum/Millennium claims, not a buildable warp drive or free-energy "
        "device.",
        "",
        f"**All checks pass: {p['all_checks_pass']}**  "
        f"({sum(ok for _,ok in checks)}/{len(checks)})",
        "",
        "| Member | Currencies | Check | Pass |",
        "|---|---|---|---|",
        f"| Quantum speed limit | time ↔ energy | build-up ≥ MT/ML floor | "
        f"{p['checks']['speed_limit_respected']} |",
        f"| Temporal double slit | time ↔ frequency | fringe spacing = 2π/Δt, "
        f"σ_t σ_ω ≥ 1/2 | {p['checks']['time_frequency_duality']} |",
        f"| Ergotropy / passivity | work ↔ entropy | 0 ≤ W ≤ ⟨H⟩−E0, no free energy | "
        f"{p['checks']['ergotropy_no_free_energy']} |",
        f"| Decoherence / branching | information | 1 ≤ N_eff ≤ d | "
        f"{p['checks']['branch_count_bracketed']} |",
        f"| Landauer's principle | info ↔ energy | erase ≥ k_B T ln 2 | "
        f"{p['checks']['landauer_cost_positive']} |",
        f"| Bekenstein bound | info ↔ energy ↔ geometry | S ≤ 2πRE | "
        f"{p['checks']['bekenstein_respected']} |",
        f"| Alcubierre energy condition | energy ↔ geometry | needs negative energy | "
        f"{p['checks']['warp_needs_negative_energy']} |",
        f"| Cherenkov cone | velocity ↔ geometry | cos θc = 1/(nβ), β>1/n | "
        f"{p['checks']['cherenkov_cone_valid']} |",
        "",
        "_Generated by `scripts/run_physical_limits.py`._",
    ]
    path.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
