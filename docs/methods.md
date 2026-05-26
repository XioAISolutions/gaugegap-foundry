# Methods Notes

## Registered hypotheses

Each experiment starts as a registered hypothesis in `hypotheses/`. The registry
records the finite model, claimed observable, control parameters, required
validation steps, and kill criteria.

## Run ledger

Every run records:

- hypothesis id;
- code version;
- model parameters;
- Hamiltonian parameter hash;
- observable;
- method;
- result values.

Provider-specific metadata will be added when simulator and QPU backends land.
The first provider-shaped path is `qiskit-pauli`, which constructs the same
finite Hamiltonian as a Qiskit `SparsePauliOp` and diagonalizes its dense matrix
as an independent representation check.

The first circuit-dynamics path is `run_dynamics.py`, which builds a first-order
Trotter circuit for the same finite Hamiltonian and records Z-site and nearest
neighbor ZZ observables through either Qiskit statevector simulation or an Aer
shot sampler.

`analyze_dynamics.py` is the first acceptance-gate layer. It treats statevector
results as the local reference, compares clean Aer shot drift and depolarizing
noise drift, then emits details, summaries, verdicts, and an SVG plot.

## Current models

The `z2_dual_chain` implementation uses a dense transverse-field Ising
Hamiltonian:

```text
H = -J sum_i Z_i Z_{i+1} - h sum_i X_i
```

This is a finite-system sanity benchmark for the foundry pipeline. It is not
continuum Yang-Mills.

The `gaugegap-0002` implementation uses a finite Z2 open-plaquette-chain toy
Hamiltonian:

```text
H = -J sum_p prod_{l in p} Z_l - h sum_l X_l
```

The direct dense path enumerates computational basis states, applies diagonal
plaquette products in the Z basis, and flips individual link bits for the X
field. The Pauli replica path exports Qiskit-compatible labels, interprets the
rightmost Pauli character as qubit 0, reconstructs the dense matrix, and checks
it against the direct dense Hamiltonian. The local VQE-style path is a
statevector simulator prototype only; it is not QPU hardware evidence.

Claim boundary for `gaugegap-0002`: finite Z2 lattice gauge toy benchmark only;
no continuum Yang-Mills mass-gap claim.
