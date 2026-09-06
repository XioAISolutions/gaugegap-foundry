# Blueprint: the finite no-hiding identities in Lean

Formalisation target for the `infogap-no-hiding` track of `formal/lean`. It is a
second-prover check of `formal/infogap/no_hiding_finite.v`: the same finite
algebra, stated and proved again in Lean 4 so two independent kernels accept it.

## Claim boundary

Exact algebraic probability identities for the implemented three-qubit circuit
`|psi>_S |00>_AB -> |Phi+>_SA |psi>_B`. Not a formalisation of the general
no-hiding theorem: no Hilbert spaces, no Stinespring dilation, no Schmidt
decomposition, no statement about arbitrary channels. This is exactly the
boundary the Coq source already declares, restated rather than relaxed.

## Setup

`ar`, `ai`, `br`, `bi` are the real and imaginary parts of the input amplitudes
`alpha` and `beta`. `h` is the Hadamard amplitude. Two hypotheses, both taken
from the Coq source:

```text
inputNorm  ar ai br bi = ar^2 + ai^2 + br^2 + bi^2 = 1
h ^ 2 = 1 / 2
```

`h` appears in every statement only inside a square, which is what lets the
Python mirror carry `h ** 2 = 1/2` exactly as a `Fraction` and never need the
irrational `h`. The Lean definitions keep the Coq's own shape — sums of
`(h * x) ^ 2` rather than a pre-factored `h ^ 2` — so the correspondence is a
transliteration, not a paraphrase.

## Correspondence with the Coq certificate

| Coq theorem | Lean node |
|---|---|
| `input_probability_normalized` | `B01` |
| `system_zero_probability` | `B02` |
| `system_one_probability` | `B02` (see below) |
| `recovery_zero_probability` | `B04` |
| `recovery_one_probability` | `B05` |
| `recovered_probability_normalized` | `B06` |
| — | `B03`, `B07` |

`system_one_probability` in the Coq source is not a second fact: it states the
same equation as `system_zero_probability` and is discharged by `apply` on it.
Porting it as a separate Lean node would inflate the count without adding
content, so it maps to `B02`, and `B03` states what the pair was reaching for —
that the two branches exhaust the probability.

`tests/test_no_hiding_theorem.py` fails if a `Theorem` appears in the Coq source
with no Lean node naming it, so this table cannot silently rot.

## Nodes

**B01 — input normalisation.** `|alpha|^2 + |beta|^2 = 1`, a restatement of the
hypothesis in terms of the two pair probabilities.

**B02 — branch weight.** A measured system branch has weight exactly `1/2`:
`h^2 * (ar^2 + ai^2 + br^2 + bi^2) = h^2 * 1 = 1/2`.

**B03 — the branches exhaust.** `1/2 + 1/2 = 1`, derived from `B02` rather than
from the hypotheses again.

**B04, B05 — exact recovery.** `2 * h^2 * (ar^2 + ai^2) = ar^2 + ai^2`, and the
same for `beta`. The factor `2 * h^2 = 1` is what makes recovery lossless; it is
the only place `h ^ 2 = 1/2` does real work.

**B06 — recovered normalisation.** Chains `B04`, `B05` and `B01`, in the same
order the Coq proof does.

**B07 — the no-hiding content, not in the Coq source.** For *any two* normalised
inputs the branch weights coincide and equal `1/2`. So the measured system
statistics are blind to `alpha` and `beta` — nothing about the input survives
there — while `B04` and `B05` recover both probabilities exactly on `B`. Stating
only `B02` leaves this implicit; `B07` says it.

## Node table

| Node | Statement | Depends on |
|---|---|---|
| B01 | `Stmt_B01_InputNormalised` | — |
| B02 | `Stmt_B02_BranchWeightHalf` | — |
| B03 | `Stmt_B03_BranchesExhaust` | B02 |
| B04 | `Stmt_B04_RecoveryAlpha` | — |
| B05 | `Stmt_B05_RecoveryBeta` | — |
| B06 | `Stmt_B06_RecoveredNormalised` | B01, B04, B05 |
| B07 | `Stmt_B07_SystemCarriesNoInformation` | B02 |

`scripts/run_lean_forge.py` checks the dependency column against the proof terms
each proof actually references, so a declared edge the proof does not use, or a
use that is not declared, fails the gate.

## Reproduce

```bash
foundry run lean-forge          # structure + mirror, plus lake build if available
foundry run lean-dag-figure     # figures/anomaly-forge/lean-dag.svg
foundry run compile-coq         # the Coq side, via coqc
```

CI runs both provers: `compile-coq` and `compile-lean` in
`.github/workflows/verify-proofs.yml`.
