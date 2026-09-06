# Blueprint: the Hadamard Gram identity in Lean

Formalisation target for the `hadamard-gram` track of `formal/lean`. It is a
second-prover check of `formal/hadamard/gram_identity.v`: the same finite
integer arithmetic, restated in Lean 4 so two independent kernels accept it.

## Claim boundary

Statements about a single pair of finite ±1 vectors of equal length. Not the
Hadamard conjecture, and not the theorem that an order `n >= 3` admitting a
Hadamard matrix satisfies `4 | n`. The even-length condition here is the
elementary half of that necessary condition, and nothing more. This is exactly
the boundary the Coq source declares, restated rather than relaxed.

## Why this identity matters

The Hadamard Forge verifier never materialises a ±1 matrix. Each row is an
arbitrary-precision bitmask and each inner product is computed as

```text
<u, v> = n - 2 * popcount(u XOR v)
```

That is the code path CI actually runs. The identity below is what licenses
reading its output as an inner product at all, so it is the right thing to have
machine-checked twice.

## Setup

`Sign` is the two-element ±1 alphabet, `Sign.value` the integer it denotes, and
`disagree a b` one popcount bit. Two recursive functions over `List Sign`:

```text
inner      (a :: u) (b :: v) = a.value * b.value + inner u v
mismatches (a :: u) (b :: v) = disagree a b + mismatches u v
```

with both returning `0` when either list is empty — the Coq definition's
behaviour, kept rather than tidied.

## Correspondence with the Coq certificate

| Coq result | Kind | Lean node |
|---|---|---|
| `disagree_bounds` | Lemma | `C01` |
| `product_from_disagree` | Lemma | `C02` |
| `mismatches_nonnegative` | Lemma | `C03` |
| `inner_eq_popcount_form` | Theorem | `C04` |
| `mismatches_self` | Lemma | `C05` |
| `inner_self_eq_length` | Theorem | `C06` |
| `orthogonal_length_even` | Theorem | `C07` |
| `orthogonal_length_is_even` | Corollary | `C08` |

One node per named Coq result, lemmas included — unlike the InfoGap track,
nothing here is a restatement of anything else, so nothing collapses.

`tests/test_prover_correspondence.py` enforces this repo-wide: every
`Lemma`, `Theorem`, `Corollary` or `Proposition` in any `formal/**/*.v` must be
named by some Lean node's description, so a Coq result added without a Lean
counterpart fails the suite. That test also guards its own regex, so it cannot
pass by parsing nothing.

## Nodes

**C01, C02 — the alphabet.** `disagree` lands in `{0, 1}`, and
`a.value * b.value = 1 - 2 * disagree a b`. Four cases each; `C02` is the whole
arithmetic content of the popcount trick, at one position.

**C03 — non-negativity.** Induction on the first list, using `C01` at the head.

**C04 — the core identity.** Induction on the first list. At the head the sum of
products contributes `1 - 2 * disagree a b` by `C02`; at the tail the induction
hypothesis contributes `length - 2 * mismatches`. The length cast steps by one,
and the two combine linearly.

**C05, C06 — the diagonal gate.** A vector never disagrees with itself, so
`inner u u = length u`: every diagonal entry of `H Hᵀ` is the order.

**C07, C08 — the off-diagonal gate.** If equal-length rows are orthogonal then
`length u = 2 * mismatches u v`, so the length is even. `C08` is `C07` packaged
as `Even`, exactly as the Coq corollary packages its theorem.

## Node table

| Node | Statement | Depends on |
|---|---|---|
| C01 | `Stmt_C01_DisagreeBounds` | — |
| C02 | `Stmt_C02_ProductFromDisagree` | — |
| C03 | `Stmt_C03_MismatchesNonneg` | C01 |
| C04 | `Stmt_C04_InnerEqPopcountForm` | C02 |
| C05 | `Stmt_C05_MismatchesSelf` | — |
| C06 | `Stmt_C06_InnerSelfEqLength` | C04, C05 |
| C07 | `Stmt_C07_OrthogonalLengthTwicePopcount` | C04 |
| C08 | `Stmt_C08_OrthogonalLengthIsEven` | C07 |

`scripts/run_lean_forge.py` checks that column against the proof terms each
proof actually references.

## The mirror

`src/gaugegap/gram_theorem.py` restates all eight nodes over Python integers and
checks them **exhaustively** over every pair of equal-length ±1 vectors up to
length 6 — 5461 pairs, of which 1385 are orthogonal, so `C07` and `C08` are not
vacuous. That is a complete check on a finite slice of the domain, not a
substitute for the universally quantified Lean statement; `lake build` supplies
that.

`tests/test_gram_theorem.py` adds the checks a mirror alone cannot make: that no
odd-length pair is ever orthogonal, and that the two sides of `C04` are not the
same expression written twice.

## Reproduce

```bash
foundry run lean-forge          # structure + mirror, plus lake build if available
foundry run compile-coq         # the Coq side, via coqc
foundry run lean-dag-figure     # figures/anomaly-forge/lean-dag.svg
```

CI runs both provers: `compile-coq` and `compile-lean` in
`.github/workflows/verify-proofs.yml`.
