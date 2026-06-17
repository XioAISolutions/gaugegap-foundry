# SBIR / STTR narrative (draft) + topic shortlist

Non-dilutive grant funding (Phase I typically $50–300k; months, not asap). This is
a reusable technical narrative; confirm against **live open topics** before
submitting and fill the **[brackets]**.

## Topic fit shortlist (verify currency)

- **DOE ASCR / Quantum** — verified/quantum scientific computing, rigorous numerics.
- **NSF (SBIR + relevant directorates)** — reproducible research software,
  formal-methods-adjacent tooling.
- **DoD (service SBIRs)** — verification & validation, assurance for numerical /
  ML systems (the eval-first angle).

## Technical narrative (draft)

**Problem.** Numerical and ML claims are routinely reported without
machine-checkable evidence or reproducibility, which is unacceptable in research,
safety-critical, and assurance settings.

**Innovation.** A verification-first toolchain that (a) produces **certified**
(interval-arithmetic) numerical bounds, (b) exports them as **machine-checkable
certificates** (Lean/Coq/Isabelle), and (c) makes claims **executable** — a DSL
where an unbacked claim fails (Spectra for certified bounds, Verdict for ML evals).

**Preliminary results (all public, reproducible).** Certified eigenvalue
enclosures with a ~14.5× bit-identical kernel speedup; a finite-truncation theorem
discharged in three proof assistants; a quantum signal-extraction toolkit with a
noise study; ~490 passing tests at 0 high claim-boundary findings.

**Phase I aims.** [1] Generalize the certified-numerics + certificate export to a
target customer problem; [2] harden the eval-first DSL into a usable assurance
tool; [3] reproducible benchmark report + a pilot with **[partner]**.

**Commercialization.** Consulting on certified numerics (see
`docs/offerings/certified-numerics.md`) and an AI-eval/guardrails product (see
`docs/product/verdict-eval-product.md`).

## Honest scope

The showcase science is a certified finite-system **negative** result; it is
**not a proof** of the Riemann Hypothesis or any Millennium Prize problem. The
fundable innovation is the verification-first tooling, not a prize claim.

> Blanks: entity + SAM/registrations, PI, budget + justification, partner letters,
> the specific solicitation/topic number.
