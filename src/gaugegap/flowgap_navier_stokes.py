"""FlowGap: finite 2D incompressible Navier-Stokes surrogate (Chorin projection).

This assembles the convective and viscous terms (the same operators used by the
1D viscous Burgers benchmark) with the existing pressure-Poisson projection so the
discrete velocity field stays approximately divergence-free. It is exercised on the
Taylor-Green vortex, an exact unsteady solution of the incompressible
Navier-Stokes equations on a periodic square, whose kinetic energy decays as
``exp(-4 nu k^2 t)`` with ``k = 2 pi``.

CLAIM BOUNDARY: this is a finite periodic-grid surrogate. The divergence-free and
energy-decay observables are numerical evidence for the configured finite
integration, not a continuum existence/smoothness result for Navier-Stokes and not
a Millennium Prize solution.
"""
from __future__ import annotations

import numpy as np

from gaugegap.flowgap_burgers import divergence_2d

CLAIM_BOUNDARY = (
    "finite periodic-grid incompressible Navier-Stokes surrogate; divergence-free "
    "and energy observables are numerical evidence for the configured finite "
    "integration, not a continuum regularity result or Millennium Prize solution"
)

# Fundamental wavenumber of the Taylor-Green vortex on the unit periodic square.
K = 2.0 * np.pi


def taylor_green(nx: int, ny: int) -> tuple[np.ndarray, np.ndarray]:
    """Exact incompressible Taylor-Green vortex on the unit periodic square."""
    x = np.linspace(0.0, 1.0, nx, endpoint=False)
    y = np.linspace(0.0, 1.0, ny, endpoint=False)
    grid_x, grid_y = np.meshgrid(x, y)  # shape (ny, nx); axis 1 is x, axis 0 is y
    ux = np.cos(K * grid_x) * np.sin(K * grid_y)
    uy = -np.sin(K * grid_x) * np.cos(K * grid_y)
    return ux, uy


def _poisson_operator(nx: int, ny: int) -> np.ndarray:
    """The 5-point periodic Laplacian used by ``pressure_poisson_2d``, row-0 pinned."""
    n = nx * ny
    dx = 1.0 / nx
    dy = 1.0 / ny
    A = np.zeros((n, n), dtype=np.float64)
    for j in range(ny):
        for i in range(nx):
            idx = j * nx + i
            A[idx, idx] = -2.0 / (dx * dx) - 2.0 / (dy * dy)
            A[idx, j * nx + (i + 1) % nx] += 1.0 / (dx * dx)
            A[idx, j * nx + (i - 1) % nx] += 1.0 / (dx * dx)
            A[idx, ((j + 1) % ny) * nx + i] += 1.0 / (dy * dy)
            A[idx, ((j - 1) % ny) * nx + i] += 1.0 / (dy * dy)
    A[0, :] = 0.0
    A[0, 0] = 1.0
    return A


def _advect_diffuse(
    ux: np.ndarray, uy: np.ndarray, nu: float, dt: float, dx: float, dy: float
) -> tuple[np.ndarray, np.ndarray]:
    """One explicit step of convective advection + viscous diffusion (no pressure)."""
    dudx = (np.roll(ux, -1, axis=1) - np.roll(ux, 1, axis=1)) / (2.0 * dx)
    dudy = (np.roll(ux, -1, axis=0) - np.roll(ux, 1, axis=0)) / (2.0 * dy)
    dvdx = (np.roll(uy, -1, axis=1) - np.roll(uy, 1, axis=1)) / (2.0 * dx)
    dvdy = (np.roll(uy, -1, axis=0) - np.roll(uy, 1, axis=0)) / (2.0 * dy)

    lap_u = (
        (np.roll(ux, -1, axis=1) - 2.0 * ux + np.roll(ux, 1, axis=1)) / (dx * dx)
        + (np.roll(ux, -1, axis=0) - 2.0 * ux + np.roll(ux, 1, axis=0)) / (dy * dy)
    )
    lap_v = (
        (np.roll(uy, -1, axis=1) - 2.0 * uy + np.roll(uy, 1, axis=1)) / (dx * dx)
        + (np.roll(uy, -1, axis=0) - 2.0 * uy + np.roll(uy, 1, axis=0)) / (dy * dy)
    )

    adv_u = ux * dudx + uy * dudy
    adv_v = ux * dvdx + uy * dvdy

    ux_star = ux + dt * (-adv_u + nu * lap_u)
    uy_star = uy + dt * (-adv_v + nu * lap_v)
    return ux_star, uy_star


