# GaugeGap Lean project

Lean 4 + Mathlib formalisation of the Anomaly Forge hypercharge result.

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
dag.json                                   node structure (no verification status)
```

Three tracks: `anomaly-forge` (13 nodes), `infogap-no-hiding` (7 nodes) and
`hadamard-gram` (8 nodes). The latter two are second-prover checks of
`formal/infogap/no_hiding_finite.v` and `formal/hadamard/gram_identity.v`;
between them they cover every named result in every curated Coq source, which
`tests/test_prover_correspondence.py` enforces.

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

Exact rational cancellation conditions for a declared finite chiral field
inventory. Not a statement about arbitrary chiral gauge theories, not a
continuum construction, and not a Millennium Prize claim. Node `A08` records
that uniqueness fails once a Dirac right-handed neutrino is admitted.

The written argument is in `docs/blueprint-anomaly-uniqueness.md`.
