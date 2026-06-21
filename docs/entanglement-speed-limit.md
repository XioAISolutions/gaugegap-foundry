# Quantum speed limit on entanglement formation

A rigorous follow-on to [entanglement-formation dynamics](entanglement-dynamics.md).
The attosecond-entanglement result shows entanglement forms over a *finite* time;
**quantum speed limits** explain why there must be a floor and let us **certify** it.

For a state evolving under a time-independent `H` (ħ = 1), the time `t` to reach a
state at Fubini–Study angle `L = arccos|⟨ψ₀|ψ_t⟩|` satisfies both

- **Mandelstam–Tamm:** `t ≥ L / ΔE`, with `ΔE = √(⟨H²⟩ − ⟨H⟩²)`
- **Margolus–Levitin:** `t ≥ L / (⟨H⟩ − E₀)`

so `t ≥ τ_QSL := max(τ_MT, τ_ML)`.

`gaugegap.quantum.entanglement_speed_limit`:
- `quantum_speed_limit(H, ψ₀, ψ_target)` — both floors + the geometric angle.
- `max_entangling_rate(H, ψ₀, times)` — peak `|dS/dt|` (scales with the coupling).
- `certified_buildup_speed_limit(H, ψ₀, ...)` — measures the build-up time, checks
  `t ≥ τ_QSL`, and emits a discharged Lean 4 / Coq certificate of
  `respects_qsl : t ≥ max(τ_MT, τ_ML)` (the two QSL inequalities are the labelled
  trust inputs; the assistant discharges the floor with `linarith` / `lra`).

```bash
make entanglement-speed-limit
python scripts/run_entanglement_speed_limit.py --energy-scale-ev 10
```

On the XX+YY exchange model the evolution moves along a **geodesic** in projective
Hilbert space, so the build-up time **saturates** the Mandelstam–Tamm limit
(`t* = τ_QSL`): entanglement forms as fast as quantum mechanics allows. The floor
scales as `1/J` with the coupling (a stronger interaction lets entanglement form
faster), shown in a floor-vs-coupling figure.

## Claim boundary

A **finite-model** demonstration. The QSL inequalities are exact and **machine-
checked** on the simulated evolution; this is **not** a reproduction of the TU Wien
helium experiment, the ~232 attosecond figure, or any real atom. The physical-time
(attosecond) conversion `t = t_model · ħ/E` is **illustrative only**. Dependency-
light (numpy). Not a continuum/Millennium claim.
