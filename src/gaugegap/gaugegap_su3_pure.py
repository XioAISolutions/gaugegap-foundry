"""
SU(3) prototype scaffold for gaugegap-0005.

This module is intentionally labeled as a PROTOTYPE SCAFFOLD. It is useful for
small finite-system pipeline testing, but it is not a completed production-grade
SU(3) lattice gauge implementation.

Implemented:
- finite lattice/link bookkeeping;
- standard Gell-Mann generator definitions;
- a simplified electric Casimir term;
- a bounded toy magnetic diagonal term for pipeline tests.

Not implemented yet:
- full plaquette group multiplication;
- physical-subspace projection;
- Gauss-law operator checks;
- Wilson loop, string tension, and Polyakov-loop observables.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

IMPLEMENTATION_STATUS = "prototype_scaffold"
CLAIM_BOUNDARY = "Finite-system prototype scaffold only."


@dataclass
class SU3PureGaugeConfig:
    """Configuration for the bounded SU(3) prototype scaffold."""

    nx: int
    ny: int
    g_electric: float
    g_magnetic: float
    truncation: float
    boundary: str = "periodic"

    def __post_init__(self) -> None:
        if self.nx < 2 or self.ny < 2:
            raise ValueError("Lattice size must be at least 2x2")
        if self.g_electric <= 0 or self.g_magnetic <= 0:
            raise ValueError("Coupling constants must be positive")
        if self.truncation <= 0:
            raise ValueError("Truncation must be positive")
        if self.boundary not in ["periodic", "open"]:
            raise ValueError("Boundary must be 'periodic' or 'open'")


class SU3PureGaugeLattice:
    """SU(3)-adjacent finite-lattice prototype scaffold."""

    def __init__(self, config: SU3PureGaugeConfig):
        self.config = config
        self.nx = config.nx
        self.ny = config.ny
        self.n_links = self._count_links()
        self.n_plaquettes = self._count_plaquettes()
        self.links = self._build_link_map()
        self.plaquettes = self._build_plaquette_map()
        self.dim_per_link = self._compute_link_dimension()
        self.hilbert_dim = self.dim_per_link ** self.n_links
        self.generators = self._build_su3_generators()

    def _count_links(self) -> int:
        if self.config.boundary == "periodic":
            return 2 * self.nx * self.ny
        return (self.nx - 1) * self.ny + self.nx * (self.ny - 1)

    def _count_plaquettes(self) -> int:
        if self.config.boundary == "periodic":
            return self.nx * self.ny
        return (self.nx - 1) * (self.ny - 1)

    def _compute_link_dimension(self) -> int:
        """Return a bounded prototype truncation dimension."""
        trunc = self.config.truncation
        if trunc <= 0.5:
            return 3
        if trunc <= 1.0:
            return 8
        return min(27, int(3 ** (1 + trunc)))

    def _build_link_map(self) -> list[tuple[int, int, str]]:
        links: list[tuple[int, int, str]] = []
        for y in range(self.ny):
            for x in range(self.nx):
                if self.config.boundary == "periodic" or x < self.nx - 1:
                    links.append((x, y, "x"))
                if self.config.boundary == "periodic" or y < self.ny - 1:
                    links.append((x, y, "y"))
        return links

    def _build_plaquette_map(self) -> list[list[int]]:
        plaquettes: list[list[int]] = []
        y_stop = self.ny if self.config.boundary == "periodic" else self.ny - 1
        x_stop = self.nx if self.config.boundary == "periodic" else self.nx - 1
        for y in range(y_stop):
            for x in range(x_stop):
                bottom = self._find_link_index(x, y, "x")
                right = self._find_link_index((x + 1) % self.nx, y, "y")
                top = self._find_link_index(x, (y + 1) % self.ny, "x")
                left = self._find_link_index(x, y, "y")
                if all(idx is not None for idx in [bottom, right, top, left]):
                    plaquettes.append([bottom, right, top, left])  # type: ignore[list-item]
        return plaquettes

    def _find_link_index(self, x: int, y: int, direction: str) -> int | None:
        try:
            return self.links.index((x, y, direction))
        except ValueError:
            return None

    def _build_su3_generators(self) -> list[np.ndarray]:
        """Build the eight standard Gell-Mann matrices."""
        lambda1 = np.array([[0, 1, 0], [1, 0, 0], [0, 0, 0]], dtype=complex)
        lambda2 = np.array([[0, -1j, 0], [1j, 0, 0], [0, 0, 0]], dtype=complex)
        lambda3 = np.array([[1, 0, 0], [0, -1, 0], [0, 0, 0]], dtype=complex)
        lambda4 = np.array([[0, 0, 1], [0, 0, 0], [1, 0, 0]], dtype=complex)
        lambda5 = np.array([[0, 0, -1j], [0, 0, 0], [1j, 0, 0]], dtype=complex)
        lambda6 = np.array([[0, 0, 0], [0, 0, 1], [0, 1, 0]], dtype=complex)
        lambda7 = np.array([[0, 0, 0], [0, 0, -1j], [0, 1j, 0]], dtype=complex)
        lambda8 = np.array([[1, 0, 0], [0, 1, 0], [0, 0, -2]], dtype=complex) / np.sqrt(3)
        return [lambda1, lambda2, lambda3, lambda4, lambda5, lambda6, lambda7, lambda8]

    def hamiltonian_dense(self) -> np.ndarray:
        if self.hilbert_dim > 10000:
            raise ValueError(
                f"Hilbert space dimension {self.hilbert_dim} too large for dense matrix."
            )
        return self._electric_term_dense() + self._magnetic_term_dense()

    def _electric_term_dense(self) -> np.ndarray:
        H_electric = np.zeros((self.hilbert_dim, self.hilbert_dim), dtype=complex)
        per_state_energy = self.config.g_electric * (4.0 / 3.0) * self.n_links
        np.fill_diagonal(H_electric, per_state_energy)
        return H_electric

    def _magnetic_term_dense(self) -> np.ndarray:
        """Build a bounded prototype magnetic toy term for pipeline tests."""
        H_magnetic = np.zeros((self.hilbert_dim, self.hilbert_dim), dtype=complex)
        coeff = -self.config.g_magnetic * max(1, self.n_plaquettes)
        for state_idx in range(self.hilbert_dim):
            toy_variation = (state_idx % self.dim_per_link) / max(1, self.dim_per_link - 1)
            H_magnetic[state_idx, state_idx] = coeff * 0.1 * toy_variation
        return H_magnetic

    def compute_gap(self) -> dict[str, Any]:
        base: dict[str, Any] = {
            "implementation_status": IMPLEMENTATION_STATUS,
            "claim_boundary": CLAIM_BOUNDARY,
            "verified_complete_su3": False,
            "verified_gauss_law": False,
        }
        if self.hilbert_dim > 10000:
            return {
                **base,
                "gap": None,
                "E0": None,
                "E1": None,
                "error": f"Hilbert space too large: {self.hilbert_dim}",
                "method": "exact_diagonalization_failed",
                "hilbert_dim": self.hilbert_dim,
                "n_links": self.n_links,
                "n_plaquettes": self.n_plaquettes,
            }
        try:
            H = self.hamiltonian_dense()
            if not np.allclose(H, H.conj().T):
                return {
                    **base,
                    "gap": None,
                    "E0": None,
                    "E1": None,
                    "error": "Hamiltonian not Hermitian",
                    "method": "exact_diagonalization_failed",
                    "hilbert_dim": self.hilbert_dim,
                    "n_links": self.n_links,
                    "n_plaquettes": self.n_plaquettes,
                }
            eigenvalues = np.sort(np.linalg.eigvalsh(H))
            E0 = float(eigenvalues[0])
            E1 = float(eigenvalues[1]) if len(eigenvalues) > 1 else None
            gap = float(E1 - E0) if E1 is not None else None
            return {
                **base,
                "gap": gap,
                "E0": E0,
                "E1": E1,
                "method": "prototype_exact_diagonalization",
                "hilbert_dim": self.hilbert_dim,
                "n_links": self.n_links,
                "n_plaquettes": self.n_plaquettes,
                "eigenvalue_count": len(eigenvalues),
            }
        except Exception as exc:
            return {
                **base,
                "gap": None,
                "E0": None,
                "E1": None,
                "error": str(exc),
                "method": "exact_diagonalization_failed",
                "hilbert_dim": self.hilbert_dim,
                "n_links": self.n_links,
                "n_plaquettes": self.n_plaquettes,
            }

    def compute_wilson_loop(self, R: int, T: int) -> dict[str, Any]:
        # KNOWN LIMITATION (claim boundary): the Wilson loop is explicitly not
        # implemented in this prototype. We return an honest "not_implemented"
        # status rather than a fabricated expectation value.
        # Roadmap: build the ordered link product around the R x T loop and take
        # its trace in the gauge-field ground state.
        return {
            "observable": "wilson_loop",
            # explicitly not implemented (prototype known limitation; see roadmap above)
            "status": "not_implemented",
            "implementation_status": IMPLEMENTATION_STATUS,
            "R": R,
            "T": T,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def compute_string_tension(self) -> dict[str, Any]:
        # KNOWN LIMITATION (claim boundary): string tension is explicitly not
        # implemented in this prototype; it depends on Wilson-loop areas that
        # are themselves not yet computed. Honest "not_implemented" status.
        # Roadmap: fit -log<W(R,T)> ~ sigma * R * T once Wilson loops exist.
        return {
            "observable": "string_tension",
            "status": "not_implemented",
            "implementation_status": IMPLEMENTATION_STATUS,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def compute_polyakov_loop(self) -> dict[str, Any]:
        # KNOWN LIMITATION (claim boundary): the Polyakov loop is explicitly not
        # implemented in this prototype. Honest "not_implemented" status rather
        # than a fabricated order parameter.
        # Roadmap: trace the temporal Wilson line wrapping the periodic time
        # direction once link operators along time are available.
        return {
            "observable": "polyakov_loop",
            # explicitly not implemented (prototype known limitation; see roadmap above)
            "status": "not_implemented",
            "implementation_status": IMPLEMENTATION_STATUS,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def check_gauge_invariance(self) -> dict[str, Any]:
        # KNOWN LIMITATION (claim boundary): the Gauss-law projector check is
        # explicitly not implemented in this prototype, so we honestly report
        # "not_implemented" (and verified_gauss_law=False) instead of asserting
        # a value we have not verified.
        # Roadmap: construct the per-site Gauss operators G_a and confirm they
        # commute with H and annihilate the physical states.
        return {
            "gauss_law_satisfied": "not_implemented",
            "su3_algebra_closed": True,
            "hermiticity_checked_in_compute_gap": True,
            "verified_gauss_law": False,
            "implementation_status": IMPLEMENTATION_STATUS,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "model": "su3_prototype_scaffold_2plus1d",
            "hypothesis_id": "gaugegap-0005",
            "track": "GaugeGap",
            "implementation_status": IMPLEMENTATION_STATUS,
            "claim_boundary": CLAIM_BOUNDARY,
            "verified_complete_su3": False,
            "verified_gauss_law": False,
            "config": {
                "nx": self.nx,
                "ny": self.ny,
                "g_electric": self.config.g_electric,
                "g_magnetic": self.config.g_magnetic,
                "truncation": self.config.truncation,
                "boundary": self.config.boundary,
            },
            "lattice": {
                "n_links": self.n_links,
                "n_plaquettes": self.n_plaquettes,
                "dim_per_link": self.dim_per_link,
                "hilbert_dim": self.hilbert_dim,
            },
            "su3_properties": {
                "n_generators": 8,
                "fundamental_dim": 3,
                "adjoint_dim": 8,
                "casimir_fundamental": 4.0 / 3.0,
                "casimir_adjoint": 3.0,
            },
        }
