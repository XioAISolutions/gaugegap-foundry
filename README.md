# GaugeGap Foundry

Verification-first AI-for-science infrastructure for finite lattice gauge
benchmarks.

This repository is **not** claiming a solution to the Yang-Mills mass gap
problem. The first milestone is narrower and useful: build reproducible
finite-system benchmarks, retain negative results, and create the measurement
and verification rails needed before any serious theorem-adjacent claim can be
made.

## Current benchmarks

`gaugegap-0001` is a finite transverse-field Ising chain used as a Z2 dual-chain
sanity benchmark. It validates the hypothesis registry, exact diagonalization
path, run ledger, CSV/JSONL export, and plot generation.

`gaugegap-0002` is a finite Z2 lattice gauge toy benchmark on an open chain of
plaquettes. Its Hamiltonian is:

```text
H = -J sum_p prod_{l in p} Z_l - h sum_l X_l
```

It has three local paths:

- dense exact diagonalization with `numpy.linalg.eigh`;
- Pauli/Qiskit-compatible operator export checked against the dense matrix;
- a local statevector VQE-style prototype for simulator-loop development.

`gaugegap-0003` is a finite spectral-gap candidate search layer. It ranks small
Z2 plaquette families by finite gap size, finite-size survival, perturbation
stability, Pauli dense replica agreement, residual norms, and claim-boundary
compliance. It writes JSON/JSONL/CSV/Markdown rankings plus per-candidate
dossiers.

Boundary: **Finite Z2 lattice gauge toy benchmark only; no continuum
Yang-Mills mass-gap claim.**

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python scripts/run_gap_sweep.py
python scripts/run_z2_plaquette.py --output-dir /tmp/gaugegap-0002-exact
python scripts/run_quantum_gap_replica.py --output-dir /tmp/gaugegap-0002-replica
python scripts/run_z2_plaquette_sweep.py --output-dir /tmp/gaugegap-0002-sweep --run-id smoke
python scripts/run_vqe_gap.py --output-dir /tmp/gaugegap-0002-vqe --samples 64
python scripts/search_gap_candidates.py --output-dir /tmp/gaugegap-0003 --max-candidates 10
python -m pytest
```

A small `gaugegap-0003` smoke run:

```bash
python scripts/search_gap_candidates.py \
  --output-dir /tmp/gaugegap-0003-smoke \
  --n-plaquettes 1 \
  --plaquette-couplings 1.0 \
  --field-points 2 \
  --max-candidates 1
```

Outputs land in `results/baselines/` by default for `gaugegap-0001`, and in the
selected output directory for later milestones.

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
3. IBM/Qiskit local statevector and shot-based Aer simulation;
4. optional IBM Runtime hardware;
5. Quantinuum and AWS Braket/QuEra adapters once the local interface is stable.

Install optional IBM/Qiskit dependencies with:

```bash
python -m pip install -e '.[quantum]'
python scripts/run_gap_sweep.py --method qiskit-pauli --sizes 4,6 --field-points 3
python scripts/run_quantum_gap_replica.py --output-dir /tmp/gaugegap-0002-replica-qiskit
python scripts/run_dynamics.py --backend statevector --n-sites 4 --times 0,0.5
python scripts/run_dynamics.py --backend aer-sampler --n-sites 4 --times 0,0.5 --shots 512
python scripts/run_dynamics.py --backend aer-sampler --noise depolarizing --n-sites 4 --times 0,0.5 --shots 512
python scripts/analyze_dynamics.py
python scripts/quantum_status.py
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

`scripts/analyze_dynamics.py` compares statevector, clean Aer, and noisy Aer
dynamics outputs, assigns `pass` / `warning` / `fail` verdicts from fixed
tolerances, and writes summary CSV/JSON plus an SVG observable plot.

`scripts/quantum_status.py` answers the key boundary question: the repository
currently uses quantum operators, quantum circuits, and quantum simulators, but
it has not yet submitted a circuit to real QPU hardware.

See `docs/gaugegap-0002.md` for the finite Z2 plaquette benchmark details.
See `docs/gaugegap-0003-ai-gap-search.md` for the candidate search layer.

## Claim boundary

Use language like:

> finite-system gap benchmark

Do not use language like:

> proof of the Yang-Mills mass gap

That boundary is intentional. The project earns credibility by making every
small claim reproducible before expanding scope.
