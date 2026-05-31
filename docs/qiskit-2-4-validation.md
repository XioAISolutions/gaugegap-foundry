# Qiskit 2.4 Validation Layer

Boundary: **finite-system Qiskit validation only; no continuum Yang-Mills mass-gap claim.**

GaugeGap treats Qiskit as an optional validation adapter, not as a base dependency. The finite exact baseline and Pauli dense replica must run without Qiskit.

## Workflow

The Qiskit layer follows the map, optimize, execute, analyze pattern:

1. map the finite Z2 candidate into first-class Pauli terms and a small hardware-test circuit;
2. optimize/inspect the circuit through Qiskit transpilation;
3. execute only local statevector/Aer paths by default;
4. analyze dense-vs-SparsePauliOp agreement and simulator artifacts.

## Command

```bash
python scripts/run_qiskit_candidate_validation.py \
  --n-plaquettes 1 \
  --plaquette-coupling 1.0 \
  --transverse-field 0.2 \
  --shots 1024 \
  --output-dir /tmp/gaugegap-qiskit-validation
```

The command does not require IBM Runtime credentials.

## Outputs

- `qiskit_validation.json`
- `qpy_manifest.json`
- `candidate_circuit.qpy` when QPY export is available
- `QISKIT_VALIDATION_SUMMARY.md`

The QPY manifest records the circuit hash, loaded circuit width/depth, operation counts, and finite-system claim boundary.

## Dependency posture

Base install remains local:

```bash
python -m pip install -e .
```

Optional quantum validation uses:

```bash
python -m pip install -e '.[quantum]'
```

The optional dependency set targets `qiskit>=2.4,<3`, `qiskit-aer>=0.17`, and `qiskit-ibm-runtime>=0.46`.

## Claim boundary

Hardware and simulator outputs are reproducible experimental artifacts for finite candidates. Hardware results are noisy experimental artifacts and do not constitute mathematical proof.
