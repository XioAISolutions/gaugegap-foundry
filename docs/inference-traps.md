# The web of inference traps

A companion to the [physical-limits web](physical-limits-web.md). That web takes viral
*physics* reels and reduces each to a single machine-checked inequality. This one does
the same for the *decision-theory and statistics* genre — the "ragebait" probability
puzzles and the classic inference traps — reducing each to an **exact, bounded,
certifiable core** with an explicit claim boundary.

The thesis is the same one stated in
[epistemics & claim boundaries](epistemics-and-claim-boundaries.md): a viral puzzle
earns a place here **only if it has a certifiable core**, and only in its proper domain.
These are decision theory and statistics — *not* physical bounds — so they live in
[`gaugegap.decision`](../src/gaugegap/decision/), never in the physical-limits web.

## The members

| Trap | Family | Exactly-computable core | Module |
|---|---|---|---|
| St. Petersburg paradox | heavy tail | naive EV diverges (truncated EV = `n`); bounded-utility CE = `$4`; finite-bankroll EV = `N+1` | [`st_petersburg`](../src/gaugegap/decision/st_petersburg.py) |
| Power law | heavy tail | scale-free tail `P(X>cx)/P(X>x) = c^{-α}`; `E[Xᵐ]=∞ ⟺ m≥α` | [`power_law`](../src/gaugegap/decision/power_law.py) |
| Regression to the mean | conditioning | `E[Y\|X=x] = ρx` (SD units): selected extremes regress by `1−ρ` | [`regression_to_mean`](../src/gaugegap/decision/regression_to_mean.py) |
| Survivorship bias (Wald) | selection | survivor hit-rate `= p·(1−kill)`: naive "armor the holes" is exactly backwards | [`survivorship_bias`](../src/gaugegap/decision/survivorship_bias.py) |
| Berkson's paradox | selection (collider) | independent traits acquire corr `= −1/2` (for `p=q=½`) once you condition on selection | [`berksons_paradox`](../src/gaugegap/decision/berksons_paradox.py) |
| Simpson's paradox | confounding | every subgroup favours A, the aggregate favours B (kidney-stone data) | [`simpsons_paradox`](../src/gaugegap/decision/simpsons_paradox.py) |
| Bayes' theorem | (the fix) | base-rate fallacy: 99%-accurate test, 0.1% prevalence ⇒ `P(disease\|+) ≈ 1.9%` | [`bayes`](../src/gaugegap/decision/bayes.py) |

## Two families, one lesson

**Heavy-tail / mean traps** — the *mean is the wrong summary*. The St. Petersburg game
has an infinite expected value yet a finite worth; a power-law variable with tail
exponent `α ≤ 1` has no finite mean at all. When the tail is heavy, "expected value"
quietly stops being a safe decision rule — which is exactly the gap the St. Petersburg
reel dramatizes. (The boundary lines of the cosmic mass–radius diagram are themselves
power laws — straight lines of slope ±1 in log–log.)

**Selection / conditioning traps** — *conditioning on the wrong variable flips the
conclusion*. Wald's bombers, Berkson's hospital admissions, and Simpson's subgroups are
the same mistake wearing three costumes: you analyse the data you can see (survivors,
the admitted, the aggregate) instead of the data you need. Regression to the mean is the
gentle version — select on an extreme and the follow-up is closer to average, with *no
causal story required*. Bayes' theorem is the framework that gets all of these right by
forcing the base rate (the prior) into the calculation.

## Why this belongs in a verification-first repo

These are not decoration. This repository's own methodology *is* these lessons applied:

- It **retains negative and failed results** — a direct guard against survivorship bias
  (don't condition your conclusions on the experiments that "returned").
- It **states base rates and claim boundaries** rather than headline numbers — the
  Bayesian and base-rate-fallacy discipline.
- It treats **divergent / heavy-tailed quantities** (infinite EV, unbounded moments) as
  signals to switch summaries, exactly as the physical-limits web treats divergences as
  signals that a naive model has left its domain.

Each module verifies its core with **exact closed forms** (not Monte-Carlo) and carries
a claim boundary; none is Coq-discharged, because the content is elementary exact
arithmetic rather than a real-analysis inequality. The one viral puzzle that did **not**
make it — a "consciousness coefficient" infographic — is documented in the epistemics
note as the negative control: no certifiable core, so no place here.

## What is deliberately excluded

- **Expected value** as such is a *building block*, not a trap; it appears throughout
  (and is precisely what St. Petersburg stress-tests), so it gets no standalone module.
- **The Hawthorne effect** (being observed changes behaviour) has no clean exact core
  *as sociology*, so it is not certified here. Its tempting equation with quantum
  measurement is a *category error* — one is a study-design effect on human behaviour,
  the other a physical property of non-commuting observables. The honest resolution is
  to certify the **physics**, not the metaphor: the rigorous cousin of "observation
  changes the system" lives in the physical-limits web as the
  [quantum Zeno effect](physical-limits-web.md) — frequent measurement provably freezes
  evolution (`survival ≥ 1 − (ΔE·T)²/N → 1`,
  [`gaugegap.quantum.quantum_zeno`](../src/gaugegap/quantum/quantum_zeno.py)) — with the
  analogy to the human-behaviour effect explicitly bounded, never asserted.
