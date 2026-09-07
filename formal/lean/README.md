# GaugeGap Lean project

Lean 4 + Mathlib formalisation of the repository's exact finite results.

```text
GaugeGapLean/AnomalyForge/Defs.lean        anomaly coefficients over ℚ
GaugeGapLean/AnomalyForge/Statements.lean  one Prop per DAG node
GaugeGapLean/AnomalyForge/Proofs.lean      one theorem per statement
GaugeGapLean/InfoGap/Defs.lean             no-hiding circuit probabilities over ℝ
GaugeGapLean/InfoGap/Statements.lean       one Prop per DAG node
GaugeGapLean/InfoGap/Proofs.lean           one theorem per statement
GaugeGapLean/Hadamard/Defs.lean            popcount inner product over lists of signs
GaugeGapLean/Hadamard/Statements.lean      one Prop per DAG node
GaugeGapLean/Hadamard/Proofs.lean          one theorem per statement
GaugeGapLean/Variational/Defs.lean         Rayleigh quotients in a declared eigenbasis
GaugeGapLean/Variational/Statements.lean   one Prop per DAG node
GaugeGapLean/Variational/Proofs.lean       one theorem per statement
GaugeGapLean/Reversibility/Defs.lean       AND, Toffoli and Fredkin over Bool
GaugeGapLean/Reversibility/Statements.lean one Prop per DAG node
GaugeGapLean/Reversibility/Proofs.lean     one theorem per statement
dag.json                                   node structure (no verification status)
```

Five tracks, 44 nodes:

| Track | Nodes | What it is | Blueprint |
|---|---|---|---|
| `anomaly-forge` | A01–A17 | hypercharge uniqueness for a declared chiral inventory, and the two-dimensional span that replaces it once a right-handed neutrino is admitted | `docs/blueprint-anomaly-uniqueness.md` |
| `infogap-no-hiding` | B01–B07 | second-prover check of `formal/infogap/no_hiding_finite.v` | `docs/blueprint-no-hiding-lean.md` |
| `hadamard-gram` | C01–C08 | second-prover check of `formal/hadamard/gram_identity.v` | `docs/blueprint-hadamard-gram-lean.md` |
| `gaugegap-variational` | D01–D05 | the Courant–Fischer step the emitted bracket certificates assume as `variational_upper` | `docs/blueprint-variational-bound.md` |
| `landauer-reversibility` | E01–E07 | which finite gates destroy information, and what carrying the inputs forward buys | `docs/blueprint-reversibility-lean.md` |

The B and C tracks are second-prover checks; between them they cover every named
result in every curated Coq source, which `tests/test_prover_correspondence.py`
enforces. The D and E tracks are not transliterations — D removes an assumption
from certificates this repository already emits, and E supplies the exact
entropy that `gaugegap.quantum.landauer` turns into an energy.

Every node also has an exact Python mirror (`src/gaugegap/*_theorem.py`, composed
in `src/gaugegap/lean_mirror.py`) that restates it over `Fraction` or by
exhaustion. The mirror is a cross-check on the statements, not a substitute for
the kernel: `scripts/run_lean_forge.py` reports both, and only `lake build`
produces `verified`.

Statements and proofs are separate modules so that editing a proof does not
force a recompile of the statements other nodes depend on.

`lake-manifest.json` pins Mathlib to the `v4.11.0` tag
(`20c73142afa995ac9c8fb80a9bb585a55ca38308`) and its transitive dependencies to
the revisions that tag itself pins. Regenerate it with `lake update` after
changing `lakefile.toml` or `lean-toolchain`.

`dag.json` records structure only. Verification status is produced by
`lake build` and written to `results/lean-forge/lean_forge_report.json`; it is
never checked in as a property of a node.

That report is regenerated on every run and committed by CI **on the default
branch only**, after `lake build` has accepted every node — so `main` carries
evidence the kernel produced rather than whatever a toolchain-less environment
could generate. It is deliberately not committed onto pull request heads: a
push made with `GITHUB_TOKEN` does not trigger workflows, so doing that would
leave the head with no checks at all. On a branch the report says whatever the
author's environment could establish, usually `toolchain_missing`, and
`tests/test_lean_forge.py` fails if its recorded source hashes no longer match
the files — so it can be honest or absent, but never stale.

## Build

```bash
cd formal/lean
lake exe cache get   # Mathlib binaries; skip only if you like waiting
lake build
```

Then, from the repository root:

```bash
python scripts/run_lean_forge.py --require-verified
```

`--require-verified` exits non-zero unless Lean itself accepted every proof.
Without a toolchain the gate reports `toolchain_missing`; there is no simulated
proof mode.

## Claim boundary

Exact finite mathematics, per track, and nothing beyond it.

`anomaly-forge`: exact rational cancellation conditions for a declared finite
chiral field inventory. Not a statement about arbitrary chiral gauge theories,
not a continuum construction, and not a Millennium Prize claim. Node `A08`
records that uniqueness fails once a Dirac right-handed neutrino is admitted.

`gaugegap-variational`: finite-dimensional linear algebra for a declared
eigenbasis expansion. The spectral theorem that supplies the basis is a standing
hypothesis, not a result of the track, and nothing here bears on the Yang–Mills
mass gap.

`landauer-reversibility`: exact combinatorics for named finite Boolean
functions. It does not prove Landauer's principle, does not compute a heat, and
makes no claim connecting erasure to gauge invariance or to a spectral gap — a
truncated Hilbert space in a lattice simulation is an approximation in a model,
not a physical erasure.

Each track's written argument is in the blueprint listed in the table above.
