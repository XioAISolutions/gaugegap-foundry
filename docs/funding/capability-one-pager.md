# Capability one-pager — GaugeGap Foundry

> **[Organization / your name]** · **[email]** · **[links]**

## What it is

An open-source, **verification-first** platform for finite-system quantum and
scientific computing: certified numerics, machine-checkable proof export, a
quantum signal-extraction toolkit, honest-by-construction DSLs, and an optional
GPU backend — all reproducible and CI-gated.

## Evidence (reproducible)

- **Certified numerics** — directed-rounding interval eigenvalue enclosures;
  ~14.5× optimized, bit-identical (PR #29).
- **Machine-checkable proofs** — Lean 4 / Coq / Isabelle export of the certified
  theorem (`docs/curverank-formal-proof.md`).
- **Quantum** — QPE (register/windowed/iterative/Trotter) + IBM Runtime path;
  signal extraction (Hadamard, `g(t)`, Prony/ESPRIT, QCELS, shadows, AE).
- **Engineering** — ~490 tests, byte-reproducible proofpacks, strict
  claim-boundary audit at 0 high, optional CUDA-Q GPU backend.

## What funding accelerates

- Larger certified panels and operator families (more compute).
- GPU-scaled quantum simulation (CUDA-Q) for bigger truncations.
- Real-hardware quantum runs (IBM/cloud credits).
- Hardening the DSLs and reproducibility tooling for outside reviewers.

## Honest scope

This produces certified **finite-system** screening and benchmarks — a certified
**negative** result. It is **not a proof** of the Riemann Hypothesis or any
Millennium Prize problem, and is not presented as one. The value is rigorous,
reproducible infrastructure and capability.

> Blanks to fill before sending: organization/legal entity, team, budget ask,
> period of performance, point of contact.
