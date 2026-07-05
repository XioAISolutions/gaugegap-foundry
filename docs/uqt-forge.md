# UQT Forge

UQT Forge is a bounded GaugeGap track for quantum-native algebra content inspired
by the Universal Quantum Transformer literature.

## What It Is

The first unit, `uqt-0001`, is an evidence pack rather than a training claim.  It
records exact finite algebra tasks and a 5-qubit UQT-like circuit ledger:

- `Z_11` addition
- `Z_11` multiplication including zero as an irreversible negative control
- `Z_11*` multiplication on the nonzero multiplicative group
- `S_4` Cayley-table composition
- SU(2) Euler mixing blocks plus a cyclic CNOT-ring unitary skeleton
- UQT-style parameter accounting

The finite checks answer a narrower question than the paper: can the repository
hold exact algebra known-answer tasks, reversibility controls, and qubit/parameter
accounting in a reproducible form before any optimizer or provider integration is
introduced?

## Claim Boundary

Allowed language:

- finite UQT-inspired algebra benchmark
- exact known-answer algebra table
- reversible/irreversible control
- 5-qubit circuit-accounting scaffold
- external literature inspiration

Avoid:

- independent reproduction of UQT crystallization
- IBM Quantum hardware result
- language understanding
- general intelligence
- proof that quantum models are universally superior

## Why The Negative Control Matters

The UQT paper emphasizes that unitary quantum dynamics naturally fits reversible
structure.  `uqt-0001` therefore keeps multiplication by zero in `Z_11` as a
negative control: its rows are not permutations because many inputs collapse to
zero.  A good Foundry artifact should not convert that into a pass.

## Next Build Rungs

1. Add an optional optimizer and record training traces.
2. Add a small classical baseline with the same train/test split.
3. Add optional Qiskit export after the local statevector evidence is stable.
4. Treat any provider execution as a separate artifact requiring backend, job ID,
   shots, calibration window, and raw counts.

## Run

```bash
python scripts/run_uqt_forge.py --task all --output-dir /tmp/uqt-0001
```

The script emits `summary.json`, `cases.csv`, `ledger.jsonl`, and
`uqt_forge.svg`.
