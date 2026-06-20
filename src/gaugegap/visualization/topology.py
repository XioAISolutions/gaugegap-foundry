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


def cartan_matrix_AN(N: int) -> np.ndarray:
    """Cartan matrix of A_{N-1} = su(N): tridiagonal (2 on diag, -1 off)."""
    if N < 2:
        raise ValueError("N must be >= 2")
    r = N - 1
    C = 2 * np.eye(r, dtype=int)
    for i in range(r - 1):
        C[i, i + 1] = -1
        C[i + 1, i] = -1
    return C


def dynkin_diagram_AN(N: int) -> dict:
    """A_{N-1} Dynkin diagram: N-1 nodes in a line, single bonds between neighbours."""
    r = N - 1
    return {
        "type": f"A{r}",
        "group": f"su({N})",
        "nodes": list(range(1, r + 1)),
        "bonds": [(i, i + 1) for i in range(1, r)],
        "cartan_matrix": cartan_matrix_AN(N).tolist(),
    }
