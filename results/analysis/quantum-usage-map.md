# Quantum Usage Map

Current maximum active level: **2 (quantum_circuit_simulation)**.
Hardware-ready level: **3 (hardware_ready_boundary)**.

The project uses quantum simulators (Qiskit + Braket local) and has hardware runners ready for IBM Runtime and AWS Braket cloud devices. Real QPU execution requires provider credentials.

## Levels

- `0 classical_reference`: exact local baselines and finite-system definitions.
- `1 quantum_operator_representation`: Hamiltonians represented as quantum operators.
- `2 quantum_circuit_simulation`: circuits or quantum algorithms run in simulators.
- `3 hardware_ready_boundary`: validated circuits are ready for provider submission.
- `4 hardware_executed`: real QPU job submitted and recorded.

## Surfaces

### exact_dense_baselines

- Track: `GaugeGap / FlowGap / CurveRank`
- Level: `0 classical_reference`
- Status: `active`
- Real hardware: `False`
- Command: `python scripts/run_gap_sweep.py`
- Meaning: Classical baselines define the finite systems and acceptance references.
- Next gate: Keep these as the source of truth before any simulator or QPU claim.

### qiskit_pauli_operator

- Track: `GaugeGap`
- Level: `1 quantum_operator_representation`
- Status: `active`
- Real hardware: `False`
- Command: `python scripts/run_gap_sweep.py --method qiskit-pauli`
- Meaning: Builds the finite Hamiltonian as a Qiskit SparsePauliOp and checks it against dense exact diagonalization.
- Next gate: Use this before turning a Hamiltonian into circuits or IBM Runtime observables.

### qiskit_statevector_dynamics

- Track: `GaugeGap`
- Level: `2 quantum_circuit_simulation`
- Status: `active`
- Real hardware: `False`
- Command: `python scripts/run_dynamics.py --backend statevector`
- Meaning: Builds a Trotter circuit and evaluates exact simulated quantum-state observables.
- Next gate: Compare with shot sampling and noisy simulation before hardware.

### qiskit_aer_sampler

- Track: `GaugeGap`
- Level: `2 shot_based_quantum_simulation`
- Status: `active`
- Real hardware: `False`
- Command: `python scripts/run_dynamics.py --backend aer-sampler --noise depolarizing`
- Meaning: Samples Trotter circuits through Aer, including a simple depolarizing noise model.
- Next gate: Only move to hardware when analysis gates pass under shot/noise drift.

### flowgap_vqls_statevector

- Track: `FlowGap`
- Level: `2 quantum_algorithm_simulation`
- Status: `active`
- Real hardware: `False`
- Command: `python scripts/run_flowgap_burgers.py --quantum`
- Meaning: Runs a tiny VQLS-style pressure-Poisson subroutine through statevector simulation.
- Next gate: Treat as a quantum-algorithm benchmark, not a Navier-Stokes theorem route.

### braket_local_simulator

- Track: `GaugeGap`
- Level: `2 braket_local_simulation`
- Status: `active`
- Real hardware: `False`
- Command: `python scripts/run_hardware.py --provider braket-local`
- Meaning: Runs Trotter circuits on Braket local StateVectorSimulator for cross-platform validation.
- Next gate: Compare Braket local results with Qiskit statevector before cloud submission.

### ibm_runtime_sampler

- Track: `GaugeGap`
- Level: `3 hardware_ready_boundary`
- Status: `ready`
- Real hardware: `True`
- Command: `python scripts/run_hardware.py --provider ibm`
- Meaning: Submits validated circuits to IBM Runtime SamplerV2/EstimatorV2 on a physical backend. Requires QISKIT_IBM_TOKEN.
- Next gate: Run only after statevector and Aer analysis gates pass. Ledger must record job_id, backend, shots.

### braket_cloud_devices

- Track: `GaugeGap`
- Level: `3 braket_cloud_boundary`
- Status: `ready`
- Real hardware: `True`
- Command: `python scripts/run_hardware.py --provider braket-cloud --device-name ionq-aria1`
- Meaning: Submits circuits to IonQ, Rigetti, or managed Braket simulators via AWS. Requires AWS credentials.
- Next gate: Run only after Braket local simulator results match Qiskit statevector. Ledger must record task_id, device_arn, shots.

### future_quantinuum

- Track: `GaugeGap`
- Level: `3 future_provider_boundary`
- Status: `planned`
- Real hardware: `False`
- Command: `not implemented`
- Meaning: Future pytket/Quantinuum backend for trapped-ion SU(2) gauge experiments.
- Next gate: Do not implement until IBM and Braket artifacts are stable and reproducible.

## IBM Runtime Readiness

- Dependency present: `True`
- Token env present: `False`
- Instance env present: `False`
- Status: `not_probed`
