# Ergotropy & passivity: certified bound on extractable work

The honest, rigorous response to "free energy / infinite energy / anti-gravity
device" claims. The maximum work a **cyclic** device can extract from a quantum state
is its **ergotropy** — a finite quantity — and it is governed by the same variational
principle that underlies the certified brackets in this repo.

For a state `rho` and Hamiltonian `H`,

```
W(rho, H) = Tr(rho H) - min_U Tr(U rho U^dagger H) = Tr(rho H) - E_passive,
```

where the passive energy `E_passive` pairs the largest populations with the lowest
energies (a rearrangement inequality). Rigorous facts:

- `W >= 0` always, and `W <= Tr(rho H) - E0` — **no energy can be drawn below the
  ground energy** `E0`; there is no bottomless well.
- A **ground** state or a **thermal** (Gibbs) state is **passive**: `W = 0`.
- After one optimal extraction the state is passive, so a **second cycle yields 0** —
  no perpetual motion.

`gaugegap.quantum.ergotropy`:
- `ergotropy`, `passive_energy`, `passive_density_matrix`, `is_passive`,
  `thermal_state`.
- `analyze_ergotropy(rho, H)` — emits a discharged Lean 4 / Coq certificate that
  `0 <= W <= Tr(rho H) - E0` (`linarith` / `lra`, no holes) and checks the
  second-cycle ergotropy is ~0.

```bash
make ergotropy
python scripts/run_ergotropy.py
```

The runner also confirms numerically that the passive energy is the minimum over
1500+ random unitaries, and plots the cumulative extracted work saturating across
cycles (the visual statement of "no free energy").

## Claim boundary

A finite, exact result about extractable work in quantum systems. It **refutes**
free-energy / infinite-energy / anti-gravity device claims rather than validating
them — extractable work is finite (often zero) and cannot be cycled for net gain.
Bismuth diamagnetic levitation is real physics, but it is a *static equilibrium* that
stores no free energy. Dependency-light (numpy). Not a continuum/Millennium claim.

References: Allahverdyan, Balian & Nieuwenhuizen, *Europhys. Lett.* **67** (2004) 565;
Pusz & Woronowicz, *Commun. Math. Phys.* **58** (1978) 273; Lenard, *J. Stat. Phys.*
**19** (1978) 575.