def vorticity_2d(ux: np.ndarray, uy: np.ndarray, dx: float, dy: float) -> np.ndarray:
    dvdx = (np.roll(uy, -1, axis=1) - np.roll(uy, 1, axis=1)) / (2.0 * dx)
    dudy = (np.roll(ux, -1, axis=0) - np.roll(ux, 1, axis=0)) / (2.0 * dy)
    return dvdx - dudy


def kinetic_energy(ux: np.ndarray, uy: np.ndarray) -> float:
    return float(0.5 * np.mean(ux * ux + uy * uy))


def simulate_navier_stokes_2d(
    nx: int = 16,
    ny: int = 16,
    nu: float = 0.02,
    dt: float = 1.0e-3,
    n_steps: int = 200,
    ux0: np.ndarray | None = None,
    uy0: np.ndarray | None = None,
) -> dict[str, object]:
    """Integrate the finite 2D incompressible surrogate with Chorin projection.

    Returns deterministic histories plus the measured vs analytic Taylor-Green
    energy-decay rate and the divergence-control observables.
    """
    dx = 1.0 / nx
    dy = 1.0 / ny
    if ux0 is None or uy0 is None:
        ux0, uy0 = taylor_green(nx, ny)
    ux = np.array(ux0, dtype=np.float64)
    uy = np.array(uy0, dtype=np.float64)

    poisson_inv = np.linalg.inv(_poisson_operator(nx, ny))

    energy_history: list[float] = [kinetic_energy(ux, uy)]
    divergence_history: list[float] = [float(np.linalg.norm(divergence_2d(ux, uy, dx, dy)))]
    max_divergence = divergence_history[0]

    for _ in range(n_steps):
        ux_star, uy_star = _advect_diffuse(ux, uy, nu, dt, dx, dy)
        div_star = divergence_2d(ux_star, uy_star, dx, dy)
        rhs = (div_star / dt).ravel()
        rhs = rhs - np.mean(rhs)
        rhs[0] = 0.0
        pressure = (poisson_inv @ rhs).reshape(ny, nx)
        dpdx = (np.roll(pressure, -1, axis=1) - np.roll(pressure, 1, axis=1)) / (2.0 * dx)
        dpdy = (np.roll(pressure, -1, axis=0) - np.roll(pressure, 1, axis=0)) / (2.0 * dy)
        ux = ux_star - dt * dpdx
        uy = uy_star - dt * dpdy

        energy_history.append(kinetic_energy(ux, uy))
        div_norm = float(np.linalg.norm(divergence_2d(ux, uy, dx, dy)))
        divergence_history.append(div_norm)
        max_divergence = max(max_divergence, div_norm)

    total_time = n_steps * dt
    analytic_rate = 4.0 * nu * K * K
    # Energy-decay rate measured from the finite run, E(t) ~ E0 exp(-rate t).
    e0, ef = energy_history[0], energy_history[-1]
    measured_rate = float(-np.log(ef / e0) / total_time) if ef > 0 and e0 > 0 else float("nan")

    return {
        "nx": nx,
        "ny": ny,
        "nu": nu,
        "dt": dt,
        "n_steps": n_steps,
        "total_time": total_time,
        "energy_history": energy_history,
        "divergence_history": divergence_history,
        "max_divergence": max_divergence,
        "analytic_energy_decay_rate": float(analytic_rate),
        "measured_energy_decay_rate": measured_rate,
        "decay_rate_relative_error": float(abs(measured_rate - analytic_rate) / analytic_rate),
        "energy_monotone_nonincreasing": all(
            energy_history[i + 1] <= energy_history[i] + 1e-12
            for i in range(len(energy_history) - 1)
        ),
        "ux_final": ux,
        "uy_final": uy,
        "claim_boundary": CLAIM_BOUNDARY,
    }
