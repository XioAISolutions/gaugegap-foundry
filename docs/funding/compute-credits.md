# Compute / quantum research-credit proposals

Short proposals for **non-dilutive** compute — the fastest external resource
(weeks, no equity). Fill the **[brackets]**; keep every claim honest.

## A. IBM Quantum Network / research access

**Ask:** access to IBM Quantum systems + runtime minutes for finite-system QPE
benchmarks.

**Why credible:** the repo already has a working IBM Runtime path (Aer emulator +
hardware staging, error-mitigation hooks) and a hardware-feasibility report
quantifying circuit cost (`docs/curverank-ibm-runbook.md`,
`results/curverank-hardware/`). We need device time to run the staged jobs.

**Use of credits:** windowed/iterative QPE eigenvalue recovery on Open-plan
devices; compare to the exact/simulator baselines; publish a reproducible report.

## B. Cloud research credits (AWS / GCP / Azure)

**Ask:** research credits for GPU instances.

**Why credible:** an optional, capability-gated **CUDA-Q** GPU simulation backend
already exists with a CPU fallback and a benchmark
(`providers/cudaq_adapter.py`, `make cudaq-benchmark`); CPU statevector is the
bottleneck at larger qubit counts.

**Use of credits:** GPU-scaled statevector / tensor-network simulation for larger
certified-screening truncations and `g(t)` records.

## Boilerplate (reusable)

- **Project:** open-source verification-first quantum/scientific-computing infra.
- **Track record:** ~490 tests, reproducible artifacts, Lean/Coq/Isabelle proof
  export, ~35 reviewed PRs (all public).
- **Honest scope:** certified finite-system **negative** result + benchmarks;
  **not a proof** of the Riemann Hypothesis or any Millennium Prize problem.
- **Deliverable back to the program:** a public, reproducible benchmark report
  citing the granted resources.

> Blanks: legal entity, PI/contact, requested amount/quota, timeline, prior usage.
