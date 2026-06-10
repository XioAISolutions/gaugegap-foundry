# GaugeGap Foundry: Verification-First Infrastructure for Finite-System Benchmarks in Gauge Theory and Spectral Screening

**Authors:** Xio AI Solutions (corresponding author TBD)
**Affiliation:** GaugeGap Foundry
**Preprint draft — v0.1. Not peer reviewed.**

> **Scope and claim boundary.** This is an *infrastructure* paper. It describes a
> software platform for **finite-system** numerical benchmarks and certified
> finite-dimensional bounds. It does **not** resolve the Yang–Mills mass-gap
> problem, the Navier–Stokes problem, or the Riemann Hypothesis; it asserts no
> continuum or first-principles result, and makes no Millennium Prize solution
> claim. Where components are prototypes we say so; where they are exact we say
> so; every quantitative claim is a certified finite-system bound or a
> reproducible numerical measurement, and all require independent review.

## Abstract

Computational attacks on hard problems in mathematical physics suffer a recurring
credibility failure: ambitious framing outruns what the code actually
establishes, and "results" are floating-point estimates dressed as guarantees.
GaugeGap Foundry is a platform built to make the opposite trade. Its organizing
principle is *verification-first*: every headline number is either (i) a
machine-checked certified bound computed in rigorous interval arithmetic, (ii) an
exactly-solvable finite system pinned to a known closed-form answer, or (iii) a
reproducible numerical measurement with an explicit, separated error budget — and
all three are fenced by an automatically-audited claim boundary that forbids
continuum and prize-level language. We describe the architecture (finite gauge
benchmarks for Z₂/U(1)/SU(2)/SU(3); a certified spectral-screening track for
Hilbert–Pólya candidate operators; a certified SU(3)-flavor relations suite; and
a defensible single-link SU(3) electric truncation), the verification methods
(directed-rounding interval eigenvalue enclosures, independent cross-checks
against a second arbitrary-precision library, known-answer regression tests,
deterministic reproducibility proofpacks with content digests, and error-budget
separation), and the review apparatus (a claim-boundary audit run in CI and a
self-contained reviewer packet). The contribution is methodological: a template
for honest, reproducible, independently-checkable computational mathematics.

## 1. Introduction

The history of computational approaches to famous problems is littered with
overclaims. The failure mode is not usually fraud but *category error*: a
finite-dimensional numerical experiment is reported with language appropriate to
an infinite-dimensional theorem, and a floating-point number with no error
analysis is presented as a certificate. The remedy is not to be less ambitious
about *infrastructure* — it is to be ruthlessly precise about what each artifact
establishes.

GaugeGap Foundry adopts three rules:

1. **If a quantity is finite, numerical, or a prototype, the code and the docs
   say so.** A continuous-time claim is never implied by a finite-truncation
   computation.
2. **Every headline number is verifiable without trusting the authors** — by
   rerunning a deterministic artifact, by an independent second implementation,
   or by comparison to a closed-form answer.
3. **The claim boundary is enforced, not merely stated.** A scanner runs in
   continuous integration and fails the build on prize/continuum language.

This paper documents how those rules are realized in code.

## 2. Architecture

The platform is organized into tracks, each a finite system with an explicit
boundary.

- **Finite gauge benchmarks.** Small Z₂ plaquette, compact U(1), SU(2), and SU(3)
  Hamiltonians, diagonalized exactly at tiny sizes. These are toy lattice models,
  not continuum field theories.
- **CurveRank — certified spectral screening.** Truncations of candidate
  Hilbert–Pólya operators (Berry–Keating `xp`, a Dirac–Rindler operator, a
  quantum-graph Laplacian) screened against the low-lying Riemann zeros, with the
  separation reported as a *certified finite-truncation bound* rather than a
  floating-point estimate.
- **Eightfold Way — certified SU(3)-flavor relations.** The Gell-Mann–Okubo mass
  relations and their relatives realized as an effective mass operator and a
  battery of certified residual intervals from particle-data inputs.
- **SU(3) electric link.** A single-link SU(3) electric (Kogut–Susskind
  strong-coupling) Hamiltonian, exactly diagonalized in the truncated irrep
  basis — a small but genuinely SU(3) system, distinct from the explicitly
  labeled 2+1D prototype scaffold.

## 3. Verification methods

### 3.1 Rigorous interval eigenvalue enclosures
The core numerical primitive is a verified Hermitian eigensolver. For a real
symmetric matrix `A`, an approximate eigenpair `(θ, x)` from a floating-point
solver yields, via the classical residual (Weyl / Bauer–Fike) bound, a certified
enclosure `[θ − ρ, θ + ρ]` with `ρ ≥ ‖Ax − θx‖ / ‖x‖` — and that residual is
evaluated entirely in interval arithmetic, so the enclosure does not depend on
the solver being accurate. The interval layer routes every elementary operation
through `mpmath.iv` directed (outward) rounding, so endpoints are certified
bounds rather than round-to-nearest estimates. Observed enclosure widths are
`~10⁻¹³`.

### 3.2 Independent second-source cross-check
Trust in the interval library itself is checked, not assumed: every certified
radius is recomputed with a completely independent rigorous backend (Arb, via
`python-flint`, at higher precision). The two libraries agree to `~35` decimal
digits, with the primary radius certified to lie at or above the independent
lower bound.

