# gaugegap-0004: Hardware-Readiness Validation

`gaugegap-0004` is the handoff layer between finite candidate discovery and optional quantum-provider execution.

Boundary: **finite-system validation only; no continuum Yang-Mills mass-gap claim.**

## IBM/Qiskit findings applied

IBM's current Qiskit materials point to a clean execution pattern:

1. map the problem to quantum-native circuits/operators;
2. optimize circuits and operators before execution;
3. execute through primitive functions only after local checks pass;
4. analyze deviations after execution.

The IBM Hello World guide also uses `qiskit[all]~=2.4.0` and `qiskit-ibm-runtime~=0.46.1`, and emphasizes secure Runtime credential setup before QPU access.

The Qiskit 2.4 release notes are especially relevant to GaugeGap because they emphasize:

- Pauli-centric workflows and Pauli-based computation support;
- faster QPY serialization/deserialization for larger circuit workflows;
- improved transpilation infrastructure;
- Python 3.10+ as the supported baseline;
- C API improvements that may later matter for compiled high-performance extensions.

## Design decision

Real hardware submission is **not** the default path.

The correct pipeline is:

```text
finite candidate
→ exact dense baseline
→ Pauli dense replica
→ resource estimate
→ Qiskit availability probe
→ shot/noise proxy
→ hardware-readiness score
→ optional Qiskit statevector/Aer
→ optional IBM Runtime execution
```

## Local validation command

```bash
python scripts/run_candidate_validation.py \
  --n-plaquettes 1 \
  --plaquette-coupling 1.0 \
  --transverse-field 0.2 \
  --shots 1024 \
  --output-dir /tmp/gaugegap-0004
```

## Outputs

- `hardware_readiness.json`
- `VALIDATION_SUMMARY.md`

## Score interpretation

- `ready_for_simulator_and_tiny_qpu_trial`: local checks are clean enough for statevector/Aer and possibly a tiny IBM Runtime trial.
- `ready_for_simulator_not_hardware`: use simulator validation first; do not submit to hardware yet.
- `not_ready`: fix exact, replica, noise, resource, or dependency issues first.

## Non-goals

This milestone does not:

- claim quantum advantage;
- claim a continuum mass gap;
- submit hardware jobs automatically;
- turn finite Z2 toy behavior into a Yang-Mills proof.

The purpose is to make the handoff from finite exact benchmarks to Qiskit/IBM execution disciplined, reproducible, and non-hype.
