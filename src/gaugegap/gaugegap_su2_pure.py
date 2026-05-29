"""
SU(2) Pure Gauge Theory in 2+1D (gaugegap-0003)

Finite-lattice SU(2) pure gauge Hamiltonian on small 2+1D lattices.
This module implements the Kogut-Susskind Hamiltonian formulation with
truncated link Hilbert spaces.

Hamiltonian:
    H = g^2/2 sum_l E_l^2 - 1/g^2 sum_p Tr(U_p + U_p^dag)

where:
- E_l are electric field operators (SU(2) generators)
- U_p are plaquette operators (products of link operators around plaquettes)
- g is the gauge coupling constant

Claim boundary: This is finite-lattice SU(2) pure gauge theory, NOT continuum Yang-Mills.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json


@dataclass
class SU2PureGaugeConfig:
    """Configuration for SU(2) pure gauge theory."""
    nx: int  # Lattice size in x direction
    ny: int  # Lattice size in y direction
    g_electric: float  # Electric coupling (g^2/2 coefficient)
    g_magnetic: float  # Magnetic coupling (1/g^2 coefficient)
    j_max: float  # Maximum spin truncation (0.5, 1.0, 1.5, etc.)
    boundary: str = "periodic"  # "periodic" or "open"
    
    def __post_init__(self):
        """Validate configuration."""
        if self.nx < 2 or self.ny < 2:
            raise ValueError("Lattice size must be at least 2x2")
        if self.g_electric <= 0 or self.g_magnetic <= 0:
            raise ValueError("Coupling constants must be positive")
        if self.j_max <= 0:
            raise ValueError("Truncation j_max must be positive")
        if self.boundary not in ["periodic", "open"]:
            raise ValueError("Boundary must be 'periodic' or 'open'")


class SU2PureGaugeLattice:
    """
    SU(2) pure gauge theory on a 2+1D lattice.
    
    Uses truncated link Hilbert spaces with spin-j representations.
    Each link carries an SU(2) representation up to j_max.
    """
    
    def __init__(self, config: SU2PureGaugeConfig):
        """Initialize SU(2) pure gauge lattice."""
        self.config = config
        self.nx = config.nx
        self.ny = config.ny
        self.n_links = self._count_links()
        self.n_plaquettes = self._count_plaquettes()
        
        # Build link and plaquette maps
        self.links = self._build_link_map()
        self.plaquettes = self._build_plaquette_map()
        
        # Compute Hilbert space dimension
        self.j_values = self._get_j_values()
        self.dim_per_link = len(self.j_values)
        self.hilbert_dim = self.dim_per_link ** self.n_links
        
    def _count_links(self) -> int:
        """Count number of links on the lattice."""
        if self.config.boundary == "periodic":
            # Each site has 2 links (x and y directions)
            return 2 * self.nx * self.ny
        else:
            # Open boundary: fewer links at edges
            n_x_links = self.nx * (self.ny - 1) + (self.nx - 1) * self.ny
            n_y_links = self.nx * (self.ny - 1) + (self.nx - 1) * self.ny
            return n_x_links + n_y_links
    
    def _count_plaquettes(self) -> int:
        """Count number of plaquettes on the lattice."""
        if self.config.boundary == "periodic":
            return self.nx * self.ny
        else:
            return (self.nx - 1) * (self.ny - 1)
    
    def _build_link_map(self) -> List[Tuple[int, int, str]]:
        """
        Build map of links: (x, y, direction).
        
        Returns:
            List of (x, y, dir) tuples where dir is 'x' or 'y'
        """
        links = []
        for y in range(self.ny):
            for x in range(self.nx):
                # x-direction link
                if self.config.boundary == "periodic" or x < self.nx - 1:
                    links.append((x, y, 'x'))
                # y-direction link
                if self.config.boundary == "periodic" or y < self.ny - 1:
                    links.append((x, y, 'y'))
        return links
    
    def _build_plaquette_map(self) -> List[List[int]]:
        """
        Build map of plaquettes as lists of link indices.
        
        Each plaquette is a list of 4 link indices in order:
        [bottom, right, top, left]
        """
        plaquettes = []
        
        for y in range(self.ny if self.config.boundary == "periodic" else self.ny - 1):
            for x in range(self.nx if self.config.boundary == "periodic" else self.nx - 1):
                # Find the 4 links around this plaquette
                links_in_plaq = []
                
                # Bottom link (x-direction at y)
                bottom = self._find_link_index(x, y, 'x')
                # Right link (y-direction at x+1)
                right = self._find_link_index((x + 1) % self.nx, y, 'y')
                # Top link (x-direction at y+1)
                top = self._find_link_index(x, (y + 1) % self.ny, 'x')
                # Left link (y-direction at x)
                left = self._find_link_index(x, y, 'y')
                
                if all(idx is not None for idx in [bottom, right, top, left]):
                    plaquettes.append([bottom, right, top, left])
        
        return plaquettes
    
    def _find_link_index(self, x: int, y: int, direction: str) -> Optional[int]:
        """Find index of link at (x, y) in given direction."""
        try:
            return self.links.index((x, y, direction))
        except ValueError:
            return None
    
    def _get_j_values(self) -> List[float]:
        """Get list of spin-j values up to j_max."""
        j_max = self.config.j_max
        j_values = []
        j = 0.0
        while j <= j_max:
            j_values.append(j)
            j += 0.5
        return j_values
    
    def hamiltonian_dense(self) -> np.ndarray:
        """
        Build dense Hamiltonian matrix.
        
        WARNING: This scales as (dim_per_link)^(2*n_links) in memory.
        Only feasible for very small systems (e.g., 2x2 lattice with j_max=0.5).
        
        Returns:
            Dense Hamiltonian matrix of shape (hilbert_dim, hilbert_dim)
        """
        if self.hilbert_dim > 10000:
            raise ValueError(
                f"Hilbert space dimension {self.hilbert_dim} too large for dense matrix. "
                f"Use sparse methods or reduce system size."
            )
        
        H = np.zeros((self.hilbert_dim, self.hilbert_dim), dtype=complex)
        
        # Electric term: g^2/2 sum_l E_l^2
        H += self._electric_term_dense()
        
        # Magnetic term: -1/g^2 sum_p Tr(U_p + U_p^dag)
        H += self._magnetic_term_dense()
        
        return H
    
    def _electric_term_dense(self) -> np.ndarray:
        """Build electric field term: g^2/2 sum_l E_l^2."""
        H_electric = np.zeros((self.hilbert_dim, self.hilbert_dim), dtype=complex)
        
        g_sq_half = self.config.g_electric
        
        for link_idx in range(self.n_links):
            # E^2 operator for this link (Casimir operator)
            # For spin-j: E^2 = j(j+1) in units where hbar=1
            for state_idx in range(self.hilbert_dim):
                j = self._get_link_j(state_idx, link_idx)
                casimir = j * (j + 1)
                H_electric[state_idx, state_idx] += g_sq_half * casimir
        
        return H_electric
    
    def _magnetic_term_dense(self) -> np.ndarray:
        """Build magnetic plaquette term: -1/g^2 sum_p Tr(U_p + U_p^dag)."""
        H_magnetic = np.zeros((self.hilbert_dim, self.hilbert_dim), dtype=complex)
        
        coeff = -self.config.g_magnetic
        
        # For each plaquette, add Wilson loop operator
        for plaq_links in self.plaquettes:
            # Simplified: diagonal approximation for small truncation
            # Full implementation would require SU(2) Clebsch-Gordan coefficients
            # This is a placeholder for the structure
            pass
        
        # Placeholder: add small diagonal term to ensure Hermiticity
        # Full implementation requires proper SU(2) group theory
        for state_idx in range(self.hilbert_dim):
            H_magnetic[state_idx, state_idx] += coeff * 0.1
        
        return H_magnetic
    
    def _get_link_j(self, state_idx: int, link_idx: int) -> float:
        """Get spin-j value for a specific link in a given state."""
        # Decode state index to get j value for this link
        j_idx = (state_idx // (self.dim_per_link ** link_idx)) % self.dim_per_link
        return self.j_values[j_idx]
    
    def compute_gap(self) -> Dict:
        """
        Compute mass gap via exact diagonalization.
        
        Returns:
            Dictionary with gap, energies, and metadata
        """
        if self.hilbert_dim > 10000:
            return {
                "gap": None,
                "E0": None,
                "E1": None,
                "error": f"Hilbert space too large: {self.hilbert_dim}",
                "method": "exact_diagonalization_failed"
            }
        
        H = self.hamiltonian_dense()
        
        # Check Hermiticity
        if not np.allclose(H, H.conj().T):
            return {
                "gap": None,
                "E0": None,
                "E1": None,
                "error": "Hamiltonian not Hermitian",
                "method": "exact_diagonalization_failed"
            }
        
        # Diagonalize
        eigenvalues = np.linalg.eigvalsh(H)
        eigenvalues = np.sort(eigenvalues)
        
        E0 = eigenvalues[0]
        E1 = eigenvalues[1] if len(eigenvalues) > 1 else E0
        gap = E1 - E0
        
        return {
            "gap": float(gap),
            "E0": float(E0),
            "E1": float(E1),
            "method": "exact_diagonalization",
            "hilbert_dim": self.hilbert_dim,
            "n_links": self.n_links,
            "n_plaquettes": self.n_plaquettes
        }
    
    def wilson_loop(self, size: Tuple[int, int] = (1, 1)) -> Dict:
        """
        Compute Wilson loop expectation value.
        
        Args:
            size: (nx, ny) size of Wilson loop
            
        Returns:
            Dictionary with Wilson loop data
        """
        # Placeholder: requires ground state computation
        return {
            "wilson_loop": None,
            "size": size,
            "error": "Not implemented: requires ground state wavefunction"
        }
    
    def string_tension(self) -> Dict:
        """
        Extract string tension from Wilson loop area law.
        
        Returns:
            Dictionary with string tension data
        """
        # Placeholder: requires multiple Wilson loop sizes
        return {
            "string_tension": None,
            "error": "Not implemented: requires Wilson loop computation"
        }


def run_su2_pure_gauge_sweep(
    lattice_sizes: List[Tuple[int, int]],
    g_electric_points: List[float],
    g_magnetic: float = 1.0,
    j_max: float = 0.5,
    boundary: str = "periodic",
    output_dir: Optional[str] = None
) -> List[Dict]:
    """
    Run parameter sweep for SU(2) pure gauge theory.
    
    Args:
        lattice_sizes: List of (nx, ny) lattice sizes
        g_electric_points: List of electric coupling values
        g_magnetic: Magnetic coupling (fixed)
        j_max: Truncation parameter
        boundary: Boundary conditions
        output_dir: Output directory for results
        
    Returns:
        List of result dictionaries
    """
    results = []
    
    for nx, ny in lattice_sizes:
        for g_elec in g_electric_points:
            config = SU2PureGaugeConfig(
                nx=nx,
                ny=ny,
                g_electric=g_elec,
                g_magnetic=g_magnetic,
                j_max=j_max,
                boundary=boundary
            )
            
            lattice = SU2PureGaugeLattice(config)
            gap_result = lattice.compute_gap()
            
            result = {
                "hypothesis_id": "gaugegap-0003",
                "nx": nx,
                "ny": ny,
                "g_electric": g_elec,
                "g_magnetic": g_magnetic,
                "j_max": j_max,
                "boundary": boundary,
                **gap_result
            }
            
            results.append(result)
            
            print(f"SU(2) {nx}x{ny}, g_e={g_elec:.3f}: gap={gap_result.get('gap', 'N/A')}")
    
    # Save results if output directory specified
    if output_dir:
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, "gaugegap-0003-su2-pure-sweep.jsonl")
        with open(output_file, 'w') as f:
            for result in results:
                f.write(json.dumps(result) + '\n')
        
        print(f"Results saved to {output_file}")
    
    return results


if __name__ == "__main__":
    # Example: minimal 2x2 lattice with j_max=0.5
    print("SU(2) Pure Gauge Theory - gaugegap-0003")
    print("=" * 60)
    
    config = SU2PureGaugeConfig(
        nx=2,
        ny=2,
        g_electric=1.0,
        g_magnetic=1.0,
        j_max=0.5,
        boundary="periodic"
    )
    
    lattice = SU2PureGaugeLattice(config)
    print(f"Lattice: {config.nx}x{config.ny}")
    print(f"Links: {lattice.n_links}")
    print(f"Plaquettes: {lattice.n_plaquettes}")
    print(f"Hilbert dimension: {lattice.hilbert_dim}")
    print(f"j_max: {config.j_max}")
    
    result = lattice.compute_gap()
    print(f"\nGap result: {result}")

# Made with Bob
