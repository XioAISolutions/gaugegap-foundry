# Unified pipeline — one path through every depth of the repo

`scripts/run_unified_pipeline.py` (target: `make unified`) threads a **single**
finite truncation of the Berry-Keating `xp` operator through every layer the
repository provides, then **cross-validates the layers against each other** and
emits one report that is checked by the repo's own claim-boundary audit.

This is the integration spine: it shows that the classical, rigorous, quantum,
advanced-quantum, formal, and DSL tracks are not separate demos but one coherent,
mutually-checking stack.

## The path

| Stage | Layer | What it does | Module(s) |
|---|---|---|---|
| 0 | Classical | dense Hermitian diagonalization | `curverank_operators`, numpy |
| 1 | Rigorous certified | interval-arithmetic eigenvalue enclosures + certified mismatch `M_n` vs the Riemann zeros (directed rounding) | `curverank_certified` |
| 2 | Quantum QPE | windowed phase estimation on the local Aer emulator (reuses the existing `run_curverank_ibm.run_one`) | `curverank_qpe`, `providers/ibm_adapter` |
| 3 | Quantum signal | `g(t)` → ESPRIT super-resolution + QCELS, validated against the certified enclosures | `curverank_signal` |
| 4 | Advanced quantum | ground-state entanglement entropy across every single-site bipartition (reference-checked) | `quantum/quantum_information` |
| 4b | **Deep quantum** (`--deep`) | a quantum Krylov subspace eigensolver (multi-eigenvalue, validated against the certified enclosures), Trotter/qDRIFT Hamiltonian-simulation fidelity, ground-state entanglement structure (entropy + negativity), and a Heisenberg-limit metrology bound with Fisher information | `quantum/quantum_subspace_methods`, `quantum/advanced_hamiltonian_simulation`, `quantum/quantum_metrology`, `quantum/quantum_information` |
| 5 | Cross-validation | classical vs certified vs QPE vs ESPRIT vs QCELS, with explicit residuals | — |
| 6 | Formal proof | discharged Lean 4 / Coq separation certificate (single trust input = the interval certificate) | `rigorous/curverank_formal_emit` |
| 7 | Honest-by-DSL | a generated **Spectra** program whose `assert separated(...)` only passes because the kernel certifies it | `spectra_lang` |
| 8 | Audited report | unified JSON + Markdown, then `claim_boundary_audit.py --strict` is run on the output | `scripts/claim_boundary_audit.py` |

## Representative result (`n_basis=8`, `k_zeros=20`)

Cross-validation of the smallest positive eigenvalue (target `0.99595933`,
certified enclosure `[0.99595933, 0.99595933]`):

| Method | Estimate | \|error\| vs classical |
|---|---|---|
| classical (exact) | 0.99595933 | 0 |
| certified enclosure | 0.99595933 | ~6e-15 |
| quantum QPE (Aer, 9 qubits, depth 587) | 0.99609375 | ~1.3e-4 |
| quantum ESPRIT | 0.99595933 | ~3e-15 |

- **Max cross-method error ~1.3e-4**; all methods agree to 1e-2.
- ESPRIT recovers **8/8** modes inside their certified enclosures.
- QCELS independently recovers the dominant eigenvalue (`~7.0578`), reported
  honestly as the coarser method (it sits just outside the ~1e-14 enclosure).
- Formal stage: separation **discharged** (lower bound `25.226 > 1.0`), Lean 4 +
  Coq certificates emitted.
- DSL stage: the Spectra `assert separated` **passes by certificate**.
- The generated report **passes** `claim_boundary_audit.py --strict` (0 high findings).

### Deep quantum layer (`--deep`)

- **Quantum Krylov subspace eigensolver** recovers the 4 lowest eigenvalues, all
  **4/4 inside their certified enclosures** — an independent quantum eigensolver
  agreeing with the certified kernel.
- **Hamiltonian-simulation fidelity** for `exp(-iHt)` across first/second/fourth-
  order Trotter and qDRIFT (the dynamics primitive QPE rides on).
- **Entanglement structure** of the certified ground state: entropy ~0.194 and
  **negativity ~0.5155** for the `q0 | rest` bipartition.
- **Quantum metrology (Heisenberg limit)** for the spectral gap: reports the
  precision, Fisher information, and Heisenberg-limited flag.

## Run it

```bash
make unified                      # n_basis=8, full path incl. Aer QPE + --deep
python scripts/run_unified_pipeline.py --n-basis 16 --k-zeros 30 --deep
python scripts/run_unified_pipeline.py --skip-quantum   # fast, no simulator
```

Outputs land in `results/unified-pipeline/` (`pipeline.json`, `pipeline.md`).
Tests: `tests/test_unified_pipeline.py`.

## Claim boundary

This is finite-system spectral screening plus a method benchmark (claim
boundary). Every quantum number is cross-checked against the certified kernel. It
is a certified negative-result screening: these truncations are bounded away from
the Riemann zeros. It is not a proof of the Riemann Hypothesis and is not a Clay
Millennium Prize submission, and the maximum quantum level reached is simulation,
not hardware.
