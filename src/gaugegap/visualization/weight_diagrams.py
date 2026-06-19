"""Weight diagrams and root systems as exact 2D projections of representation space.

An SU(3) irrep lives in a higher-dimensional representation space, but its *weights*
are vectors in the rank-2 Cartan subalgebra — so the familiar octet hexagon /
decuplet triangle are genuine 2D projections (onto the (T3, Y) plane) of that
structure, with multiplicities computed exactly by **Freudenthal's recursion**.
No mysticism: these are the real weight lattices of su(3) representation theory.

Coordinates: weights are realised in the sum-zero subspace of R^3 (so dot products
are the standard Killing form up to scale), then projected to the physics plane
``T3 = (a-b)/2``, ``Y = (a+b-2c)/3``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np

# A2 (su(3)) data in the sum-zero subspace of R^3.
_ALPHA1 = np.array([1.0, -1.0, 0.0])   # simple root
_ALPHA2 = np.array([0.0, 1.0, -1.0])   # simple root
_POS_ROOTS = [_ALPHA1, _ALPHA2, _ALPHA1 + _ALPHA2]
_OMEGA1 = np.array([2.0, -1.0, -1.0]) / 3.0   # fundamental weights
_OMEGA2 = np.array([1.0, 1.0, -2.0]) / 3.0
_RHO = _OMEGA1 + _OMEGA2


def su3_dimension(p: int, q: int) -> int:
    """Dimension of the su(3) irrep with Dynkin labels (p, q)."""
    return (p + 1) * (q + 1) * (p + q + 2) // 2


def project_t3_y(w: np.ndarray) -> Tuple[float, float]:
    """Project a sum-zero R^3 weight to the physics (T3, Y) plane."""
    a, b, c = w
    return ((a - b) / 2.0, (a + b - 2 * c) / 3.0)


def su3_weights(p: int, q: int) -> List[Dict]:
    """Exact weights of the su(3) irrep (p, q) with Freudenthal multiplicities.

    Returns a list of ``{"t3", "y", "mult", "r3"}`` dicts; the multiplicities sum
    to :func:`su3_dimension`.
    """
    Lam = p * _OMEGA1 + q * _OMEGA2
    Lam_rho_sq = float(np.dot(Lam + _RHO, Lam + _RHO))

    # Candidate weights mu = Lam - i*alpha1 - j*alpha2 on a generous grid; the
    # recursion assigns mult 0 outside the actual weight diagram.
    bound = 2 * (p + q) + 2
    mults: Dict[Tuple[int, int], float] = {}
    order = sorted(((i, j) for i in range(bound + 1) for j in range(bound + 1)),
                   key=lambda ij: ij[0] + ij[1])
    for (i, j) in order:
        if i == 0 and j == 0:
            mults[(0, 0)] = 1.0
            continue
        mu = Lam - i * _ALPHA1 - j * _ALPHA2
        denom = Lam_rho_sq - float(np.dot(mu + _RHO, mu + _RHO))
        if denom <= 1e-9:
            mults[(i, j)] = 0.0
            continue
        acc = 0.0
        for alpha in _POS_ROOTS:
            k = 1
            while True:
                nu = mu + k * alpha
                # nu = Lam - (i - k*a_i) alpha1 - (j - k*a_j) alpha2
                ai = i - k * (1 if (alpha is _ALPHA1 or alpha is _POS_ROOTS[2]) else 0)
                aj = j - k * (1 if (alpha is _ALPHA2 or alpha is _POS_ROOTS[2]) else 0)
                if ai < 0 or aj < 0:
                    break
                m = mults.get((ai, aj), 0.0)
                if m:
                    acc += m * float(np.dot(nu, alpha))
                k += 1
        mults[(i, j)] = max(0.0, 2.0 * acc / denom)

    weights: List[Dict] = []
    for (i, j), m in mults.items():
        mi = int(round(m))
        if mi <= 0:
            continue
        w = Lam - i * _ALPHA1 - j * _ALPHA2
        t3, y = project_t3_y(w)
        weights.append({"t3": t3, "y": y, "mult": mi, "r3": tuple(float(x) for x in w)})
    weights.sort(key=lambda d: (round(d["y"], 6), round(d["t3"], 6)))
    return weights


def su3_root_system() -> List[Dict]:
    """The 6 roots of su(3) (A2) projected to the (T3, Y) plane, plus origin."""
    roots = _POS_ROOTS + [-r for r in _POS_ROOTS]
    out = []
    for r in roots:
        t3, y = project_t3_y(r)
        out.append({"t3": t3, "y": y, "r3": tuple(float(x) for x in r)})
    out.sort(key=lambda d: np.arctan2(d["y"], d["t3"]))
    return out


# Named representations for convenience.
NAMED_IRREPS = {
    "fundamental": (1, 0),   # 3
    "antifundamental": (0, 1),  # 3-bar
    "adjoint": (1, 1),       # 8 (octet)
    "sextet": (2, 0),        # 6
    "decuplet": (3, 0),      # 10
}
