#!/usr/bin/env python3
"""Benchmark the simulation backends: numpy vs CUDA-Q.

Times the gate-list statevector primitive (and the Trotter correlation signal)
across qubit counts on each available backend. On CPU-only machines the CUDA-Q
rows are reported as unavailable; where CUDA-Q + a GPU are present, this shows the
acceleration the optional backend buys.

CLAIM BOUNDARY: simulation timing only; nothing here changes a result or bears on
a proof of the Riemann Hypothesis.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.providers import cudaq_adapter as cq


def _layered_circuit(n: int, depth: int = 6):
    """A scalable entangling circuit: alternating ry layers + CX ladders."""
    gates = []
    rng = np.random.default_rng(0)
    for _ in range(depth):
        gates += [("ry", (q,), float(rng.uniform(0, np.pi))) for q in range(n)]
        gates += [("cx", (q, q + 1), None) for q in range(n - 1)]
    return gates


def _time(fn, repeats: int = 3) -> float:
    best = float("inf")
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        best = min(best, time.perf_counter() - t0)
    return best


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--max-qubits", type=int, default=12)
    p.add_argument("--output-dir", type=Path, default=ROOT / "results" / "cudaq-benchmark")
    args = p.parse_args()

    have_cudaq = cq.cudaq_available()
    print(f"CUDA-Q available: {have_cudaq} | backend_info: {cq.backend_info()}")
    rows = []
    for n in range(4, args.max_qubits + 1, 2):
        gates = _layered_circuit(n)
        t_np = _time(lambda: cq.numpy_statevector(gates, n))
        t_cq = (_time(lambda: cq.cudaq_statevector(gates, n)) if have_cudaq else None)
        speedup = (t_np / t_cq) if (t_cq and t_cq > 0) else None
        rows.append({"n_qubits": n, "numpy_s": t_np, "cudaq_s": t_cq,
                     "speedup": speedup})
        cq_str = f"{t_cq:.4f}s" if t_cq is not None else "n/a"
        sp_str = f"{speedup:.1f}x" if speedup else "-"
        print(f"  n={n:2d}  numpy={t_np:.4f}s  cudaq={cq_str}  speedup={sp_str}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "cudaq-benchmark.json").write_text(json.dumps({
        "claim_boundary": "Simulation timing only; not a proof of the Riemann Hypothesis.",
        "cudaq_available": have_cudaq,
        "backend_info": cq.backend_info(),
        "rows": rows,
    }, indent=2), encoding="utf-8")
    print(f"report -> {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
