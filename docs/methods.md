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

## Current model

The current `z2_dual_chain` implementation uses a dense transverse-field Ising
Hamiltonian:

```text
H = -J sum_i Z_i Z_{i+1} - h sum_i X_i
```

This is a finite-system sanity benchmark for the foundry pipeline. It is not
continuum Yang-Mills.
