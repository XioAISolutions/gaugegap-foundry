"""Exact topological / Lie-algebra data: Calabi-Yau Hodge diamonds and A_{N-1}
Cartan matrices / Dynkin diagrams.

These are standard, exact invariants (no mysticism, no fitting):

- A Calabi-Yau threefold's **Hodge diamond** is fixed by two numbers (h^{1,1},
  h^{2,1}); the Fermat **quintic** has (1, 101), Euler characteristic chi = -200.
  We build the full diamond, verify its Hodge symmetries, and compute the Euler
  characteristic and Betti numbers.
- The su(N) (A_{N-1}) **Cartan matrix** and **Dynkin diagram** encode the simple-
  root geometry behind the weight diagrams.

CLAIM BOUNDARY: textbook exact invariants. The "number of generations ~ |chi|/2"
remark is the standard heuristic from string compactification, labelled as such,
not a physics result of this repo.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np


@dataclass
class HodgeDiamond:
    name: str
    complex_dim: int
    h: Dict  # (p, q) -> h^{p,q}

    def euler_characteristic(self) -> int:
        return int(sum((-1) ** (p + q) * v for (p, q), v in self.h.items()))

    def betti_numbers(self) -> List[int]:
        n = 2 * self.complex_dim
        b = [0] * (n + 1)
        for (p, q), v in self.h.items():
            b[p + q] += v
        return b

    def hodge_symmetric(self) -> bool:
        """Hodge symmetry h^{p,q}=h^{q,p} and (Calabi-Yau) Serre duality
        h^{p,q}=h^{n-p,n-q}."""
        n = self.complex_dim
        for (p, q), v in self.h.items():
            if self.h.get((q, p), 0) != v:
                return False
            if self.h.get((n - p, n - q), 0) != v:
                return False
        return True

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "complex_dim": self.complex_dim,
            "hodge_numbers": {f"{p},{q}": v for (p, q), v in sorted(self.h.items())},
            "euler_characteristic": self.euler_characteristic(),
            "betti_numbers": self.betti_numbers(),
            "hodge_symmetric": self.hodge_symmetric(),
        }


def calabi_yau_threefold(h11: int, h21: int, name: str = "CY3") -> HodgeDiamond:
    """Hodge diamond of a Calabi-Yau threefold from (h^{1,1}, h^{2,1})."""
    h = {}
    # corners and diagonal of a CY3 diamond (h^{0,0}=h^{3,0}=1, etc.)
    h[(0, 0)] = 1; h[(3, 3)] = 1
    h[(3, 0)] = 1; h[(0, 3)] = 1            # holomorphic 3-form (CY)
    h[(1, 1)] = h11; h[(2, 2)] = h11
    h[(2, 1)] = h21; h[(1, 2)] = h21
    return HodgeDiamond(name=name, complex_dim=3, h=h)


def fermat_quintic_hodge() -> HodgeDiamond:
    """The quintic threefold in CP^4: h^{1,1}=1, h^{2,1}=101, chi=-200."""
    return calabi_yau_threefold(1, 101, name="Fermat quintic (CP^4)")


def mirror_threefold(diamond: HodgeDiamond) -> HodgeDiamond:
    """Mirror of a CY threefold: swap h^{1,1} <-> h^{2,1} (Euler char flips sign).

    Mirror symmetry exchanges the complex-structure and Kähler moduli; for a CY3
    this swaps the two free Hodge numbers and sends chi -> -chi.
    """
    if diamond.complex_dim != 3:
        raise ValueError("mirror_threefold is defined here for CY threefolds")
    h11 = diamond.h.get((1, 1), 0)
    h21 = diamond.h.get((2, 1), 0)
    return calabi_yau_threefold(h21, h11, name=f"mirror of {diamond.name}")


def is_mirror_pair(a: HodgeDiamond, b: HodgeDiamond) -> bool:
    """True iff b is a's CY3 mirror: swapped (h11,h21) and chi(b) == -chi(a)."""
    if a.complex_dim != 3 or b.complex_dim != 3:
        return False
    return (a.h.get((1, 1), 0) == b.h.get((2, 1), 0)
            and a.h.get((2, 1), 0) == b.h.get((1, 1), 0)
            and a.euler_characteristic() == -b.euler_characteristic())


# --- Finite-type Cartan matrices & Dynkin diagrams (A,B,C,D,E,F,G) ------------

