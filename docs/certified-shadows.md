# Certified classical shadows

Classical shadows estimate many observables from few measurements. This layer adds
**honest confidence bands** on top: a **median-of-means** estimator over independent
shadow batches plus a confidence interval, cross-validated against the exact
expectation.

## Method

`gaugegap.quantum.certified_shadows`:
- Implements the Huang–Kueng–Preskill random-Pauli classical-shadow protocol
  directly (single-qubit rotations + the `3·U†|b⟩⟨b|U − I` inverse channel),
  unit-tested against exact values. (The repo's older
  `shadow_tomography.classical_shadow_pauli` did not reproduce arbitrary-observable
  expectations, so this module supersedes it for certified estimates.)
- `certified_shadow_estimate(state, observables, n_snapshots, n_batches, level, seed)`
  runs the protocol over `n_batches` independent child seeds; the robust point
  estimate is the **median of the batch means**, and the CI is the
  normal-approximation interval over batches (`repeated_runs.confidence_interval`).
- Each result records `estimate`, the CI, the exact `⟨ψ|O|ψ⟩`, and whether the CI
  **covers** the exact value. The largest CI half-width feeds an `ErrorBudget`
  (statistical/stochastic component).

## Use it

```bash
make certified-shadows
python scripts/run_certified_shadows.py --operator berry_keating_xp --n-basis 8
```

```python
from gaugegap.quantum.certified_shadows import certified_shadow_estimate
res = certified_shadow_estimate(psi, {"Z0Z1": ZZ}, n_snapshots=800, n_batches=16)
res["Z0Z1"].ci_low, res["Z0Z1"].ci_high, res["Z0Z1"].covered
```

On the Berry-Keating ground state (3 qubits, 95% level) all single-site and
two-site CIs cover the exact expectations.

## Claim boundary

A **statistical** confidence band on a **finite-state** observable at a **fixed shot
budget** — median-of-means is a standard robust shadow estimator. Not a continuum,
Yang-Mills, or Millennium claim. Dependency-light (numpy only).
