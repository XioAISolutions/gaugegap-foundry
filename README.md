# GaugeGap Foundry

Verification-first AI-for-science infrastructure for Millennium Prize-adjacent finite-system benchmarks.

## Current Status

This repository is **not** claiming a solution to any Millennium Prize problem. It builds reproducible finite-system benchmarks, retains negative results, and creates verification infrastructure for theorem-adjacent progress.

The current CurveRank work includes a **computer-assisted spectral screening result** for Berry-Keating-style operator candidates. Treat this as a local, reproducible negative-result artifact that still needs independent expert review before any publication claim.

📄 Example certificate: `results/sprint-now/proof_certificate.json`  
📊 Example summary: `results/sprint-now/PROOF_SUMMARY.md`

---

## Current Benchmarks

### GaugeGap Track: Yang-Mills-adjacent finite gauge systems

**Natural progression**: Z₂ → U(1) → SU(2) → SU(3) → continuum Yang-Mills research questions.

1. **`gaugegap-0001`**: Z₂ dual-chain / Ising sanity benchmark
   - finite transverse-field Ising chain
   - validates hypothesis registry and exact diagonalization

2. **`gaugegap-0002`**: Z₂ plaquette chain
   - finite Z₂ lattice gauge toy benchmark
   - Hamiltonian: `H = -J sum_p prod_{l in p} Z_l - h sum_l X_l`
   - Pauli/Qiskit-compatible operator export

3. **`gaugegap-u1-0001`**: U(1) compact gauge
   - finite-lattice U(1) gauge theory in 2+1D
   - truncated link Hilbert spaces

4. **`gaugegap-0003`**: SU(2) pure gauge
   - finite-lattice SU(2) pure gauge theory in 2+1D
   - first non-abelian finite benchmark in the series

5. **`gaugegap-0004`**: SU(2) gauge-matter
   - SU(2) gauge + matter fields
   - string-breaking dynamics and meson-spectrum benchmarks

6. **`gaugegap-0005`**: SU(3) QCD-like finite benchmark
   - finite-lattice SU(3) pure gauge theory
   - closest current finite-system analog in this repo to Yang-Mills-style gauge dynamics
   - quantum-provider adapters are optional and require credentials

**Boundary**: all GaugeGap items above are finite-system benchmarks only; no continuum Yang-Mills mass-gap claim.

### FlowGap Track: Navier-Stokes-adjacent finite PDE systems

- **`flowgap-0001`**: Burgers equation surrogate
  - viscous Burgers as a Navier-Stokes-adjacent proxy
  - pressure-Poisson subroutine benchmarks

### CurveRank Track: Riemann-adjacent spectral screening

- **`curverank-0001`**: spectral operator screening
  - candidate operator screening against zeta-zero-inspired targets
  - Berry-Keating-style negative-result artifact
  - quantum phase-estimation path is exploratory

## Quick Start

### Reproduce the local spectral screening artifact

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[spectral]"

python scripts/run_curverank_screen.py \
    --family xp \
    --n-basis 10,15,20 \
    --k-zeros 20 \
    --output-dir results/verify

cat results/verify/curverank-0001-spectral-screen.csv
```

### Run core benchmarks

```bash
pip install -e '.[all]'

# GaugeGap
python scripts/run_gap_sweep.py
python scripts/run_z2_plaquette.py
python scripts/run_z2_plaquette_sweep.py
python scripts/run_gaugegap_u1.py
python scripts/run_gaugegap_su2_pure.py
python scripts/run_gaugegap_su3_pure.py

# FlowGap
python scripts/run_flowgap_burgers.py

# CurveRank
python scripts/run_curverank_screen.py --family xp --n-basis 10,15,20,25,30

# Tests
python -m pytest
```

### Claim-boundary audit and proofpack

```bash
python scripts/claim_boundary_audit.py --strict
python scripts/generate_reproducibility_proofpack.py --output-dir results/proofpack
```

The proofpack writes a JSON manifest, a Markdown summary, command logs, output hashes, and the claim boundary used for the run.

### Run SU(3) finite benchmark

```bash
python scripts/run_gaugegap_su3_pure.py \
    --lattice-sizes 2x2 \
    --g-coupling-min 0.5 \
    --g-coupling-max 2.0 \
    --g-coupling-points 5 \
    --truncation 0.5 \
    --output-dir results/baselines

cat results/baselines/gaugegap-0005-su3-pure-sweep.csv
```

Optional hardware submission commands require provider credentials and should be treated as exploratory finite-system runs, not proof artifacts.

### Docker Deployment

```bash
docker-compose up
docker-compose --profile gaugegap up
docker-compose --profile flowgap up
docker-compose --profile curverank up
```

See `DEPLOYMENT.md` for the deployment guide.

## Program Direction

The foundry is designed around a verification ladder:

1. register each hypothesis with explicit kill criteria;
2. compute an exact classical baseline;
3. compare independent implementations;
4. add noiseless and noisy simulators;
5. use hardware or analogue backends only after local checks pass;
6. publish reproducible artifacts with finite-system scope stated clearly.

The backend order is:

1. local exact diagonalization;
2. local Pauli-operator validation;
3. local statevector and shot-based simulation;
4. optional provider hardware submission;
5. independent expert review before any strong publication claim.

## Repository Layout

```text
docs/           roadmap and methods notes
hypotheses/     registered finite-system hypotheses
scripts/        reproducible experiment entrypoints
src/gaugegap/   package code
tests/          unit tests and smoke coverage
results/        small checked-in baseline artifacts
```

## Claim Boundary

Use language like:

> finite-system benchmark

> local screening artifact

> candidate negative result requiring independent review

Do not use language like:

> proof of the Yang-Mills mass gap

> solution to a Millennium Prize problem

> prize-ready theorem

That boundary is intentional. The project earns credibility by making every small claim reproducible before expanding scope.
