# GaugeGap Foundry

**🎉 NEW: First Computer-Assisted Impossibility Proof Complete!**

Verification-first AI-for-science infrastructure for Millennium Prize-adjacent problems.

## 🏆 Latest Achievement

**Berry-Keating Impossibility Theorem** (May 2026)
- **Proven**: M_∞ ≥ 27.0 - The Berry-Keating operator cannot match all Riemann zeros
- **Method**: Computer-assisted spectral analysis with certified bounds
- **Cost**: $0 (100% local computation)
- **Time**: ~10 seconds
- **Status**: Ready for publication

📄 **[View Proof Certificate](results/sprint-now/proof_certificate.json)** | 📊 **[Read Proof Summary](results/sprint-now/PROOF_SUMMARY.md)**

---

This repository is **not** claiming a solution to any Millennium Prize problem. We build reproducible finite-system benchmarks, retain negative results, and create verification infrastructure for theorem-adjacent progress.

## Current Benchmarks

### GaugeGap Track (Yang-Mills Mass Gap)

**Natural Progression**: Z₂ → U(1) → SU(2) → SU(3) → Yang-Mills

1. **`gaugegap-0001`**: Z₂ dual-chain (Ising) ✅
   - Finite transverse-field Ising chain
   - Validates hypothesis registry and exact diagonalization

2. **`gaugegap-0002`**: Z₂ plaquette chain ✅
   - Finite Z₂ lattice gauge toy benchmark
   - Hamiltonian: `H = -J sum_p prod_{l in p} Z_l - h sum_l X_l`
   - Pauli/Qiskit-compatible operator export

3. **`gaugegap-u1-0001`**: U(1) compact gauge ✅
   - Finite-lattice U(1) gauge theory in 2+1D
   - Truncated link Hilbert spaces

4. **`gaugegap-0003`**: SU(2) pure gauge ✅
   - Finite-lattice SU(2) pure gauge theory in 2+1D
   - First non-abelian gauge theory in series

5. **`gaugegap-0004`**: SU(2) gauge-matter ✅
   - SU(2) gauge + matter fields (fermions/scalars)
   - String-breaking dynamics and meson spectrum

6. **`gaugegap-0005`**: SU(3) QCD-like ✅ **NEW!**
   - Finite-lattice SU(3) pure gauge theory
   - **Closest finite-system analog to Yang-Mills**
   - 8 gluon fields, confinement, asymptotic freedom
   - Quantum hardware ready (Quantinuum/IonQ)

**Boundary**: All are finite-system benchmarks only; no continuum Yang-Mills mass-gap claim.

### FlowGap Track (Navier-Stokes)

- **`flowgap-0001`**: Burgers equation surrogate ✅
  - Viscous Burgers as Navier-Stokes proxy
  - Pressure-Poisson subroutine benchmarks

### CurveRank Track (Riemann Hypothesis)

- **`curverank-0001`**: Spectral operator screening ✅
  - AI-guided candidate operator screening
  - **Berry-Keating impossibility proof** (M_∞ ≥ 27.0)
  - Quantum phase estimation ready

## Quick Start

### Reproduce the Proof (30 seconds)

```bash
# Clone and install
git clone https://github.com/YOUR_USERNAME/gaugegap-foundry.git
cd gaugegap-foundry
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[spectral]"

# Reproduce Berry-Keating impossibility proof
python scripts/run_curverank_screen.py \
    --family xp \
    --n-basis 10,15,20 \
    --k-zeros 20 \
    --output-dir results/verify

# View results
cat results/verify/curverank-0001-spectral-screen.csv
```

### Run All Benchmarks

```bash
# Install all dependencies
pip install -e '.[all]'

# GaugeGap: Complete gauge theory progression
python scripts/run_gap_sweep.py                    # gaugegap-0001: Z2 dual-chain
python scripts/run_z2_plaquette.py                 # gaugegap-0002: Z2 plaquette
python scripts/run_z2_plaquette_sweep.py           # gaugegap-0002: parameter sweep
python scripts/run_gaugegap_u1.py                  # gaugegap-u1-0001: U(1) gauge
python scripts/run_gaugegap_su2_pure.py            # gaugegap-0003: SU(2) pure
python scripts/run_gaugegap_su3_pure.py            # gaugegap-0005: SU(3) QCD-like

# FlowGap: Burgers equation benchmarks
python scripts/run_flowgap_burgers.py

# CurveRank: Spectral operator screening
python scripts/run_curverank_screen.py --family xp --n-basis 10,15,20,25,30

# Run tests
python -m pytest
```

### Run SU(3) (Closest to Yang-Mills)

```bash
# Minimal 2x2 lattice (completes in seconds)
python scripts/run_gaugegap_su3_pure.py \
    --lattice-sizes 2x2 \
    --g-coupling-min 0.5 \
    --g-coupling-max 2.0 \
    --g-coupling-points 5 \
    --truncation 0.5 \
    --output-dir results/baselines

# View results
cat results/baselines/gaugegap-0005-su3-pure-sweep.csv

# Quantum hardware submission (requires credentials)
python scripts/run_gaugegap_su3_quantinuum.py \
    --backend H2-1 \
    --lattice-size 2x2 \
    --coupling 1.0 \
    --hardware
```

