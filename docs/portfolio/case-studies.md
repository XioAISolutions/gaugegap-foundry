# Case studies

Four worked examples from this repository, each: **problem → what was built →
result**, with metrics that trace to merged, tested work. (PR numbers reference
this repo's history.)

## 1. A ~14× speedup of a certified-numerics kernel — with zero result change

**Problem.** Certified eigenvalue enclosures (directed-rounding interval
arithmetic) dominated runtime: a representative screening workload took ~155 s,
~98% inside one residual routine.

**What I built.** Profiled the hot path, then reused the mpmath interval matrix
**once per eigensolve** (instead of once per eigenpair) and kept all arithmetic in
the directed-rounding context — same operations, same order, same precision.

**Result.** **~14.5× faster (155 s → ~10.7 s), bit-for-bit identical output** —
verified by the recorded certified values and 49 tests, plus the full suite (490
passed). *Skills: profiling, numerical linear algebra, interval arithmetic,
regression safety.* (PR #29)

## 2. A certified result, exported to three proof assistants

**Problem.** Turn a numerical separation result into something a machine can check
— without overclaiming.

**What I built.** Assembled the certified finite-truncation theorem as a formal
object and exported it to **Lean 4 / Coq / Isabelle**, with discharged
(`linarith`/`lra`) proofs whose single trust input is the interval certificate.

**Result.** Reproducible proof bundle + honest docs precisely stating what is and
is **not a proof** (it is the finite-truncation separation, not the Riemann
Hypothesis). *Skills: formal methods, computer-assisted proof, scientific
integrity.* (PR #10)

## 3. A quantum signal-extraction toolkit

**Problem.** Extract eigenvalues / spectral content from quantum states beyond
textbook QPE, in a way that is testable without hardware.

**What I built.** Hadamard test, the correlation signal `g(t)`, Prony/ESPRIT
super-resolution, **QCELS** (Heisenberg-style, ~`1/T` scaling), classical shadows,
and amplitude estimation — all with an exact statevector mode for deterministic
tests, plus a dephasing+shot noise model and study.

**Result.** Recovers a benchmark operator's spectrum to ~1e-14 (exact mode), every
eigenvalue validated against certified enclosures; honest finding that QCELS is
noise-robust while full-spectrum super-resolution is fragile. *Skills: quantum
algorithms, signal processing, statistics, test design.* (PRs #31/#32)

## 4. Two "honest-by-construction" DSLs

**Problem.** Make scientific integrity executable, not aspirational.

**What I built.** **Spectra** (a claim only passes if the interval kernel
discharges it, emitting a Lean/Coq certificate) and **Verdict** (a model claim
only passes if a logged, reproducible eval backs it) — small interpreters where an
unbacked claim *fails the program*.

**Result.** Working DSLs + CLIs + tests where the honest-failure cases are
asserted. *Skills: language/interpreter design, API design, developer experience.*
(PRs #26/#27/#33)

---

> Every metric above is reproducible from the repo (`make` targets, `pytest`,
> `claim_boundary_audit.py`). Nothing is fabricated; the science stays a certified
> **negative** result, not a proof of any Millennium Prize problem.
