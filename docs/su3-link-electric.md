# Single-link SU(3) electric Hamiltonian (defensible toy truncation)

A finite, **exactly solvable** SU(3) gauge truncation (issue #12, A3) with
genuine SU(3) representation-theory structure — the defensible counterpart to the
`gaugegap_su3_pure` prototype scaffold.

> **Claim boundary.** A single-link SU(3) **electric** (Kogut–Susskind
> strong-coupling) Hamiltonian, exactly diagonalized in a truncated irrep basis.
> This is genuine finite SU(3) gauge structure, but it is **one link** with **no
> magnetic/plaquette dynamics**, no continuum limit, and **no Yang–Mills
> mass-gap claim**. It is a finite-system benchmark.

## The model

The electric term of the Kogut–Susskind lattice gauge Hamiltonian on one link is

```
H_E = (g²/2) · Σ_a (E^a)²  =  (g²/2) · C₂(R)
```

where the link Hilbert space is spanned by SU(3) irreps `R = (p, q)`. The
colour-electric energy of a link carrying irrep `R` is its quadratic Casimir
`C₂(R)`; each irrep contributes `dim(R)²` degenerate basis states (left and right
colour indices). The basis is truncated to irreps with `p, q ≤ cutoff` (the
standard strong-coupling truncation).

Everything is exact — these are textbook SU(3) identities:

```
dim(p, q) = (p+1)(q+1)(p+q+2)/2
C₂(p, q)  = (p² + q² + p q)/3 + (p + q)
```

| irrep | (p, q) | dim | C₂ | electric energy (g=1) |
|-------|--------|-----|----|------------------------|
| singlet `1` | (0,0) | 1 | 0 | 0 |
| fundamental `3` / `3̄` | (1,0)/(0,1) | 3 | 4/3 | 2/3 |
| adjoint `8` | (1,1) | 8 | 3 | 3/2 |
| sextet `6` / `6̄` | (2,0)/(0,2) | 6 | 10/3 | 5/3 |
| decuplet `10` | (3,0) | 10 | 6 | 3 |

## What is exact (known-answer tested)

- **Ground state** is the colour singlet, `E = 0`, non-degenerate.
- **Electric mass gap** to the fundamental is `(g²/2)·(4/3) = 2g²/3` — closed form.
- **Level degeneracies** are `dim(R)²` (e.g. the fundamental level is `3² + 3̄² =
  18`-fold; the adjoint level is `8² = 64`-fold).
- **Gap scales as `g²`** with the coupling.
- Hilbert dimension is `Σ dim(R)²` over the truncated irreps.

All of these are checked in `tests/test_su3_link.py`.

## Run it

```bash
python3 scripts/run_su3_link.py --g-electric 1.0 --cutoff 2
pytest tests/test_su3_link.py -q
```

## Relationship to the prototype scaffold

`gaugegap_su3_pure` remains an honestly-labeled `prototype_scaffold` (the full
2+1D lattice with plaquette dynamics is not implemented). This module is the
*defensible* path A3 asks for: a smaller system — a single link, electric sector
only — but **genuinely and exactly SU(3)**. Adding the magnetic/plaquette term
(which needs SU(3) Clebsch–Gordan / 6j machinery) is the natural next step and is
deliberately out of scope here.
