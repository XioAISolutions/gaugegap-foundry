# Technical-depth exhibit — GaugeGap Foundry

> **Secondary / "how deep can he go" page.** The primary portfolio is
> [`README.md`](./README.md) (AI Product & Construction-Tech). This page exists to
> answer one question from a technical interviewer or a skeptical client: *can he
> actually drive rigorous, well-tested, reproducible engineering — not just demos?*
>
> The answer is a real, public, CI-green codebase. Every claim below links to
> merged, tested work; nothing here is slideware.

> Maintainer: **Viacheslav (Slava) Smagin** · slavazeph@gmail.com · 647-863-9522 ·
> Toronto, ON · github.com/XioAISolutions · xioai.co

## What this repo is

A verification-first **quantum / scientific-computing** infrastructure project.
It is deliberately over-engineered for rigor: certified numerics, machine-checkable
proofs, hardware-path quantum code, and a CI that *audits its own claims*.

- **Stack:** Python (numpy, scipy, mpmath, `python-flint`/Arb), Qiskit / IBM
  Runtime, optional CUDA-Q, Lean 4 / Coq / Isabelle export, GitHub Actions CI.
- **Evidence of discipline:** ~490 tests passing, byte-reproducible build
  artifacts, a strict automated claim-boundary audit at **0 high findings**,
  ~35 reviewed PRs.

## Skills matrix (each linked to real work)

| Skill | Demonstrated by |
|---|---|
| Rigorous / certified numerics | interval-arithmetic eigenvalue enclosures + a **~14× kernel speedup, bit-identical** (`src/gaugegap/rigorous/`, PR #29) |
| Formal verification | machine-checkable separation theorem exported to **Lean 4 / Coq / Isabelle** (`docs/curverank-formal-proof.md`, PR #10) |
| Quantum software | QPE (register/windowed/iterative/Trotter), IBM Runtime path with mitigation (`curverank_qpe.py`, `providers/ibm_adapter.py`) |
| Quantum signal processing | Hadamard test, `g(t)`, Prony/ESPRIT, **QCELS**, classical shadows, amplitude estimation (`curverank_signal.py`, PRs #31/#32) |
| Language / DSL design | two interpreters, **Spectra** & **Verdict**, with certified / eval-first semantics (`spectra_lang/`, `verdict_lang/`) |
| GPU acceleration | optional, capability-gated **CUDA-Q** backend with CPU fallback + parity test (`providers/cudaq_adapter.py`, PRs #34/#35) |
| Reproducibility / DevX | one-command `make` targets, hashed proofpacks, reviewer packets, hermetic CI |
| Technical writing | cited landscape survey, honest evaluations, runbooks (`docs/`) |

## Four worked case studies (problem → built → result)

### 1. A ~14× speedup of a certified-numerics kernel — with zero result change
**Problem.** Certified eigenvalue enclosures (directed-rounding interval
arithmetic) dominated runtime: a representative screening workload took ~155 s,
~98% inside one residual routine.
**Built.** Profiled the hot path, then reused the mpmath interval matrix **once per
eigensolve** (instead of once per eigenpair), all arithmetic kept in the
directed-rounding context — same operations, order, precision.
**Result.** **~14.5× faster (155 s → ~10.7 s), bit-for-bit identical output**,
verified by recorded certified values + 490 passing tests. *(PR #29)*

### 2. A certified result, exported to three proof assistants
**Problem.** Turn a numerical separation result into something a machine can check
— without overclaiming.
**Built.** Assembled the certified finite-truncation theorem as a formal object and
exported it to **Lean 4 / Coq / Isabelle**, with discharged (`linarith`/`lra`)
proofs whose single trust input is the interval certificate.
**Result.** Reproducible proof bundle + honest docs precisely stating what is and
is **not** a proof. *(PR #10)*

### 3. A quantum signal-extraction toolkit
**Problem.** Extract spectral content from quantum states beyond textbook QPE, in a
way that is testable without hardware.
**Built.** Hadamard test, correlation signal `g(t)`, Prony/ESPRIT super-resolution,
**QCELS**, classical shadows, amplitude estimation — exact statevector mode for
deterministic CI, plus a dephasing+shot noise study.
**Result.** Recovers a benchmark spectrum to ~1e-14 (exact mode), every eigenvalue
validated against certified enclosures; honest finding that QCELS is noise-robust
while full-spectrum super-resolution is fragile. *(PRs #31/#32)*

### 4. Two "honest-by-construction" DSLs
**Problem.** Make scientific integrity executable, not aspirational.
**Built.** **Spectra** (a claim passes only if the interval kernel discharges it,
emitting a Lean/Coq certificate) and **Verdict** (a model claim passes only if a
logged, reproducible eval backs it) — interpreters where an unbacked claim *fails
the program*.
**Result.** Working DSLs + CLIs + tests where the honest-failure cases are
asserted. *(PRs #26/#27/#33)*

## How to read the repo in 5 minutes
1. `README.md` — the tracks, diagrams, and claim boundary.
2. `docs/curverank-formal-proof.md` — certified result → machine-checkable proof.
3. `docs/curverank-signal-extraction.md` — the quantum signal-extraction toolkit.

> **Honest scope.** The science here is finite-system spectral *screening* — a
> certified **negative** result. It is **not a proof** of the Riemann Hypothesis or
> any Millennium Prize problem. What it demonstrates is *engineering capability*:
> rigorous, reproducible, well-tested software, and the discipline to bound a claim
> before making it. That discipline is the transferable asset — it's the same thing
> that makes a product ship correctly and a build come in on spec.
