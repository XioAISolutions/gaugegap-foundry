# Offering — Certified numerics & machine-checkable certificates

A consulting / small-engagement offer built on capability already demonstrated in
this repository. Honest scope, fixed deliverables.

> Contact: **[your name]** · **[email]** · **[links]** · rates **[day / project]**.

## What I provide

1. **Certified eigenvalue / spectral bounds.** Rigorous, directed-rounding
   interval-arithmetic enclosures for finite matrices/operators — **rigorously
   certified** bounds, not floating-point estimates (a-posteriori residual /
   Bauer–Fike style),
   with arbitrary precision via mpmath / Arb.
2. **Machine-checkable certificates.** Export the result to **Lean 4 / Coq /
   Isabelle** with the numeric certificate as a single, clearly-labelled trust
   input — so a third party can re-check the claim in a proof assistant.
3. **Reproducibility harness.** Hashed, byte-reproducible artifacts + a CI gate so
   the numbers regenerate identically and don't silently drift.

## Who this is for

- **Research groups** needing referee-proof numerical claims.
- **Safety-critical / finance** teams wanting verified bounds (eigenvalues,
  spectra, error envelopes) rather than point estimates.
- **Formal-methods teams** wanting a numerics→proof-assistant bridge.

## Proof it works (this repo)

- Certified interval-arithmetic kernel, **~14.5× optimized with bit-identical
  output** (PR #29).
- A finite-truncation theorem exported and discharged in **Lean/Coq/Isabelle**
  (`results/curverank-formal/`, `docs/curverank-formal-proof.md`).
- ~490 passing tests; strict claim-boundary audit at 0 high.

## Engagement shape

- **Scoping call (free)** → fixed-scope statement of work.
- **Deliverables:** the certified-bounds module for your problem, the
  proof-assistant export, a reproducibility harness, and a short report stating
  *exactly* what is and isn't certified.
- **Process:** verification-first — every number reproducible before it's reported.

## Honest boundaries

I certify **finite computations** (a specific matrix / finite truncation), not
asymptotic or infinite statements. The showcase result is a certified **negative**
result and is **not a proof** of the Riemann Hypothesis or any Millennium Prize
problem — what's for sale is the rigorous-numerics + certificate-export capability.
