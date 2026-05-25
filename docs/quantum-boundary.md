# Where Quantum Is Actually Used

This project currently has three different layers that are easy to confuse.

## 1. Classical baselines

These are not quantum:

- exact dense diagonalization;
- Burgers finite-difference dynamics;
- CurveRank toy-operator diagonalization;
- dynamics analysis gates.

They are still mandatory because they define the finite systems and acceptance
criteria.

## 2. Quantum simulation

This is where the repo currently uses quantum tooling:

- `qiskit-pauli` builds Hamiltonians as Qiskit `SparsePauliOp` objects;
- `run_dynamics.py --backend statevector` builds Trotter circuits and evaluates
  exact quantum-state observables;
- `run_dynamics.py --backend aer-sampler` samples those circuits through Qiskit
  Aer, optionally with depolarizing noise;
- FlowGap's VQLS subroutine runs a quantum-algorithm benchmark in statevector
  simulation.

This is real quantum-program design, but it is not real QPU execution.

## 3. Real quantum hardware

Real hardware begins only when a validated circuit is submitted to a provider
runtime, for example IBM Runtime Sampler/Estimator on an operational physical
backend.

That is not active yet.

Use:

```bash
python scripts/quantum_status.py
python scripts/quantum_status.py --probe-ibm
```

The first command writes `results/analysis/quantum-usage-map.*`. The second
tries to inspect IBM Runtime credentials and available physical backends without
submitting a job.

## Current boundary

The current maximum active level is:

```text
2 quantum_circuit_simulation
```

The next level is:

```text
3 hardware_ready_boundary
```

Do not describe any result as a real quantum-hardware result until the run
ledger contains a provider job id, backend name, shot count, and hardware
calibration context.
