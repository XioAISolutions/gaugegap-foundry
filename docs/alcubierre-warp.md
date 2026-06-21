# Alcubierre warp metric: certified negative-energy requirement

The GR/QFT sibling of the [entanglement speed limit](entanglement-speed-limit.md).
Where the quantum speed limit gives a rigorous *floor* on how fast entanglement can
form, the energy conditions give a rigorous *obstruction* to the Alcubierre warp
bubble: it provably requires **negative energy density**, and quantum field theory
bounds how much negative energy can exist.

## The metric and its energy density

The Alcubierre (1994) metric contracts space ahead of a craft and expands it behind,
allowing globally faster-than-light *coordinate* travel while every local observer
stays subluminal (so the bubble itself does not signal faster than light — the same
no-signaling caveat as the quantum thread). In geometric units (`G = c = 1`) the
energy density seen by Eulerian observers is, in closed form,

```
rho(x,y,z) = -(1/(8 pi)) * (v_s^2 (y^2 + z^2) / (4 r_s^2)) * f'(r_s)^2
```

with `r_s = sqrt((x - x_s)^2 + y^2 + z^2)`, bubble velocity `v_s`, shape function
`f`. This is `-(non-negative prefactor) * (a square)`, so:

- **`rho <= 0` everywhere**, and `rho < 0` wherever the wall has a gradient — the
  **weak energy condition is violated for any bubble parameters**.
- The negative energy concentrates in a **torus** around the bubble wall (radius
  `~ R`): the *ring of negative energy density*.
- `total negative energy ∝ v_s^2` and grows with wall steepness.

`gaugegap.relativity.alcubierre`:
- `energy_density(x, y, z, *, v_s, R, sigma)` — the exact closed form.
- `total_negative_energy(...)` — integrated negative energy (geometric units).
- `ford_roman_bound(tau)` — the quantum-inequality floor `~ 3/(32 pi^2 tau^4)`.
- `analyze_warp_bubble(...)` — samples `rho`, certifies the WEC violation, and emits
  a discharged Lean 4 / Coq certificate of `rho_nonpos : -(1/(8 pi)) K s <= 0` from
  `K >= 0` (a ratio of squares) and `s = f'(r_s)^2 >= 0` (discharged by
  `nlinarith` / `nra`, no holes).

```bash
make alcubierre-warp
python scripts/run_alcubierre_warp.py --v-s 2 --sigma 8
```

## The quantum-inequality obstruction

Ford–Roman quantum inequalities bound the magnitude and duration of negative energy
density a quantum field can sustain. Pfenning & Ford (1997) applied them to the warp
bubble and found the wall must be only a few hundred Planck lengths thick unless the
total exotic energy is astronomically large (of order the mass-energy of the visible
universe for a macroscopic bubble). This module reports the QI floor, but the
dramatic violation is a **macroscopic** result; in the dimensionless toy units used
here it is illustrative only — the rigorous, machine-checked content of this module
is the exact energy-condition violation.

## Claim boundary

A **classical-GR + semiclassical-QFT analysis of a toy metric**. It does **not**
build a warp drive and makes **no** claim that faster-than-light travel is
achievable. The negative-energy (weak-energy-condition) violation is exact and
machine-checked; the quantum-inequality obstruction is the standard literature
result. Dependency-light (numpy). Not a continuum/Millennium claim.

References: Alcubierre, *Class. Quantum Grav.* **11** (1994) L73; Ford & Roman,
*Phys. Rev. D* **51** (1995) 4277; Pfenning & Ford, *Class. Quantum Grav.* **14**
(1997) 1743.
