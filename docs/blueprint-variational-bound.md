# Blueprint: the variational bound the bracket certificates assume

Formalisation target for the `gaugegap-variational` track of `formal/lean`.
Unlike the other tracks, this one is not a second-prover check of an existing
Coq file. It removes an assumption from certificates this repository already
emits.

## The finding

`results/certified-bracket/bracket_E0.lean` concludes a two-sided eigenvalue
bracket. It rests on three `axiom` declarations, and they are not the same kind
of thing:

| Assumption | Kind |
|---|---|
| `certified_lower : E ≥ -12.787631637507566` | numerical — an interval-arithmetic enclosure produced by directed rounding outside any prover |
| `variational_upper : E ≤ -12.787631637495053` | **mathematical** — its docstring says "by Courant-Fischer" |
| `E : ℝ` | the eigenvalue itself, abstract |

The second one is a theorem being assumed. Courant-Fischer is not a measurement;
it is an inequality, and an elementary one in finite dimension. This track proves
it, so that certificate pattern can rest on numerics alone.

The same shape appears in `results/temple-bracket/`, and the pattern generalises
to the other emitted certificates: `scripts/build_formal_registry.py` now reports
`trust_input_count` and `assumption_free_count` alongside `hole_free_count`,
which is how a file resting entirely on axioms stops being counted as
established.

## Claim boundary

Finite-dimensional real linear algebra for a **declared eigenbasis expansion**.
The state is given by its coefficients `c` in an orthonormal eigenbasis with
eigenvalues `lam`, so `⟪ψ, Hψ⟫ = ∑ lam i * c i ^ 2` and `‖ψ‖² = ∑ c i ^ 2`.

That expansion — that a Hermitian operator on a finite-dimensional space *has*
such a basis — is the spectral theorem, and it is a **standing hypothesis here,
not something this track establishes**. Claim boundary, stated exactly: the
inequality half of Courant-Fischer is machine-checked; the spectral
decomposition it is applied to is assumed. Nothing here concerns unbounded operators, constructs a spectrum, or
bears on the Yang-Mills mass gap.

## Nodes

**D01, D02 — the scaled bounds.** If `lo ≤ lam i` for every `i`, then
`lo * ∑ c i ^ 2 ≤ ∑ lam i * c i ^ 2`, and dually for an upper bound. Both are one
application of `Finset.sum_le_sum` to the pointwise inequality
`lo * c i ^ 2 ≤ lam i * c i ^ 2`, which holds because `c i ^ 2 ≥ 0`. The squared
norm is carried explicitly because the bound is not scale-free: doubling the
state quadruples both sides.

**D03 — the normalised bracket.** With `∑ c i ^ 2 = 1` the scaling disappears and
the Rayleigh quotient lies between any bounds on the spectrum.

**D04 — the variational principle.** No normalised trial state has a Rayleigh
quotient below the ground energy. This is precisely `variational_upper`, and it
is derived from `D01` rather than assumed.

**D05 — the certified bracket.** Shaped like `bracket_E0.lean` so the two can be
compared line by line. The interval-arithmetic enclosure and the evaluated trial
state remain hypotheses, because they really are numerical inputs. The step
between them is `D04`.

## Node table

| Node | Statement | Depends on |
|---|---|---|
| D01 | `Stmt_D01_RayleighLowerBound` | — |
| D02 | `Stmt_D02_RayleighUpperBound` | — |
| D03 | `Stmt_D03_NormalisedBracket` | D01, D02 |
| D04 | `Stmt_D04_VariationalPrinciple` | D01 |
| D05 | `Stmt_D05_CertifiedBracket` | D04 |

## The mirror

`src/gaugegap/variational_theorem.py` restates all five nodes over exactly
normalised rational coefficient vectors. `tests/test_variational_theorem.py`
checks the two things a mirror cannot: that the bound is not an equality in
disguise (11 sampled states sit strictly above the ground energy) and that a
state concentrated on the ground mode attains it exactly.

## What this does not do

It does not make `bracket_E0.lean` axiom-free. That file is a standalone emitted
artifact and cannot import this library, so its own text still declares three
axioms. What has changed is that one of the three is now known to be a theorem
with a machine-checked proof in this repository, and the registry reports the
remaining assumptions instead of counting the file as established.
