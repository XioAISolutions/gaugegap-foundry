# Entanglement-formation dynamics

A finite-model demonstration of how entanglement **builds up over time** during an
interaction — inspired by attosecond-entanglement research (entanglement forms over
a finite interval, not instantaneously).

`gaugegap.quantum.entanglement_dynamics`:
- `two_qubit_exchange_model(coupling)` — an excitation localized on qubit 0 (`|10>`)
  exchange-coupled (XX+YY) to its partner; entanglement grows from zero.
- `simulate_buildup(H, psi0, ...)` — exact statevector evolution; returns the
  entanglement-entropy curve `S(t)`, the asymptote, and the **build-up time** (time
  to reach a fraction of the max).

```bash
make entanglement-dynamics
python scripts/run_entanglement_dynamics.py --coupling 1.0 --energy-scale-ev 10
```

On the exchange model, `S(0)=0` grows to `ln 2`, with a finite build-up time (≈0.30
model units; ≈20 as at an illustrative 10 eV scale). An `S(t)` figure is written.

## Claim boundary

This is a **finite-model** demonstration of entanglement-formation dynamics,
**inspired by** the TU Wien attosecond-entanglement result — it is **not** a
reproduction of the helium photoionization experiment, nor a claim about the
specific ~232 attosecond figure or any real atom. The physical-time (attosecond)
conversion `t = t_model · ħ/E` is **illustrative only**. Exact statevector,
dependency-light (numpy). Not a continuum/Millennium claim.
