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
- `run_hardware.py --provider braket-local` runs Trotter circuits on the Braket
  local StateVectorSimulator for cross-platform validation;
- FlowGap's VQLS subroutine runs a quantum-algorithm benchmark in statevector
  simulation.

This is real quantum-program design, but it is not real QPU execution.

## 3. Real quantum hardware (ready, not yet executed)

Hardware runners are implemented and tested. They will submit validated circuits
to real QPU backends when provider credentials are configured:

- **IBM Runtime**: `run_hardware.py --provider ibm` uses SamplerV2 with
  dynamical decoupling and transpilation. Requires `QISKIT_IBM_TOKEN`.
- **AWS Braket cloud**: `run_hardware.py --provider braket-cloud` submits to
  IonQ (Aria, Forte), Rigetti (Ankaa-2), QuEra Aquila, or managed simulators
  (SV1, DM1, TN1). Requires AWS credentials.

Every hardware result must record provider job/task id, backend/device name,
shot count, and circuit metadata in the run ledger.

Use:

```bash
python scripts/quantum_status.py
python scripts/quantum_status.py --probe-ibm
python scripts/run_hardware.py --provider braket-local --n-sites 4 --times 0,0.5
python scripts/run_hardware.py --provider ibm --n-sites 4 --times 0,0.5
python scripts/run_hardware.py --provider braket-cloud --device-name sv1 --n-sites 4 --times 0,0.5
```

## Current boundary

The current maximum active level is:

```text
2 quantum_circuit_simulation (Qiskit + Braket local)
```

Hardware-ready level:

```text
3 hardware_ready_boundary (IBM Runtime + Braket cloud)
```

The runners are built. To move to level 4 (hardware_executed), configure
provider credentials and run `scripts/run_hardware.py`. Do not describe
any result as a real quantum-hardware result until the run ledger contains
a provider job id, backend name, shot count, and hardware calibration context.
