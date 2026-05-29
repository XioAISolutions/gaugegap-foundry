# GaugeGap Foundry Roadmap

Date: 2026-05-28 (Updated with Quantum MVP Plan)

## Position

The credible target is not "solve a Millennium problem this month." The
credible target is a grant-worthy, publication-grade discovery engine that can:

- prune mathematical and physical hypotheses with explicit kill criteria;
- expose robust finite-size phenomena before making large claims;
- generate benchmark-quality datasets that other researchers can reproduce;
- build the verification infrastructure needed if a real theorem route appears.

Three tracks share the same verification infrastructure:

- **GaugeGap** (Yang-Mills mass gap): AI-guided, verification-first
  finite-lattice gauge-theory experiments around mass gaps,
  confinement-adjacent observables, and string-breaking dynamics.
- **FlowGap** (Navier-Stokes): finite reduced-model benchmarks using viscous
  Burgers surrogates and pressure-Poisson subroutines, with hybrid
  quantum-classical comparison on tiny grids.
- **CurveRank** (Riemann hypothesis): spectral screening of truncated
  Hilbert-Polya candidate operators against known Riemann zeta zeros, with
  GUE spacing statistics and truncation stability analysis.

## Glasswing lesson

Anthropic's Project Glasswing is an operational model, not a science-discovery
model. Its useful lesson is that the scarce resource becomes verification
capacity, not candidate generation.

The science analogue is:

```text
generate hypothesis -> compute exact baseline -> run simulator -> run noisy emulator/QPU -> reproduce -> publish artifact
```

For science, "better than Glasswing" means more open, reproducible, benchmarked,
and grant-aligned, not simply larger.

## Verification ladder

1. exact classical baseline;
2. independent implementation check;
3. noiseless simulator;
4. noisy emulator;
5. hardware or analogue run where available;
6. finite-size, truncation, ansatz, and backend stability checks;
7. public dataset with negative results retained.

## Quantum boundary

The project currently reaches Qiskit quantum simulation, not real QPU execution.
Real hardware begins only when a validated circuit is submitted to a provider
runtime and the ledger records provider job id, backend, shots, and calibration
context. See `docs/quantum-boundary.md`.

**NEW:** Provider adapters and hardware-ready workflows are now implemented.
See `docs/quantum-mvp-plan.md` for the complete quantum MVP implementation plan
covering Quantinuum H2/Helios, IBM Runtime, AWS Braket/QuEra, and IonQ platforms.

## First ten experiments

1. Z2 minimal finite chain, gap vs coupling, exact diagonalization.
2. Same Hamiltonian with an independent matrix-construction path.
3. Gap stability under lattice size 4, 6, 8, 10 where feasible.
4. Correlator extraction on the same ground states.
5. String/domain-wall initial state, short-time exact dynamics.
6. Noiseless circuit simulation of the smallest Hamiltonian.
7. Noisy simulator run with shot-count sweep.
8. AI-proposed ansatz compared against simple baseline ansatz.
9. Negative control Hamiltonian where expected gap behavior is known.
10. Dataset export plus one-command reproduction script.

## Claim boundary

Acceptable first results are finite-system results, not Clay-prize claims.

### GaugeGap

- gap estimates: `Delta(L, g, truncation) = E1 - E0`;
- stable trends across lattice size or truncation;
- Wilson-loop or Creutz-ratio surrogates;
- electric-flux and two-point correlators;
- string-breaking or domain-wall dynamics;
- entanglement/Renyi proxies.

### FlowGap

- kinetic energy decay under viscous dissipation;
- pressure-Poisson residuals, classical vs quantum;
- divergence reduction after projection;
- grid convergence and noise sensitivity.

### CurveRank

- spectral mismatch trends vs truncation;
- GUE spacing statistics (mean ratio, stability);
- truncation drift and eigenvalue stability;
- ranked candidate operator families.

### Avoid across all tracks

- "we will solve [Millennium problem]";
- "AI discovered [fundamental result]";
- "quantum computer proves [theorem]";
- theorem-adjacent claims without precise finite-system definitions.

## Quantum MVP Implementation (2026-05-28)

### Provider Architecture

The repository now includes a unified provider adapter architecture supporting:

- **Quantinuum H2/Helios**: Trapped-ion systems with all-to-all connectivity
  - Primary target for GaugeGap (SU(2) lattice gauge theory)
  - Emulator support with realistic noise models
  - State-vector emulation up to 32 qubits

- **IBM Qiskit Runtime**: Superconducting systems with error mitigation
  - Primary target for FlowGap (Burgers/Poisson benchmarks)
  - Local Aer simulators with noise models
  - Runtime Sampler/Estimator with resilience controls

- **AWS Braket/QuEra Aquila**: Neutral-atom analog simulation
  - Secondary target for GaugeGap (string-breaking dynamics)
  - 256-qubit programmable array
  - Local AHS simulator for protocol validation

- **IonQ Forte/Aria**: Trapped-ion systems with built-in debiasing
  - Secondary target for CurveRank (QPE experiments)
  - All-to-all connectivity up to 36 qubits
  - Automatic debiasing for jobs with ≥500 shots

### Hardware-Ready Workflow

The standard emulator-to-hardware workflow is now implemented:

1. **Classical baseline**: Exact diagonalization or PDE solver
2. **Noiseless emulator**: Ideal quantum simulation
3. **Noisy emulator**: Hardware-calibrated noise model
4. **Validation**: Compare emulator vs classical within tolerance
5. **Readiness checks**: Credentials, calibration, circuit constraints
6. **Hardware submission**: Submit to QPU with full metadata capture
7. **Ledger recording**: Record job ID, backend, calibration context

See `src/gaugegap/workflows/emulator_to_hardware.py` for implementation.

### Priority Order

1. **GaugeGap** (4-8 weeks): Finite-lattice gap extraction on Quantinuum H2
2. **FlowGap** (2-6 weeks): Pressure-Poisson hybrid benchmark on IBM Runtime
3. **CurveRank** (2-6 weeks): AI-ranked spectral search with QPE validation

### Next Steps

- Week 1-2: Implement Quantinuum H2 emulator integration for Z2 plaquette
- Week 3-4: Run GaugeGap emulator validation and hardware submission
- Week 5-6: Add IBM Runtime integration for FlowGap Poisson benchmark
- Week 7-8: Implement QuEra Aquila AHS protocol for string-breaking

See `docs/quantum-mvp-plan.md` for complete implementation details.
