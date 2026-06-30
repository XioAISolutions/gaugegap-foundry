#!/usr/bin/env python3
"""Run the finite 2D incompressible Navier-Stokes surrogate (Taylor-Green vortex).

Emits reproducible evidence: per-step kinetic-energy and divergence histories, the
measured-vs-analytic energy-decay rate, a grid-refinement convergence check, and a
ledgered JSON/CSV bundle. Finite-grid evidence only; not a Navier-Stokes regularity
result or a Millennium Prize solution.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.flowgap_navier_stokes import (  # noqa: E402
    CLAIM_BOUNDARY,
    simulate_navier_stokes_2d,
)
from gaugegap.ledger import git_state, object_hash, utc_run_id, write_jsonl  # noqa: E402

HYPOTHESIS_ID = "flowgap-0005"


def _summary(result: dict[str, object]) -> dict[str, object]:
    return {k: v for k, v in result.items() if k not in {"ux_final", "uy_final"}}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--grid", type=int, default=16, help="grid points per side")
    ap.add_argument("--nu", type=float, default=0.02, help="kinematic viscosity")
    ap.add_argument("--dt", type=float, default=1.0e-3)
    ap.add_argument("--n-steps", type=int, default=200)
    ap.add_argument(
        "--refine-grid",
        type=int,
        default=24,
        help="finer grid for the convergence check (0 to skip)",
    )
    ap.add_argument("--output-dir", type=Path, default=ROOT / "results" / HYPOTHESIS_ID)
    args = ap.parse_args(argv)

    run_id = utc_run_id()
    git = git_state(ROOT)

    base = simulate_navier_stokes_2d(
        nx=args.grid, ny=args.grid, nu=args.nu, dt=args.dt, n_steps=args.n_steps
    )

    convergence: dict[str, object] | None = None
    if args.refine_grid and args.refine_grid > args.grid:
        fine = simulate_navier_stokes_2d(
            nx=args.refine_grid, ny=args.refine_grid, nu=args.nu, dt=args.dt, n_steps=args.n_steps
        )
        convergence = {
            "coarse_grid": args.grid,
            "fine_grid": args.refine_grid,
            "coarse_rate_error": base["decay_rate_relative_error"],
            "fine_rate_error": fine["decay_rate_relative_error"],
            "refinement_improves": fine["decay_rate_relative_error"] < base["decay_rate_relative_error"],
        }

    config = {
        "grid": args.grid,
        "nu": args.nu,
        "dt": args.dt,
        "n_steps": args.n_steps,
        "model": "taylor_green_vortex_2d",
    }
    payload = {
        "hypothesis_id": HYPOTHESIS_ID,
        "track": "FlowGap",
        "run_id": run_id,
        "git": git,
        "config": config,
        "config_hash": object_hash(config),
        "claim_boundary": CLAIM_BOUNDARY,
        "result": _summary(base),
        "convergence": convergence,
    }

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{HYPOTHESIS_ID}-navier-stokes.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True)
    )

    with (out / f"{HYPOTHESIS_ID}-history.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["step", "kinetic_energy", "divergence_norm"])
        for step, (energy, div) in enumerate(
            zip(base["energy_history"], base["divergence_history"])
        ):
            writer.writerow([step, energy, div])

    write_jsonl(out / f"{HYPOTHESIS_ID}-records.jsonl", [payload])

    print("=" * 72)
    print(f"FlowGap {HYPOTHESIS_ID}: 2D incompressible Navier-Stokes surrogate (Taylor-Green)")
    print(
        f"  grid={args.grid}  nu={args.nu}  energy {base['energy_history'][0]:.5f} -> "
        f"{base['energy_history'][-1]:.5f}  monotone={base['energy_monotone_nonincreasing']}"
    )
    print(
        f"  decay rate measured={base['measured_energy_decay_rate']:.5f} "
        f"analytic={base['analytic_energy_decay_rate']:.5f} "
        f"rel_err={base['decay_rate_relative_error']:.4f}"
    )
    print(f"  max divergence={base['max_divergence']:.3e}")
    if convergence:
        print(
            f"  refinement {convergence['coarse_grid']}->{convergence['fine_grid']} "
            f"improves accuracy: {convergence['refinement_improves']}"
        )
    print(f"  CLAIM BOUNDARY: {CLAIM_BOUNDARY}")
    print(f"  wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
