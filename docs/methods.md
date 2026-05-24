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

## Current model

The current `z2_dual_chain` implementation uses a dense transverse-field Ising
Hamiltonian:

```text
H = -J sum_i Z_i Z_{i+1} - h sum_i X_i
```

This is a finite-system sanity benchmark for the foundry pipeline. It is not
continuum Yang-Mills.
