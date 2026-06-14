# Spectra — a certified spectral-screening language

Spectra is a tiny declarative DSL over this repository's certified pipeline. It is
a concrete answer to "what would a small, honest quantum/AI-adjacent language for
*this* problem look like?"

Its one defining idea: **certification is a first-class semantic.**

- A value produced by `certify` is a rigorous **interval** (verified eigenvalue
  enclosures + Arb-certified zeros) — floats never silently leak.
- An `assert separated(...)` is **discharged by the interval kernel** — emitting a
  machine-checkable Lean/Coq certificate — or the **program fails**. You cannot
  state a spectral separation the kernel will not back.

This makes the repo's claim-boundary ethos executable: a Spectra program that runs
is, by construction, only making claims that are certified.

> **Scope (binding).** Spectra screens finite-truncation candidate Hilbert–Pólya
> operators and benchmarks them. It is **not** a general quantum programming
> language, and it does **not** prove the Riemann Hypothesis — every Spectra
> claim is a finite-system, certified negative-result about a finite matrix.

## Example

`examples/curverank_screen.spectra`:

```
zeros    Z   = riemann(20)

operator xp  = berry_keating(n=20)
operator dr  = dirac_rindler(n=20)
operator qg  = quantum_graph(n=20)

certify  Mx  = mismatch(xp, Z)
certify  Md  = mismatch(dr, Z)
certify  Mq  = mismatch(qg, Z)

assert   separated(Mx, threshold=1.0)
assert   separated(Md, threshold=1.0)
assert   separated(Mq, threshold=1.0)

report   "results/spectra-demo"
```

Run it:

```bash
python scripts/run_spectra.py examples/curverank_screen.spectra
```

Output (certified intervals; each assertion emits a Lean/Coq certificate):

```
certify Mx: xp n=20 M in [35.535690, 35.535690]
certify Md: dirac_rindler n=20 M in [26.191066, 26.191066]
certify Mq: quantum_graph n=20 M in [76.165716, 76.165716]
assert separated(Mx, > 1.0): OK (certified lower 35.535690) -> Lean/Coq certificate
...
report -> results/spectra-demo
```

## Grammar

One statement per line; `#` starts a comment.

| Statement | Meaning |
|---|---|
| `zeros Z = riemann(k)` | the first `k` Arb-certified non-trivial zeros |
| `operator x = <family>(n=N)` | a finite truncation of a candidate family |
| `certify M = mismatch(x, Z)` | certified L2 spectral mismatch interval `M_n` |
| `assert separated(M, threshold=t)` | discharge `M ≥ t` (Lean/Coq) or fail |
| `measure Q = qpe(x, window=r, precision=p)` | windowed QPE eigenvalue recovery (needs qiskit) |
| `report "dir"` | write the JSON report + emitted certificates |

Families: `berry_keating` (xp), `dirac_rindler`, `quantum_graph`.

## How it compiles

Spectra is an interpreter (`src/gaugegap/spectra_lang/`) over existing primitives —
no new math, just a declarative surface:

- `certify` → `gaugegap.curverank_certified.certified_family_mismatch`
- `assert separated` → `gaugegap.rigorous.curverank_formal_emit.discharged_separation_proof`
  (raises if the certified lower bound does not exceed the threshold — that's the
  failure semantic)
- `measure qpe` → the windowed QPE path in `scripts/run_curverank_ibm.py`
- `report` → JSON bundle + `.lean`/`.v` certificates per assertion

## Why a DSL at all (and why not more)

A general-purpose quantum or AI language would compete with mature ecosystems
(Qiskit, Q#, Quipper, PennyLane, CUDA-Q; PyTorch/JAX) and is a multi-year effort
with little payoff here. The honest, high-value version is this **thin, certified
DSL**: it makes whole screening experiments declarative, reproducible, and
self-documenting, and it bakes the project's integrity rule into the language —
a program that runs only asserts what is certified. That is a genuine
differentiator, not a reimplementation.

Possible extensions (only if a need appears): a `prove monotone` verb over a
panel; vendor backends for `measure` (`backend=ibm-hardware`); export of the whole
program-run as a reviewer packet.