### 3.3 Known-answer regression tests
Each finite track is pinned to an *independently derived* exact answer, not to a
prior run of the code: the Z₂ single-plaquette closed-form spectrum
`±√(J² + (h·b)²)` (from the anticommuting `{P, B}=0` structure); the compact-U(1)
link algebra and electric-only gap `g²/2`; the SU(3) Gell-Mann identities
(`Tr(λₐλ_b)=2δ_ab`, Casimir `∑λₐ²=(16/3)I`, `f₁₂₃=1`); and the SU(3) link
electric gap `2g²/3`. These catch silent numerical regressions.

### 3.4 Error-budget separation
Uncertainty sources are kept apart rather than collapsed: statistical
(quadrature) versus bounded systematic/truncation (linear, worst-case)
contributions, with the dominant source made explicit. An interval *width* is
numerical error; the distance of an enclosure from a target is a
finite-truncation (systematic) bound — never conflated with a statistical
estimate.

### 3.5 Reproducibility and seeding
Stochastic routines draw from explicitly-seeded generators (never the global RNG
state), and the reproducibility proofpack is deterministic: it honors
`SOURCE_DATE_EPOCH`, and a content `reproducible_digest` over the benchmark
outputs is byte-identical across fresh builds of the same commit. A verifier
rebuilds twice and asserts the digest matches.

## 4. Results

The platform's certified outputs are reproducible from the repository. Selected
headline certified bounds and exact measurements:

- **CurveRank.** Certified finite-truncation spectral-mismatch bounds for the
  `xp`, Dirac–Rindler, and quantum-graph families, enclosures of width `~10⁻¹³`,
  independently corroborated by Arb. These are finite-`n` separations, with the
  truncation → ∞ behaviour recorded only as non-certified supporting evidence.
- **Eightfold Way.** A certified battery of SU(3)-flavor mass relations
  (baryon-octet GMO, decuplet equal spacing, pseudoscalar GMO, Coleman–Glashow,
  the Ω⁻ equal-spacing prediction, η–η′ and ω–φ mixing, SU(6) magnetic moments,
  isospin decay ratios, the Gell-Mann–Nishijima relation, SU(3) tensor
  decompositions, and a Cabibbo/CKM sector) — each a certified interval from
  data-with-uncertainties.
- **SU(3) electric link.** Exact spectrum with colour-singlet ground state,
  electric gap `2g²/3`, and degeneracies `dim(R)²`.

None of these is a statement about a continuum theory or a Millennium Prize
problem; each is a certified or exact finite-system quantity.

## 5. Review apparatus

A claim-boundary audit (a context-aware scanner for prize/continuum/overclaim
language) runs as a hard CI gate. A separate research-maturity audit reports
prototype/placeholder risk honestly without blocking. A one-command reviewer
packet assembles provenance, audit status, the certified-result trust chains, and
a reviewer checklist for an outside expert. The certified CurveRank result ships
with an explicit list of verification obligations (directed-rounding soundness,
disjointness of enclosures, trust in zero-finding) so a referee knows exactly
what to check.

## 6. Limitations

- Results are certified or exact only at the finite sizes tested; no continuum or
  thermodynamic limit is asserted.
- The SU(3) 2+1D lattice model is a prototype scaffold, not a completed
  implementation; the defensible SU(3) result is a single link, electric sector
  only.
- Several advanced quantum-algorithm modules are research/utility code; only the
  pieces with reference values are validated, and the rest are flagged as such.
- Independent expert review is a prerequisite before any external scientific
  claim; this paper documents infrastructure, not a result in mathematical
  physics.

## 7. Conclusion

GaugeGap Foundry demonstrates that ambition and honesty are compatible in
computational mathematics if verification is built in from the start: certified
interval bounds, independent cross-checks, known-answer tests, deterministic
proofpacks, separated error budgets, and an enforced claim boundary. The value is
a reusable template for reproducible, independently-checkable finite-system
science — the foundation on which any legitimate next step (independent review,
larger truncations, genuinely new operator content) would have to be built.

## Reproducibility

```bash
pip install -e ".[dev]"
make audit              # claim-boundary (strict gate) + maturity report
make proofpack          # deterministic finite-benchmark proofpack
make proofpack-verify   # asserts two fresh builds share a reproducible_digest
make reviewer-packet    # self-contained packet for outside experts
pytest -q               # full known-answer + certified test suite
```

## References (to be completed)

1. M. V. Berry and J. P. Keating, *H = xp and the Riemann zeros* (1999).
2. S. Gell-Mann; S. Okubo — the Eightfold Way and SU(3)-flavor mass relations (1961–62).
3. J. Kogut and L. Susskind, *Hamiltonian formulation of Wilson's lattice gauge theories* (1975).
4. S. M. Rump, *Verification methods: rigorous results using floating-point arithmetic*, Acta Numerica (2010).
5. The `mpmath` library (arbitrary-precision and interval arithmetic) and Arb / `python-flint`.
6. Standard references on the residual / Weyl eigenvalue perturbation bound for symmetric matrices.
