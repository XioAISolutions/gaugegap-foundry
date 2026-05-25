# GaugeGap Foundry Roadmap

Date: 2026-05-24

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
