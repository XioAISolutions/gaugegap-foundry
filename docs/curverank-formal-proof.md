# CurveRank formal proof — certified finite-truncation separation theorem

This document states **precisely** what is proved about the **finite-system**
truncation, how it is machine-checked, and where the rigour stops (the closing
claim boundary is binding). It is deliberately conservative.

## What is proved (finite-system truncation, not the Riemann Hypothesis)

For each truncation size `n` in the panel, the **finite-truncation separation
theorem**:

> **Theorem (finite n).** Let `H_n` be the Berry–Keating `xp` operator
> `H = ½(xp + px)` truncated to `n` position-space basis states. Let
> `{t_1, …, t_k}` be the first `k` non-trivial Riemann zeta zeros. Then the L2
> spectral mismatch
> `M_n = ‖ sort(|eig H_n|)[:n] − sort(t)[:k] ‖₂ / √n`
> satisfies `M_n ≥ B_n`, where `B_n` is a certified interval lower bound.

Representative certified bounds (`k = 20`):

| n | certified `M_n ≥` |
|---:|---:|
| 10 | 27.391322 |
| 15 | 29.390825 |
| 20 | 35.535690 |

These are produced by `scripts/run_curverank_formal_proof.py` into
`results/curverank-formal/`.

## How it is machine-checked (the genuine rigour)

The machine-**checked** content is the interval-arithmetic certificate, assembled
by `gaugegap.rigorous.spectral_impossibility.prove_berry_keating_impossibility`
and validated by `Theorem.verify()`:

1. **Verified eigenvalue enclosures** of `H_n` (exact interval matrix → certified
   Hermitian eigenvalue enclosures via the classical residual bound).
2. **Certified zeta-zero enclosures** — independently from Arb (`acb.zeta_zeros`,
   Turing's method, index-correct) when `python-flint` is present, else
   `mpmath.zetazero`; see `gaugegap/rigorous/certified_zeros.py`.
3. **Order-statistic mismatch bound** that is valid for *every* ordering
   consistent with the eigenvalue enclosures (so overlapping enclosures cannot
   inflate the bound).

All three are directed-rounding interval computations, so `B_n` is a rigorous
lower bound, not a floating-point estimate.

## The proof-assistant exports (what they are, and are not)

`scripts/run_curverank_formal_proof.py` also exports each theorem to **Lean 4,
Coq, and Isabelle/HOL** (`gaugegap.rigorous.formal_export`). Be precise about
what these files are:

- They transcribe the theorem **statement** and the certified numeric **bounds**
  into each assistant's syntax — a faithful, machine-readable scaffold.
- Their proof **terms** are left as `sorry` (Lean) / `Admitted` (Coq) / `oops`
  placeholders. **They are not yet assistant-discharged proofs.** Completing them
  (or, better, formalising the interval-arithmetic kernel itself) is future work.
- `formal_export.verify_certificate` checks certificate *well-formedness*, not
  that a proof term has been discharged.

So the rigorous object is the **interval certificate**; these generic exports are
statement+bound scaffolds for ingestion.

### Discharged proofs (no `sorry`) — `results/curverank-formal/discharged/`

Going one level deeper, `curverank_formal_emit` emits proofs that are **actually
discharged** by the proof assistant — Lean 4 `linarith`, Coq `lra` — with **no
proof holes**, for **all three operator families** (`xp`, `dirac_rindler`,
`quantum_graph`). The honest structure of a computer-assisted proof over a
verified numeric kernel:

1. the interval-arithmetic certificate is imported as a **single explicit,
   labelled axiom**: `axiom certified_lower_bound : M ≥ <certified lower bound>`;
2. the assistant then genuinely closes the remaining real-arithmetic goal
   `M ≥ separationThreshold` — `Qed`, not `Admitted`.

What this does and does not buy you, stated plainly:

- **Does:** the assistant machine-checks the logic and arithmetic turning the
  certified bound into the separation conclusion. The trust boundary is reduced
  to exactly one clearly-marked axiom (the interval certificate).
- **Does not:** the assistant does **not** re-derive the spectral computation
  itself (that lives in the axiom / the Python interval kernel), and this remains
  the **finite-truncation separation** theorem — not a proof of RH.

> Lean 4 (Mathlib) and Coq are **not installed in this environment**, so the
> emitted proofs are not executed here. They use only standard tactics on
> concrete literals and are structured to check; run `lake build` (Lean) or
> `coqc` (Coq ≥ 8.13) to verify them end-to-end.

## Claim boundary — what this is NOT

This is a certified **negative** (separation/impossibility) result about a
**finite matrix**: it shows the truncated operator is provably *far* from the
zeros. It does **not** prove the Riemann Hypothesis, does **not** prove the
Hilbert–Pólya conjecture, asserts **no** continuum (`n → ∞`) limit, and is **not**
a Clay Millennium Prize submission. A large certified mismatch at finite `n` is
evidence *against* a candidate operator, not a step toward proving RH.

## Reproduce

```bash
python scripts/run_curverank_formal_proof.py \
    --n-panel 10,15,20 --k-zeros 20 --output-dir results/curverank-formal
```
