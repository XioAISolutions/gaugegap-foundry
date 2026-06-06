# Certified Eightfold-Way / Gell-Mann–Okubo Benchmark

A finite, machine-checked realization of the **Eightfold Way** — the SU(3)-flavor
classification of hadrons — and its **Gell-Mann–Okubo (GMO)** mass relations,
built on the same rigorous interval-arithmetic machinery as the rest of this
repository.

> **Claim boundary.** This is a finite-dimensional *effective* SU(3)-flavor
> **mass-operator** model (the Gell-Mann–Okubo phenomenology) made rigorous with
> interval arithmetic. It is **not** a dynamical lattice-QCD computation: it does
> not derive hadron masses from a gauge+matter path integral, and it makes no
> continuum or first-principles claim. The certified statements concern the
> finite model operator and linear relations among input masses.

## The idea

The Eightfold Way organizes baryons into an SU(3)-flavor **octet** and
**decuplet**. Its mathematical content is a mass operator on a multiplet that is
a flavor singlet plus a term transforming like the hypercharge (`T_8`) component
of an octet:

```
M = a·1 + b·Y + c·(I(I+1) − Y²/4)
```

where `Y` is hypercharge and `I` isospin. We build this operator as a certified
real-symmetric **interval matrix** and run it through
`verified_hermitian_eigenvalues`, so the multiplet structure and the mass
relations come out as certified finite-system bounds.

## What is certified

Run it:

```bash
python3 scripts/run_eightfold.py
pytest tests/test_eightfold.py -q
```

**(A) Multiplet structure.** The certified eigenvalue enclosures show the
symmetry breaking lifting the degeneracy:

| operator | certified distinct levels | cluster sizes |
|----------|---------------------------|---------------|
| SU(3) limit (`b=c=0`) | 1 | `[8]` (full octet degeneracy) |
| octet breaking | 4 | `[2, 1, 3, 2]` = N, Λ, Σ, Ξ |

"Certified distinct" means the enclosures are pairwise disjoint, so the
eigenvalues are provably different — a machine-checked statement that the
breaking term splits the octet into exactly the four isospin multiplets
N(2) + Λ(1) + Σ(3) + Ξ(2) = 8.

**(B) The GMO relation is certified exact for the model.** Evaluated in interval
arithmetic on the operator's own levels,

```
2(M_N + M_Ξ) − 3·M_Λ − M_Σ  =  [0, 0]   (certified)
```

for every choice of `a, b, c` — because the breaking term transforms as an
octet.

**(C) Certified empirical checks (PDG masses with uncertainties).**

- **GMO residual.** With the measured isospin-averaged octet masses, the
  certified residual is `≈ [−25.96, −25.62]` MeV — about `0.56%` of the mass
  scale. This is the well-known small GMO discrepancy (the breaking is not a
  pure octet), now reported as a certified interval propagated from the input
  uncertainties.
- **The Ω⁻ prediction.** The decuplet equal-spacing rule predicts
  `M_Ω = 2·M_Ξ* − M_Σ*`. From the measured `Σ*` and `Ξ*`, the certified
  prediction is `≈ [1678.1, 1681.7]` MeV, vs. the measured `1672.45 ± 0.29` MeV
  — agreement to `≈ 0.45%`. This is the historic prediction that confirmed the
  Eightfold Way, here as a certified interval.

## Files

| component | path |
|-----------|------|
| Model + certified checks | `src/gaugegap/eightfold.py` |
| Report runner | `scripts/run_eightfold.py` |
| Tests | `tests/test_eightfold.py` |

## Relation to the rest of the repo

This reuses `gaugegap.rigorous.interval_arithmetic` (the directed-rounding
`Interval` type and `verified_hermitian_eigenvalues`) — the same certified
eigenvalue machinery used by the CurveRank spectral-screening track. It is a
separate physics application of that infrastructure and shares no claims with
the Riemann/Hilbert–Pólya work.
