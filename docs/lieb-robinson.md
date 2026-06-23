# Lieb–Robinson light cone

A many-body speed limit and the **information ↔ time** edge of the
[physical-limits web](physical-limits-web.md): with local interactions, information
cannot spread arbitrarily fast — a local perturbation stays, up to exponentially small
tails, inside a linear light cone `x(t) ≤ v_LR·t + ξ`.

This completes a **trio of speed limits** in the web: the quantum speed limit (a single
state's evolution), Cherenkov (a local medium speed limit), and Lieb–Robinson (a
many-body information speed limit).

## Model

Single-excitation hopping on an open chain — a continuous-time quantum walk on a path
graph, `H = -J Σ |i⟩⟨i+1| + h.c.`. The exact single-particle amplitude is
`|⟨x|e^{-iHt}|0⟩| = |J_x(2Jt)|` (a Bessel function), so:

- the **group (ballistic) front** advances at `2|J|`;
- the **rigorous Lieb–Robinson velocity** is `v_LR = e|J|` — from `|J_x(2Jt)| ≤ (eJt/x)^x`,
  the amplitude is exponentially small once `x > e|J|t`, so `e|J|` bounds even the
  leading Bessel tail (it exceeds the group velocity).

`gaugegap.quantum.lieb_robinson`:
- `chain_hamiltonian`, `evolve_distribution`, `front_position`, `group_velocity`,
  `lieb_robinson_velocity`.
- `analyze_lieb_robinson(...)` — measures the information front vs time, confirms it
  respects `x(t) ≤ v_LR·t + ξ` (fixed Lieb–Robinson length `ξ`), **cross-checks the
  evolution against the (previously dormant) `quantum_walks` CTQW** (agreement to ~1e-16
  when SciPy is present), and emits a discharged Lean 4 / Coq certificate of the linear
  cone `vf ≤ v_LR, t ≥ 0 ⟹ vf·t ≤ v_LR·t`. The schema is added to the
  [z3 verifier](certificate-verification.md).

```bash
make lieb-robinson
python scripts/run_lieb_robinson.py --n-sites 41 --J 1.0
```

## Claim boundary

A finite, exact lattice demonstration of the Lieb–Robinson light cone for a
**free-hopping** model (where `v_LR = e|J|` is the exact Bessel-bound velocity); it is
not the general interacting Lieb–Robinson constant. Dependency-light (numpy core;
optional SciPy cross-check via `quantum_walks`). Not a continuum/Millennium claim.

References: Lieb & Robinson, *Commun. Math. Phys.* **28** (1972) 251; Hastings (2010).
