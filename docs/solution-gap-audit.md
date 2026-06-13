# Solution Gap Audit

**Purpose:** Convert GaugeGap Foundry from an ambitious finite-system benchmark repo into a credible research platform that can move closer to real mass-gap-adjacent discovery without overclaiming.

This document is not a victory lap. It is the hard map of what is missing before the project can be treated as publishable science, let alone a route toward a Millennium Prize-level result.

---

## Current Verdict

| Target | Current readiness | Honest status |
|---|---:|---|
| Reproducible finite-system benchmark platform | 60-70% | Real structure exists, but needs stronger independent validation and clean one-command reproduction. |
| Publishable methods/tool preprint | 40-55% | Possible after credibility cleanup, external review, stronger baselines, and reproducibility proofpack hardening. |
| Serious Yang-Mills-adjacent research program | 15-25% | Directionally useful, but still finite, small, mostly numerical, and not yet mathematically rigorous. |
| Continuum Yang-Mills mass-gap solution | 1-5% | Not close. Requires new mathematical physics, continuum limits, rigorous bounds, and expert review. |

---

## What Is Actually Strong

1. **Claim boundary discipline**
   - The repo repeatedly states finite-system scope.
   - It avoids claiming a Millennium Prize solution.
   - This protects credibility and should stay mandatory.

2. **Benchmark ladder**
   - Z2, U(1), SU(2), SU(3-labeled work, FlowGap, and CurveRank form a useful verification foundry layout.
   - This is the correct architecture for an AI-for-science infrastructure project.

3. **Reproducibility direction**
   - Scripts write JSON/JSONL/CSV/Markdown/SVG outputs.
   - Proofpack generation exists.
   - Claim-boundary audit exists.

4. **Negative-result capability**
   - CurveRank certified screening is currently more credible as a proof-adjacent artifact than the mass-gap claims.
   - Ruling out candidates cleanly is scientifically valuable.

---

## Highest-Risk Gaps

### 1. SU(3) is not yet a real SU(3) Yang-Mills engine

The current SU(3) lane contains useful scaffolding, but the magnetic plaquette term, Wilson loops, string tension, Polyakov loop, and Gauss-law checks are still placeholders/prototypes.

**Rule:** Until this is fixed, docs must say **SU(3 prototype scaffold**, not **SU(3 implemented**.

**Required before stronger claims:**
- Kogut-Susskind Hamiltonian implementation for SU(3) or an explicitly documented toy truncation.
- Real plaquette operator construction.
- Gauss-law operator and physical-subspace projection.
- Wilson loop observable.
- String tension estimator.
- Comparison to at least one known lattice gauge benchmark.

### 2. No rigorous continuum bridge

Finite lattice data does not imply a continuum mass gap. A real bridge requires:
- thermodynamic limit controls;
- lattice spacing extrapolation;
- renormalization group treatment;
- lower-bound proof strategy;
- proof assistant or computer-assisted proof route for finite claims.

### 3. Error budget still too loose

The current systematic error analysis is directionally useful, but not strong enough for research-grade claims.

Required:
- separate finite-size, truncation, discretization, optimizer, sampling, and backend noise errors;
- repeatability across seeds;
- confidence intervals from repeated runs;
- regression tests proving that known baselines remain stable.

### 4. Reproduction should be one-command

A serious reviewer should be able to run:

```bash
make proofpack
```

and get:
- environment lockfile;
- exact commands;
- output hashes;
- claim boundary manifest;
- generated figures;
- machine-readable benchmark summary;
- failure report if anything is placeholder or unverified.

### 5. External expert review is mandatory

Before any strong public positioning, get review from:
- lattice gauge theorist;
- mathematical physicist;
- numerical methods/HPC person;
- quantum simulation person.

---

## Readiness Tiers

### Tier 0 — Current state

Finite-system benchmark scaffold with some real components and some prototype components.

**Allowed language:**
- finite-system benchmark;
- toy gauge model;
- verification infrastructure;
- mass-gap-adjacent experiments;
- negative-result screening.

**Forbidden language:**
- solved Yang-Mills;
- proof of mass gap;
- continuum result;
- QCD solved;
- Millennium Prize solution.

### Tier 1 — Credible finite benchmark platform

Definition of done:
- all scripts in README run on clean install;
- CI green on Python 3.10 and 3.12;
- placeholder audit report generated;
- SU(3) labeled honestly as prototype unless fixed;
- proofpack includes hashes and command logs;
- benchmarks include known sanity checks.

### Tier 2 — Publishable tool/preprint

Definition of done:
- one-command reproduction;
- proper baseline comparison;
- error bars and seed stability;
- public dataset/results bundle;
- external reviewer comments addressed;
- paper frames the repo as infrastructure, not solution.

### Tier 3 — Serious solution-candidate program

Definition of done:
- rigorous finite-volume bounds;
- proof-assistant checked lemmas for finite claims;
- continuum-limit strategy;
- collaboration with domain experts;
- publication-quality mathematical argument.

---

## Immediate Agent Priorities

1. **Truth hardening**
   - Detect placeholders and prevent them from being treated as completed science.
   - Add maturity reports to proofpack.

2. **SU(3) repair**
   - Either implement a mathematically defensible toy SU(3) truncation or rename the lane as prototype.

3. **One-command proofpack**
   - Add `make proofpack` and `make smoke`.

4. **Known-answer tests**
   - Add analytic/small-system reference checks for Z2 and U(1).

5. **Reviewer package**
   - Generate a clean `reviewer_packet/` with methods, commands, results, claim boundaries, and open limitations.

---

## Best Public Positioning

Use this line:

> GaugeGap Foundry is a verification-first finite gauge theory benchmark platform for mass-gap-adjacent experiments, negative-result screening, and quantum/hardware validation workflows.

Do not use this line yet:

> GaugeGap Foundry solves Yang-Mills.
