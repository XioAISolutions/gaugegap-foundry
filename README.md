# GaugeGap Foundry

Verification-first AI-for-science infrastructure for finite lattice gauge
benchmarks.

This repository is **not** claiming a solution to the Yang-Mills mass gap
problem. The first milestone is narrower and useful: build reproducible
finite-system benchmarks, retain negative results, and create the measurement
and verification rails needed before any serious theorem-adjacent claim can be
made.

## Current benchmark

`gaugegap-0001` is a finite transverse-field Ising chain used as a Z2 dual-chain
sanity benchmark. It validates the hypothesis registry, exact diagonalization
path, run ledger, CSV/JSONL export, and plot generation.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python scripts/run_gap_sweep.py
python -m unittest discover -s tests
```

Outputs land in `results/baselines/` by default:

- `gaugegap-0001-gap-sweep.jsonl`
- `gaugegap-0001-gap-sweep.csv`
- `gaugegap-0001-gap-sweep.svg`

## Program direction

The foundry is designed around a verification ladder:

1. register each hypothesis with explicit kill criteria;
2. compute an exact classical baseline;
3. compare independent implementations;
4. add noiseless and noisy simulators;
5. use hardware or analogue backends only after local checks pass;
6. publish reproducible artifacts with finite-system scope stated clearly.

The near-term backend order is:

1. local exact diagonalization;
2. IBM/Qiskit local Pauli-operator validation;
3. IBM/Qiskit local statevector and noisy simulation;
4. optional IBM Runtime hardware;
5. Quantinuum and AWS Braket/QuEra adapters once the local interface is stable.

Install optional IBM/Qiskit dependencies with:

```bash
python -m pip install -e '.[quantum]'
python scripts/run_gap_sweep.py --method qiskit-pauli --sizes 4,6 --field-points 3
```

## Repository layout

```text
docs/           roadmap and methods notes
hypotheses/     registered finite-system hypotheses
scripts/        reproducible experiment entrypoints
src/gaugegap/   package code
tests/          unit tests and smoke coverage
results/        small checked-in baseline artifacts
```

## Claim boundary

Use language like:

> finite-system gap benchmark

Do not use language like:

> proof of the Yang-Mills mass gap

That boundary is intentional. The project earns credibility by making every
small claim reproducible before expanding scope.