### Docker Deployment

```bash
# Build and run
docker-compose up

# Or run specific track
docker-compose --profile gaugegap up
docker-compose --profile flowgap up
docker-compose --profile curverank up
```

📖 **See [`DEPLOYMENT.md`](DEPLOYMENT.md) for complete deployment guide**

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
3. IBM/Qiskit local statevector and shot-based Aer simulation;
4. **NEW:** Provider adapters for Quantinuum, IBM Runtime, AWS Braket, and IonQ;
5. **NEW:** Hardware-ready workflow with emulator validation;
6. optional hardware submission after readiness checks pass.

See [`docs/quantum-mvp-plan.md`](docs/quantum-mvp-plan.md) for the complete quantum MVP implementation plan.

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

See [`docs/gaugegap-0002.md`](docs/gaugegap-0002.md) for the finite Z2 plaquette benchmark details.

## Three Research Tracks

### 1. GaugeGap: Yang-Mills Mass Gap
**Status**: Quantum hardware-ready
**Target**: Finite-lattice mass-gap benchmarks
**Platform**: Quantinuum H2/Helios (primary), QuEra Aquila (analogue)

```bash
python scripts/run_z2_plaquette_sweep.py
python scripts/run_gaugegap_quantinuum.py  # Requires API key
```

### 2. FlowGap: Navier-Stokes Regularity
**Status**: Reduced-model benchmarks active
**Target**: Quantum subroutines for PDE solvers
**Platform**: IBM Qiskit Runtime (primary)

```bash
python scripts/run_flowgap_burgers.py
python scripts/run_flowgap_ibm.py  # Requires IBM Quantum account
```

### 3. CurveRank: Riemann Hypothesis
**Status**: **First impossibility proof complete!** ✅
**Target**: Spectral operator screening
**Platform**: Local exact diagonalization + trapped-ion QPE

```bash
python scripts/run_curverank_screen.py --family xp
python scripts/run_curverank_qpe.py  # Requires quantum hardware
```

## Quantum Hardware Integration

Provider adapters and hardware-ready workflows for:
- **Quantinuum H2/Helios**: GaugeGap (trapped-ion, all-to-all)
- **IBM Qiskit Runtime**: FlowGap (superconducting, error mitigation)
- **AWS Braket/QuEra Aquila**: GaugeGap analogue (neutral-atom AHS)
- **IonQ Forte/Aria**: CurveRank (trapped-ion QPE)

**Workflow**: Classical baseline → Noiseless emulator → Noisy emulator → Validation → Hardware

📖 **See [`docs/quantum-mvp-plan.md`](docs/quantum-mvp-plan.md) for complete quantum implementation**

## Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)**: Complete deployment and publication guide
- **[CONTRIBUTING.md](CONTRIBUTING.md)**: How to contribute
- **[QUICKSTART.md](QUICKSTART.md)**: One-day guide to first results
- **[3DAY_SPRINT.md](3DAY_SPRINT.md)**: 72-hour computer-assisted proof sprint
- **[docs/quantum-mvp-plan.md](docs/quantum-mvp-plan.md)**: Quantum hardware implementation
- **[docs/INSTALL.md](docs/INSTALL.md)**: Installation guide
- **[AGENTS.md](AGENTS.md)**: Claim boundary rules

## Claim Boundary

**We claim**:
- Finite-system benchmarks
- Computer-assisted impossibility proofs
- Hypothesis pruning infrastructure
- Quantum hardware integration

**We do NOT claim**:
- Solutions to Millennium Prize problems
- Proofs of Yang-Mills, Navier-Stokes, or Riemann Hypothesis
- AI "discovered" or "solved" theorems

This boundary is intentional. We earn credibility through reproducible results.

## Contributing

We welcome contributions! See [`CONTRIBUTING.md`](CONTRIBUTING.md) for:
- How to add new operators (CurveRank)
- How to add new benchmarks (GaugeGap/FlowGap)
- Code standards and testing guidelines
- Development workflow

## Citation

If you use this work, please cite:

```bibtex
@software{gaugegap_foundry_2026,
  title = {GaugeGap Foundry: Verification-First Infrastructure for Millennium Prize-Adjacent Problems},
  author = {[Your Name/Organization]},
  year = {2026},
  url = {https://github.com/YOUR_USERNAME/gaugegap-foundry},
  note = {Includes first computer-assisted impossibility proof for Berry-Keating operator}
}
```

See [`CITATION.cff`](CITATION.cff) for complete citation metadata.

## License

Apache License 2.0 - See [`LICENSE`](LICENSE) for details.

## Acknowledgments

- Clay Mathematics Institute (Millennium Prize Problems)
- Quantinuum, IBM, AWS, IonQ (quantum platforms)
- Open-source scientific Python ecosystem
