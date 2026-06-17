# Portfolio — GaugeGap Foundry

A capability portfolio built from a real, public, CI-green codebase:
**verification-first quantum / scientific-computing infrastructure.** Every claim
below links to merged, tested work in this repository — no slideware.

> Maintainer: **[your name]** · **[email]** · **[GitHub/LinkedIn]** ·
> available for **[contract / full-time]**, **[rate / range]**.

## Snapshot

- **Language/stack:** Python (numpy, scipy, mpmath, `python-flint`/Arb), Qiskit /
  IBM Runtime, optional CUDA-Q, Lean 4 / Coq / Isabelle export, GitHub Actions CI.
- **Scale of evidence:** ~490 tests passing, byte-reproducible build artifacts, a
  strict automated claim-boundary audit at **0 high findings**, ~35 reviewed PRs.
- **Ethos:** every result is reproducible and scope-bounded before any claim — the
  same discipline teams want in research, safety-critical, and ML-eval work.

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

## How to read the repo in 5 minutes

1. `README.md` — the tracks, diagrams, and claim boundary.
2. `docs/curverank-formal-proof.md` — certified result → machine-checkable proof.
3. `docs/curverank-signal-extraction.md` — the quantum signal-extraction toolkit.
4. `docs/portfolio/case-studies.md` — four worked case studies with metrics.

> **Honest scope.** The science here is finite-system spectral *screening* — a
> certified **negative** result. It is **not a proof** of the Riemann Hypothesis
> or any Millennium Prize problem. What it demonstrates is engineering capability:
> rigorous, reproducible, well-tested quantum and scientific software.
