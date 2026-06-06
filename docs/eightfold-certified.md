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

**(C) Certified relations battery (PDG masses with uncertainties).** Every
standard SU(3)-flavor mass relation, evaluated in interval arithmetic so each
residual is a certified enclosure propagated from the input mass uncertainties:

| relation | certified residual | rel. | encloses 0? |
|----------|--------------------|------|-------------|
| baryon octet GMO `2(N+Ξ)−3Λ−Σ` | `[−25.96, −25.62]` MeV | 0.57% | no |
| decuplet spacing `(Ξ*−Σ*)−(Σ*−Δ)` | `[−7.00, −0.20]` MeV | 2.4% | no |
| decuplet spacing `(Ω−Ξ*)−(Ξ*−Σ*)` | `[−9.54, −5.36]` MeV | 4.9% | no |
| pseudoscalar GMO `4K²−3η²−π²` (quadratic) | `≈ [5.48, 5.50]×10⁴` MeV² | 5.6% | no |
| Coleman–Glashow `(n−p)+(Ξ⁻−Ξ⁰)−(Σ⁻−Σ⁺)` | `[−0.31, 0.43]` MeV | 0.8% | **yes** |

The residuals quantify, with certified bounds, exactly how well each symmetry
relation holds: the octet GMO breaking is `≈ −26` MeV (0.57%), the pseudoscalar
GMO carries the well-known `≈ 5.6%` shift from η–η′ mixing, and the
electromagnetic **Coleman–Glashow** relation is certified *consistent with zero*.

**(D) Derived certified quantities.**

- **Constituent quark masses** (decuplet additive model, `Δ=qqq`, `Ω=sss`):
  `m_q ≈ [410.3, 411.0]`, `m_s ≈ [557.4, 557.6]` MeV, with strange–light
  splitting `m_s − m_q ≈ [146.4, 147.2]` MeV — the scale that sets the decuplet
  equal spacing.
- **The Ω⁻ prediction.** Equal spacing gives `M_Ω = 2·M_Ξ* − M_Σ*`; the certified
  prediction `≈ [1678.1, 1681.7]` MeV vs. measured `1672.45 ± 0.29` (~0.45%) —
  the historic confirmation of the Eightfold Way, as a certified interval.
- **η–η′ mixing.** From a 2×2 mass-squared system (octet `m₈²` fixed by GMO), the
  off-diagonal `t²` is certified strictly positive — a certified consistency
  check that a real octet–singlet mixing angle exists.

**(E) Weight diagrams.** The runner emits the Eightfold-Way `(I₃, Y)` weight
diagrams (the octet hexagon and the decuplet triangle) as SVG to `figures/`.

## Files

| component | path |
|-----------|------|
| Model + full certified battery | `src/gaugegap/eightfold.py` |
| Report runner + figures | `scripts/run_eightfold.py` |
| Tests | `tests/test_eightfold.py` |
| Weight diagrams | `figures/octet_weight_diagram.svg`, `figures/decuplet_weight_diagram.svg` |

## Relation to the rest of the repo

This reuses `gaugegap.rigorous.interval_arithmetic` (the directed-rounding
`Interval` type and `verified_hermitian_eigenvalues`) — the same certified
eigenvalue machinery used by the CurveRank spectral-screening track. It is a
separate physics application of that infrastructure and shares no claims with
the Riemann/Hilbert–Pólya work.
