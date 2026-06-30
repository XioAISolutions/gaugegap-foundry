# FlowGap — the Navier–Stokes equations, term by term

The incompressible Navier–Stokes equations govern viscous fluid motion:

```text
continuity:  ∇·u = 0
momentum:    ∂u/∂t + (u·∇)u = −(1/ρ)∇p + ν∇²u + f
```

FlowGap is the Navier–Stokes-adjacent track. Each term in the popular "what the
reel animates" breakdown maps onto code that already runs in this repository.

> **Boundary:** everything here is a finite-grid surrogate. None of it is a
> continuum existence or smoothness result for Navier–Stokes, and none of it is a
> Millennium Prize solution. The 3D global-regularity question is explicitly out of
> scope.

## Term ↔ implementation

| Term | Meaning | Where it lives |
|---|---|---|
| `∂u/∂t` | local acceleration | explicit time step in `flowgap_navier_stokes.simulate_navier_stokes_2d` |
| `(u·∇)u` | convective (nonlinear) acceleration — the turbulence driver | `_advect_diffuse` (also `-u·dudx` in `flowgap_burgers.burgers_viscous_1d`) |
| `−(1/ρ)∇p` | pressure gradient | pressure step in the projection (`pressure_poisson_2d` + gradient subtraction) |
| `ν∇²u` | viscous diffusion / internal friction | central-difference Laplacian in `_advect_diffuse` (also `nu·d2udx2` in Burgers) |
| `∇·u = 0` | incompressibility (continuity) | `divergence_2d` + the Chorin projection that enforces it |
| `f` | body forces | optional forcing on the right-hand side |

## The two surrogates already in the repo

- **`flowgap-0001` viscous Burgers (1D)** is exactly the reduced Navier–Stokes
  momentum equation: convective `(u·∇)u` plus viscous `ν∇²u`, with no pressure. It
  is the standard simplification used to study the nonlinear term in isolation.
- **`flowgap-0003` Lorenz** is a severe truncation of 2D Rayleigh–Bénard
  convection — a genuine fluid-dynamics lineage for the "chaos from the nonlinear
  term" story.

## `flowgap-0005` — a finite 2D incompressible surrogate

`flowgap_navier_stokes.py` assembles the convective and viscous terms with the
existing pressure-Poisson projection (Chorin's method) and runs the **Taylor–Green
vortex**, an exact unsteady incompressible solution on the unit periodic square
whose kinetic energy decays analytically as `exp(−4 ν k² t)` with `k = 2π`.

What the run certifies as finite-grid evidence:

- **deterministic** integration for fixed inputs;
- **monotone** kinetic-energy decay under the unforced viscous flow;
- a **divergence-controlled** field — the projection cuts the divergence of a
  divergent field by more than 10× (collocated central differences do not reach
  machine zero, which is stated, not hidden);
- recovery of the **analytic decay rate** `4 ν k²` to ~1% on a 16×16 grid, with the
  error **shrinking under grid refinement** (≈1.9% → 1.1% → 0.4% at 12 → 16 → 24).

```bash
foundry run flowgap-0005-navier-stokes
foundry run flowgap-0005-smoke
```

The reel's other numerical methods (finite volume, finite element, lattice
Boltzmann, DGSEM) are natural further surrogates; the repository currently uses
finite differences.

> **Boundary:** a finite grid that tracks an exact analytic solution well is
> numerical evidence for the configured integration. It does not establish
> existence, uniqueness, or smoothness of solutions in the continuum, and it is not
> a proof about turbulence.
