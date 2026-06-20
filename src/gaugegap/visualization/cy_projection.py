"""Calabi-Yau (Fermat) cross-section as a 2D projection of a higher-dim surface.

The degree-``n`` Fermat hypersurface ``z1^n + z2^n = 1`` (a complex curve, real
2-surface living in C^2 = R^4) is the standard "Calabi-Yau cross-section" image
(Hanson's construction). We compute its ``n x n`` patches exactly, project
R^4 -> R^3 with a mixing angle, then orthographically to 2D for a figure.

This is a faithful projection of an exact algebraic surface — the same
flatten-the-higher-dimensional-object idea as an SU(3) weight diagram, rendered
honestly. The full string-theory Calabi-Yau threefold (real dim 6) is not depicted
here; this is the classic 2-surface cross-section used to visualize it.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np


@dataclass
class CYPatch:
    k1: int
    k2: int
    grid3d: np.ndarray  # (n_grid, n_grid, 3) projected to R^3


def fermat_patches(n: int = 5, n_grid: int = 14, proj_alpha: float = np.pi / 4,
                   eta_max: float = 1.0) -> List[CYPatch]:
    """Exact patches of ``z1^n + z2^n = 1`` projected R^4 -> R^3.

    ``z1 = e^{2πi k1/n} cos(ξ+iη)^{2/n}``, ``z2 = e^{2πi k2/n} sin(ξ+iη)^{2/n}``
    so ``z1^n + z2^n = cos^2 + sin^2 = 1``. R^4 -> R^3 via
    ``(Re z1, Re z2, Im z1 cos α + Im z2 sin α)``.
    """
    xi = np.linspace(0.0, np.pi / 2, n_grid)
    eta = np.linspace(-eta_max, eta_max, n_grid)
    XI, ETA = np.meshgrid(xi, eta, indexing="ij")
    w = XI + 1j * ETA
    cos_part = np.cos(w) ** (2.0 / n)
    sin_part = np.sin(w) ** (2.0 / n)
    patches: List[CYPatch] = []
    for k1 in range(n):
        for k2 in range(n):
            z1 = np.exp(2j * np.pi * k1 / n) * cos_part
            z2 = np.exp(2j * np.pi * k2 / n) * sin_part
            x = z1.real
            y = z2.real
            z = z1.imag * np.cos(proj_alpha) + z2.imag * np.sin(proj_alpha)
            grid = np.stack([x, y, z], axis=-1)
            patches.append(CYPatch(k1=k1, k2=k2, grid3d=grid))
    return patches


def orthographic(points3d: np.ndarray, yaw: float = 0.6, pitch: float = 0.5
                 ) -> np.ndarray:
    """Rotate a (..., 3) array and drop the depth axis -> (..., 2)."""
    cy, sy = np.cos(yaw), np.sin(yaw)
    cp, sp = np.cos(pitch), np.sin(pitch)
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    rot = rx @ ry
    p = points3d @ rot.T
    return p[..., :2]
