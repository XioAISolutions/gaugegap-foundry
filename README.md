# GaugeGap Foundry

Verification-first AI-for-science infrastructure for Millennium Prize-adjacent finite-system benchmarks.

## Current Status

This repository is **not** claiming a solution to any Millennium Prize problem. It builds reproducible finite-system benchmarks, retains negative results, and creates verification infrastructure for theorem-adjacent progress.

The current CurveRank work includes a **computer-assisted spectral screening result** for Berry-Keating-style operator candidates. Treat this as a local, reproducible negative-result artifact that still needs independent expert review before any publication claim.

📄 Example certificate: `results/sprint-now/proof_certificate.json`  
📊 Example summary: `results/sprint-now/PROOF_SUMMARY.md`

### Hardening status

The repo now tracks a practical solution-gap scorecard and agent work orders:

- `docs/solution-gap-audit.md` — honest gap between current finite benchmarks and a true solution path.
- `docs/agent-work-orders.md` — execution-ready tasks for Codex/agent runs.
- `scripts/research_maturity_audit.py` — scans for unbounded placeholder/prototype risk.
- `Makefile` — one-command smoke, audit, proofpack, and reviewer-packet targets.

---

## Current Benchmarks

### GaugeGap Track: finite gauge-system benchmarks

**Natural progression**: Z₂ → U(1) → SU(2) → SU(3 prototype scaffold) → continuum research questions.

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

5. **`gaugegap-0004`**: SU(2) gauge-matter / hardware-readiness validation lane
   - SU(2) gauge + matter fields, string-breaking dynamics, and meson-spectrum benchmarks
   - current implementation adds a finite Z₂ candidate hardware-readiness validator before any provider submission

6. **`gaugegap-0005`**: SU(3) prototype scaffold
   - finite-system SU(3)-adjacent pipeline scaffold
   - not a completed production-grade SU(3) lattice gauge implementation yet
   - records `implementation_status=prototype_scaffold`
   - plaquette group multiplication, Gauss-law constraints, Wilson loops, and physical-subspace projection remain work-order items

7. **`gaugegap-search-0001`**: Z₂ finite gap candidate search
   - ranks finite Z₂ plaquette candidates by gap size, finite-size survival, perturbation stability, replica agreement, and residuals
   - writes JSON/JSONL/CSV/Markdown rankings plus candidate dossiers

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

## Qiskit 2.4 / IBM Runtime Findings Applied

The hardware-readiness lane follows IBM's current Qiskit pattern:

```text
map finite operator/circuit
→ inspect/transpile resources
→ execute only after local checks pass
→ analyze deviations
```

The Qiskit 2.4 release is relevant because it strengthens Pauli-centric workflows, faster QPY serialization, transpilation infrastructure, and compiled-extension paths. For this repo that means:

- keep Pauli terms as first-class artifacts;
- record resource estimates before any backend call;
- avoid hardware submission until exact and Pauli dense replicas agree;
- serialize and hash validation outputs as proofpack material;
- keep Qiskit/IBM Runtime optional because finite exact baselines must run without provider credentials.

The first implementation of this is `gaugegap-0004`, a local hardware-readiness validator for finite Z₂ candidates. It does not submit to hardware by default.

Hardware results are noisy experimental artifacts and do not constitute mathematical proof.

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
python scripts/search_gap_candidates.py --output-dir /tmp/gaugegap-search-0001 --max-candidates 10
python scripts/run_candidate_validation.py --output-dir /tmp/gaugegap-0004 --disable-qiskit-probe
python scripts/run_qiskit_candidate_validation.py --output-dir /tmp/gaugegap-qiskit-validation
python scripts/submit_ibm_runtime_candidate.py --dry-run --output-dir /tmp/gaugegap-runtime-dryrun

# FlowGap
python scripts/run_flowgap_burgers.py

# CurveRank
python scripts/run_curverank_screen.py --family xp --n-basis 10,15,20,25,30

# Tests
python -m pytest
```

### One-command reviewer workflow

```bash
make audit
make smoke
make proofpack
make reviewer-packet
```

### Claim-boundary audit and proofpack

```bash
python scripts/claim_boundary_audit.py --strict
python scripts/research_maturity_audit.py --strict
python scripts/generate_reproducibility_proofpack.py \
  --output-dir results/proofpack \
  --include-search \
  --include-validation
```

The proofpack writes a JSON manifest, a Markdown summary, command logs, output hashes, and the claim boundary used for the run. The maturity audit flags unbounded placeholder/prototype risk before public claims are made.

### Run SU(3) prototype scaffold

```bash
python scripts/run_gaugegap_su3_pure.py \
    --lattice-sizes 2x2 \
    --g-coupling-min 0.5 \
    --g-coupling-max 2.0 \
    --g-coupling-points 5 \
    --truncation 0.5 \
    --output-dir results/baselines

cat results/baselines/gaugegap-0005-su3-prototype-sweep.csv
```

Optional hardware submission commands require provider credentials and should be treated as exploratory finite-system runs, not proof artifacts.

See also:

- `docs/gaugegap-0004-hardware-readiness.md`
- `docs/qiskit-2-4-validation.md`
- `docs/ibm-runtime-submission.md`

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

> prototype scaffold

Avoid unbounded claim language such as:

> continuum Yang-Mills mass-gap proof

> Millennium Prize resolution

> theorem ready for a prize claim

That boundary is intentional. The project earns credibility by making every small claim reproducible before expanding scope.
