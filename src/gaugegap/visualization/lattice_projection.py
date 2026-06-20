"""Lattice geometry and a Wilson loop, as a 3D->2D projection.

A finite cubic lattice of sites and links (the spacetime grid that lattice gauge
theory discretises) with a highlighted **Wilson loop** — a closed rectangular path
of links whose ordered product is the gauge-invariant Wilson-loop observable.

This is purely the *geometry* of the lattice and the loop, projected R^3 -> R^2;
it carries no dynamical/physics claim. It visualises how a higher-dimensional
lattice configuration flattens to an observable 2D shadow.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np


@dataclass
class Lattice:
    sites: np.ndarray            # (n_sites, 3) integer coordinates
    links: List[Tuple[int, int]]  # index pairs (nearest-neighbour bonds)
    dims: Tuple[int, int, int]

    def index(self, x: int, y: int, z: int) -> int:
        Lx, Ly, Lz = self.dims
        return (x * Ly + y) * Lz + z


def cubic_lattice(Lx: int = 3, Ly: int = 3, Lz: int = 3) -> Lattice:
    """A finite cubic lattice with nearest-neighbour links."""
    sites = np.array([[x, y, z] for x in range(Lx) for y in range(Ly)
                      for z in range(Lz)], dtype=float)
    dims = (Lx, Ly, Lz)
    lat = Lattice(sites=sites, links=[], dims=dims)
    links: List[Tuple[int, int]] = []
    for x in range(Lx):
        for y in range(Ly):
            for z in range(Lz):
                i = lat.index(x, y, z)
                if x + 1 < Lx:
                    links.append((i, lat.index(x + 1, y, z)))
                if y + 1 < Ly:
                    links.append((i, lat.index(x, y + 1, z)))
                if z + 1 < Lz:
                    links.append((i, lat.index(x, y, z + 1)))
    lat.links = links
    return lat


def wilson_loop(lat: Lattice, origin=(0, 0, 0), R: int = 2, T: int = 2,
                plane: str = "xy") -> List[int]:
    """A closed rectangular Wilson loop (R x T) on a coordinate plane.

    Returns the ordered site indices around the loop (last == first).
    """
    ox, oy, oz = origin
    ax = {"xy": (0, 1), "xz": (0, 2), "yz": (1, 2)}[plane]
    corners_2d = [(0, 0), (R, 0), (R, T), (0, T), (0, 0)]
    path: List[int] = []
    for (u, v) in corners_2d:
        c = [ox, oy, oz]
        c[ax[0]] += u
        c[ax[1]] += v
        path.append(lat.index(int(c[0]), int(c[1]), int(c[2])))
    # densify edges so the loop follows lattice links (unit steps), without
    # duplicating the shared corner between consecutive segments
    start = lat.sites[path[0]].astype(int)
    dense: List[int] = [lat.index(*start)]
    for a, b in zip(path[:-1], path[1:]):
        pa = lat.sites[a].astype(int)
        pb = lat.sites[b].astype(int)
        step = np.sign(pb - pa).astype(int)
        cur = pa.copy()
        while not np.array_equal(cur, pb):
            cur = cur + step
            dense.append(lat.index(*cur))
    return dense


def project(points3d: np.ndarray, yaw: float = 0.6, pitch: float = 0.5) -> np.ndarray:
    """Orthographic R^3 -> R^2 (rotate then drop depth)."""
    cy, sy = np.cos(yaw), np.sin(yaw)
    cp, sp = np.cos(pitch), np.sin(pitch)
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    return (points3d @ (rx @ ry).T)[..., :2]
