# CurveRank QPE hardware-feasibility report

Generated: 2026-06-13T00:48:47.926256  
n_precision: 4; metric: transpiled to {u, cx}, optimization_level=1

## Findings

- **Qubit width:** the iterative single-ancilla variant uses 5 qubits at n_basis=16 versus 8 for the register-based variants -- the consistent NISQ advantage.
- **CX count:** across the measured sizes the dense controlled unitary remains cheaper in CX than Trotter; the crossover lies beyond the largest n_basis tested (dense grows like 4^n_system, so extend the sweep to locate it).
- **Hardware primitive:** dense synthesis loads an arbitrary unitary (not a device primitive); Trotter/iterative use only rotation gates.

## Measurements

| n_basis | sys qubits | pauli terms | dense CX | trotter CX | iter-round CX | iter qubits |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 1 | 1 | 26 | 78 | 32 | 2 |
| 4 | 2 | 6 | 55 | 619 | 320 | 3 |
| 8 | 3 | 25 | 226 | 3322 | 1760 | 4 |
| 16 | 4 | 92 | 969 | 14969 | 7968 | 5 |

Claim boundary: Circuit-resource proxy for hardware feasibility only; no hardware run and no scientific claim about operator spectra.
