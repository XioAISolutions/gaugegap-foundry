# GaugeGap Lean project

Lean 4 + Mathlib formalisation of the Anomaly Forge hypercharge result.

```text
GaugeGapLean/AnomalyForge/Defs.lean        anomaly coefficients over ℚ
GaugeGapLean/AnomalyForge/Statements.lean  one Prop per DAG node
GaugeGapLean/AnomalyForge/Proofs.lean      one theorem per statement
dag.json                                   node structure (no verification status)
```

Statements and proofs are separate modules so that editing a proof does not
force a recompile of the statements other nodes depend on.

`dag.json` records structure only. Verification status is produced by
`lake build` and written to `results/lean-forge/lean_forge_report.json`; it is
never checked in as a property of a node.

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