def _dynkin_bonds(typ: str, n: int) -> List[tuple]:
    """Bonds as (i, j, mult) with 0-indexed simple roots; mult in {1,2,3}."""
    typ = typ.upper()
    if typ == "A":
        return [(i, i + 1, 1) for i in range(n - 1)]
    if typ in ("B", "C"):
        return [(i, i + 1, 1) for i in range(n - 2)] + [(n - 2, n - 1, 2)]
    if typ == "D":
        if n < 4:
            raise ValueError("D_n requires n >= 4")
        return [(i, i + 1, 1) for i in range(n - 2)] + [(n - 3, n - 1, 1)]
    if typ == "E":
        if n not in (6, 7, 8):
            raise ValueError("E_n requires n in {6,7,8}")
        return [(i, i + 1, 1) for i in range(n - 2)] + [(2, n - 1, 1)]
    if typ == "F":
        if n != 4:
            raise ValueError("F requires n == 4")
        return [(0, 1, 1), (1, 2, 2), (2, 3, 1)]
    if typ == "G":
        if n != 2:
            raise ValueError("G requires n == 2")
        return [(0, 1, 3)]
    raise ValueError(f"unknown Cartan type {typ!r}")


def cartan_matrix(typ: str, n: int) -> np.ndarray:
    """Cartan matrix of a finite-type simple Lie algebra (A,B,C,D,E,F,G)."""
    C = 2 * np.eye(n, dtype=int)
    for (i, j, m) in _dynkin_bonds(typ, n):
        # off-diagonals multiply to m (B/C/F/G asymmetry; arrow long->short)
        C[i, j] = -1
        C[j, i] = -m
    # For B/C the conventional arrow direction differs but the matrix is valid
    # finite-type either way; det is transpose-invariant.
    return C


# Known Cartan determinants (index of the root lattice in the weight lattice).
_CARTAN_DET = {"A": lambda n: n + 1, "B": lambda n: 2, "C": lambda n: 2,
               "D": lambda n: 4, "E": lambda n: {6: 3, 7: 2, 8: 1}[n],
               "F": lambda n: 1, "G": lambda n: 1}


def cartan_determinant(typ: str, n: int) -> int:
    """The known determinant of the Cartan matrix (for verification)."""
    return _CARTAN_DET[typ.upper()](n)


def _symmetrized(typ: str, n: int) -> np.ndarray:
    """Symmetrise the Cartan matrix via the positive diagonal D with D_i*C_ij =
    D_j*C_ji (exists because Dynkin diagrams are trees). For a finite-type algebra
    D*C is symmetric positive-definite."""
    C = cartan_matrix(typ, n).astype(float)
    bonds = _dynkin_bonds(typ, n)
    D = [None] * n
    D[0] = 1.0
    # propagate along the tree: bond (i,j,m) has C[i,j]=-1, C[j,i]=-m -> D_i=m*D_j
    changed = True
    adj = {i: [] for i in range(n)}
    for (i, j, m) in bonds:
        adj[i].append((j, m)); adj[j].append((i, m))
    stack = [0]
    while stack:
        u = stack.pop()
        for (i, j, m) in bonds:
            if i == u and D[j] is None:
                D[j] = D[u] / m; stack.append(j)
            elif j == u and D[i] is None:
                D[i] = D[u] * m; stack.append(i)
    Dv = np.diag([d if d is not None else 1.0 for d in D])
    return Dv @ C


def dynkin_diagram(typ: str, n: int) -> dict:
    """Dynkin-diagram data for a finite-type algebra: nodes + bonds (with
    multiplicity) + the Cartan matrix and its (verified) determinant."""
    bonds = _dynkin_bonds(typ, n)
    C = cartan_matrix(typ, n)
    S = _symmetrized(typ, n)
    return {
        "type": f"{typ.upper()}{n}",
        "rank": n,
        "nodes": list(range(n)),
        "bonds": [{"i": i, "j": j, "mult": m} for (i, j, m) in bonds],
        "cartan_matrix": C.tolist(),
        "determinant": int(round(float(np.linalg.det(C)))),
        "known_determinant": cartan_determinant(typ, n),
        "positive_definite": bool(np.all(np.linalg.eigvalsh(S) > 1e-9)),
    }


def cartan_matrix_AN(N: int) -> np.ndarray:
    """Cartan matrix of A_{N-1} = su(N) (kept for the weight-diagram code)."""
    if N < 2:
        raise ValueError("N must be >= 2")
    return cartan_matrix("A", N - 1)


def dynkin_diagram_AN(N: int) -> dict:
    """A_{N-1} Dynkin diagram (1-indexed nodes) for su(N)."""
    r = N - 1
    return {
        "type": f"A{r}",
        "group": f"su({N})",
        "nodes": list(range(1, r + 1)),
        "bonds": [(i, i + 1) for i in range(1, r)],
        "cartan_matrix": cartan_matrix_AN(N).tolist(),
    }

