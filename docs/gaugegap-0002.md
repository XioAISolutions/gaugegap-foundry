# gaugegap-0002: Finite Z2 Plaquette Benchmark

`gaugegap-0002` is a finite Z2 lattice gauge toy benchmark. It is designed to
exercise the exact-solver, Pauli-export, certificate, and simulator-prototype
parts of the foundry on a model small enough to audit directly.

Boundary: **Finite Z2 lattice gauge toy benchmark only; no continuum
Yang-Mills mass-gap claim.**

## Model

The benchmark uses an open chain of square plaquettes represented by link
qubits. One plaquette has four links. Adjacent plaquettes share one link, so an
`n_plaquettes` chain has `3 * n_plaquettes + 1` links/qubits.

```text
H = -J sum_p prod_{l in p} Z_l - h sum_l X_l
```

`J` is `plaquette_coupling`; `h` is `transverse_field`.

## Exact Diagonalization

`scripts/run_z2_plaquette.py` builds the dense Hamiltonian directly from basis
states and computes:

```text
Delta = E1 - E0
```

using `numpy.linalg.eigh`. Outputs include JSON, CSV, and a gap certificate
that repeats the claim boundary.

```bash
python scripts/run_z2_plaquette.py --output-dir /tmp/gaugegap-0002-exact
```

`scripts/run_z2_plaquette_sweep.py` extends this into a small reproducible
grid over transverse field and plaquette count. It records the exact gap,
Pauli-replica deltas, mean plaquette-Z expectation, and mean link-X
expectation.

```bash
python scripts/run_z2_plaquette_sweep.py --output-dir /tmp/gaugegap-0002-sweep --run-id smoke
```

## Pauli/Qiskit Export

`scripts/run_quantum_gap_replica.py` exports Pauli labels for the same finite
Hamiltonian and reconstructs a dense matrix locally. Labels use Qiskit's
ordering convention: qubit 0 is the rightmost character.

The script verifies:

```text
hamiltonian_dense() == pauli_terms_to_dense(pauli_terms(...))
```

within numerical tolerance. If Qiskit is installed, the same labels are also
passed through `SparsePauliOp`.

```bash
python scripts/run_quantum_gap_replica.py --output-dir /tmp/gaugegap-0002-replica
python -m pip install -e '.[quantum]'
python scripts/run_quantum_gap_replica.py --output-dir /tmp/gaugegap-0002-replica-qiskit
```

This is an operator-representation check. It is not a hardware run.

## Local VQE-Style Prototype

`scripts/run_vqe_gap.py` runs a tiny local numpy statevector variational loop
for development of simulator workflows.

```bash
python scripts/run_vqe_gap.py --output-dir /tmp/gaugegap-0002-vqe --samples 64
```

The VQE-style result may report `warning_variational_gap_error` at low sample
counts. That warning is expected for rough local sampling and should not be
described as physics evidence.

## Tests

```bash
python -m pytest
python scripts/run_z2_plaquette.py --output-dir /tmp/gaugegap-0002-exact
python scripts/run_quantum_gap_replica.py --output-dir /tmp/gaugegap-0002-replica
python scripts/run_z2_plaquette_sweep.py --output-dir /tmp/gaugegap-0002-sweep --run-id smoke
python scripts/run_vqe_gap.py --output-dir /tmp/gaugegap-0002-vqe --samples 64
```

The acceptance tests check Hermiticity, finite non-negative gaps, Pauli ordering,
certificate claim boundaries, and script smoke execution.
