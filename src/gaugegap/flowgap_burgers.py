"""FlowGap: classical viscous Burgers solver and pressure-Poisson routines.

This is a finite reduced-model benchmark, not a Navier-Stokes regularity claim.
"""
from __future__ import annotations

import numpy as np


def burgers_viscous_1d(
    nx: int,
    nu: float,
    dt: float,
    n_steps: int,
    u0: np.ndarray | None = None,
    bc: str = "periodic",
) -> dict[str, object]:
    dx = 1.0 / nx
    x = np.linspace(0.0, 1.0, nx, endpoint=False)
    if u0 is None:
        u0 = np.sin(2.0 * np.pi * x)
    u = u0.copy()

    kinetic_history: list[float] = []
    residual_history: list[float] = []

    for _ in range(n_steps):
        u_old = u.copy()
        if bc == "periodic":
            dudx = (np.roll(u, -1) - np.roll(u, 1)) / (2.0 * dx)
            d2udx2 = (np.roll(u, -1) - 2.0 * u + np.roll(u, 1)) / (dx * dx)
        else:
            dudx = np.zeros_like(u)
            d2udx2 = np.zeros_like(u)
            dudx[1:-1] = (u[2:] - u[:-2]) / (2.0 * dx)
            d2udx2[1:-1] = (u[2:] - 2.0 * u[1:-1] + u[:-2]) / (dx * dx)

        rhs = -u * dudx + nu * d2udx2
        u = u_old + dt * rhs

        kinetic_history.append(float(0.5 * np.sum(u ** 2) * dx))
        residual_history.append(float(np.linalg.norm(u - u_old)))

    return {
        "u_final": u,
        "x": x,
        "kinetic_history": kinetic_history,
        "residual_history": residual_history,
        "nx": nx,
        "nu": nu,
        "dt": dt,
        "n_steps": n_steps,
    }


def poisson_matrix_1d(nx: int) -> np.ndarray:
    dx = 1.0 / nx
    A = np.zeros((nx, nx), dtype=np.float64)
    for i in range(nx):
        A[i, i] = -2.0 / (dx * dx)
        A[i, (i + 1) % nx] = 1.0 / (dx * dx)
        A[i, (i - 1) % nx] = 1.0 / (dx * dx)
    return A


def pressure_poisson_2d(
    nx: int,
    ny: int,
    rhs: np.ndarray,
) -> np.ndarray:
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

    b = rhs.ravel()
    b = b - np.mean(b)
    A[0, :] = 0.0
    A[0, 0] = 1.0
    b[0] = 0.0

    p = np.linalg.solve(A, b)
    return p.reshape(ny, nx)


def divergence_2d(ux: np.ndarray, uy: np.ndarray, dx: float, dy: float) -> np.ndarray:
    dudx = (np.roll(ux, -1, axis=1) - np.roll(ux, 1, axis=1)) / (2.0 * dx)
    dvdy = (np.roll(uy, -1, axis=0) - np.roll(uy, 1, axis=0)) / (2.0 * dy)
    return dudx + dvdy


def projection_step_2d(
    ux_star: np.ndarray,
    uy_star: np.ndarray,
    dt: float,
) -> dict[str, np.ndarray]:
    ny, nx = ux_star.shape
    dx = 1.0 / nx
    dy = 1.0 / ny
    div = divergence_2d(ux_star, uy_star, dx, dy)
    rhs = div / dt

    pressure = pressure_poisson_2d(nx, ny, rhs)

    dpdx = (np.roll(pressure, -1, axis=1) - np.roll(pressure, 1, axis=1)) / (2.0 * dx)
    dpdy = (np.roll(pressure, -1, axis=0) - np.roll(pressure, 1, axis=0)) / (2.0 * dy)

    ux = ux_star - dt * dpdx
    uy = uy_star - dt * dpdy

    div_after = divergence_2d(ux, uy, dx, dy)

    return {
        "ux": ux,
        "uy": uy,
        "pressure": pressure,
        "divergence_before": float(np.linalg.norm(div)),
        "divergence_after": float(np.linalg.norm(div_after)),
    }
