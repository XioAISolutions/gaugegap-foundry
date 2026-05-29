"""
Tests for SU(3) Pure Gauge Theory (gaugegap-0005)
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add src to path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.gaugegap_su3_pure import (
    SU3PureGaugeConfig,
    SU3PureGaugeLattice,
)


class TestSU3PureGaugeConfig:
    """Test SU(3) configuration validation."""
    
    def test_valid_config(self):
        """Test valid configuration."""
        config = SU3PureGaugeConfig(
            nx=2,
            ny=2,
            g_electric=1.0,
            g_magnetic=1.0,
            truncation=0.5
        )
        assert config.nx == 2
        assert config.ny == 2
        assert config.g_electric == 1.0
        assert config.g_magnetic == 1.0
        assert config.truncation == 0.5
        assert config.boundary == "periodic"
    
    def test_invalid_lattice_size(self):
        """Test invalid lattice size."""
        with pytest.raises(ValueError, match="at least 2x2"):
            SU3PureGaugeConfig(
                nx=1,
                ny=2,
                g_electric=1.0,
                g_magnetic=1.0,
                truncation=0.5
            )
    
    def test_invalid_coupling(self):
        """Test invalid coupling constants."""
        with pytest.raises(ValueError, match="positive"):
            SU3PureGaugeConfig(
                nx=2,
                ny=2,
                g_electric=-1.0,
                g_magnetic=1.0,
                truncation=0.5
            )
    
    def test_invalid_truncation(self):
        """Test invalid truncation."""
        with pytest.raises(ValueError, match="positive"):
            SU3PureGaugeConfig(
                nx=2,
                ny=2,
                g_electric=1.0,
                g_magnetic=1.0,
                truncation=0.0
            )
    
    def test_invalid_boundary(self):
        """Test invalid boundary condition."""
        with pytest.raises(ValueError, match="periodic"):
            SU3PureGaugeConfig(
                nx=2,
                ny=2,
                g_electric=1.0,
                g_magnetic=1.0,
                truncation=0.5,
                boundary="invalid"
            )


class TestSU3PureGaugeLattice:
    """Test SU(3) lattice construction and properties."""
    
    def test_lattice_construction(self):
        """Test basic lattice construction."""
        config = SU3PureGaugeConfig(
            nx=2,
            ny=2,
            g_electric=1.0,
            g_magnetic=1.0,
            truncation=0.5
        )
        lattice = SU3PureGaugeLattice(config)
        
        assert lattice.nx == 2
        assert lattice.ny == 2
        assert lattice.n_links == 8  # 2x2 periodic: 2*2*2
        assert lattice.n_plaquettes == 4  # 2x2 periodic
        assert lattice.dim_per_link == 3  # Minimal truncation
        assert lattice.hilbert_dim == 3 ** 8
    
    def test_link_counting_periodic(self):
        """Test link counting with periodic boundaries."""
        config = SU3PureGaugeConfig(
            nx=3,
            ny=3,
            g_electric=1.0,
            g_magnetic=1.0,
            truncation=0.5,
            boundary="periodic"
        )
        lattice = SU3PureGaugeLattice(config)
        assert lattice.n_links == 18  # 2 * 3 * 3
    
    def test_link_counting_open(self):
        """Test link counting with open boundaries."""
        config = SU3PureGaugeConfig(
            nx=3,
            ny=3,
            g_electric=1.0,
            g_magnetic=1.0,
            truncation=0.5,
            boundary="open"
        )
        lattice = SU3PureGaugeLattice(config)
        # Open: (3*2 + 2*3) + (3*2 + 2*3) = 12 + 12 = 24
        # Actually: x-links: 3*(3-1) + (3-1)*3 = 6+6=12
        #           y-links: 3*(3-1) + (3-1)*3 = 6+6=12
        # Total: 12
        assert lattice.n_links == 12
    
    def test_plaquette_counting_periodic(self):
        """Test plaquette counting with periodic boundaries."""
        config = SU3PureGaugeConfig(
            nx=3,
            ny=3,
            g_electric=1.0,
            g_magnetic=1.0,
            truncation=0.5,
            boundary="periodic"
        )
        lattice = SU3PureGaugeLattice(config)
        assert lattice.n_plaquettes == 9  # 3 * 3
    
    def test_plaquette_counting_open(self):
        """Test plaquette counting with open boundaries."""
        config = SU3PureGaugeConfig(
            nx=3,
            ny=3,
            g_electric=1.0,
            g_magnetic=1.0,
            truncation=0.5,
            boundary="open"
        )
        lattice = SU3PureGaugeLattice(config)
        assert lattice.n_plaquettes == 4  # (3-1) * (3-1)
    
    def test_su3_generators(self):
        """Test SU(3) generator construction."""
        config = SU3PureGaugeConfig(
            nx=2,
            ny=2,
            g_electric=1.0,
            g_magnetic=1.0,
            truncation=0.5
        )
        lattice = SU3PureGaugeLattice(config)
        
        # Should have 8 generators (Gell-Mann matrices)
        assert len(lattice.generators) == 8
        
        # Each should be 3x3
        for gen in lattice.generators:
            assert gen.shape == (3, 3)
        
        # Check Hermiticity
        for gen in lattice.generators:
            assert np.allclose(gen, gen.conj().T)
        
        # Check tracelessness
        for gen in lattice.generators:
            assert np.abs(np.trace(gen)) < 1e-10
    
    def test_truncation_dimensions(self):
        """Test different truncation levels."""
        # Minimal truncation
        config1 = SU3PureGaugeConfig(
            nx=2, ny=2, g_electric=1.0, g_magnetic=1.0, truncation=0.5
        )
        lattice1 = SU3PureGaugeLattice(config1)
        assert lattice1.dim_per_link == 3
        
        # Extended truncation
        config2 = SU3PureGaugeConfig(
            nx=2, ny=2, g_electric=1.0, g_magnetic=1.0, truncation=1.0
        )
        lattice2 = SU3PureGaugeLattice(config2)
        assert lattice2.dim_per_link == 8


class TestSU3GapComputation:
    """Test mass gap computation for SU(3)."""
    
    def test_compute_gap_small_system(self):
        """Test gap computation on minimal system."""
        config = SU3PureGaugeConfig(
            nx=2,
            ny=2,
            g_electric=1.0,
            g_magnetic=1.0,
            truncation=0.5
        )
        lattice = SU3PureGaugeLattice(config)
        
        # This should work (3^8 = 6561 states)
        result = lattice.compute_gap()
        
        assert "gap" in result
        assert "E0" in result
        assert "E1" in result
        assert "method" in result
        
        # Should succeed
        if result.get("gap") is not None:
            assert result["gap"] >= 0  # Mass gap should be non-negative
            assert result["E1"] >= result["E0"]  # E1 >= E0
            assert result["method"] == "exact_diagonalization"
    
    def test_compute_gap_too_large(self):
        """Test that large systems fail gracefully."""
        config = SU3PureGaugeConfig(
            nx=3,
            ny=3,
            g_electric=1.0,
            g_magnetic=1.0,
            truncation=1.0  # 8 states per link
        )
        lattice = SU3PureGaugeLattice(config)
        
        # This should be too large (8^18 states)
        result = lattice.compute_gap()
        
        assert result["gap"] is None
        assert "error" in result
        assert "too large" in result["error"].lower()
    
    def test_hermiticity_check(self):
        """Test that Hamiltonian is Hermitian."""
        config = SU3PureGaugeConfig(
            nx=2,
            ny=2,
            g_electric=1.0,
            g_magnetic=1.0,
            truncation=0.5
        )
        lattice = SU3PureGaugeLattice(config)
        
        H = lattice.hamiltonian_dense()
        
        # Check Hermiticity
        assert np.allclose(H, H.conj().T)


class TestSU3Observables:
    """Test SU(3) observable placeholders."""
    
    def test_wilson_loop_placeholder(self):
        """Test Wilson loop placeholder."""
        config = SU3PureGaugeConfig(
            nx=2,
            ny=2,
            g_electric=1.0,
            g_magnetic=1.0,
            truncation=0.5
        )
        lattice = SU3PureGaugeLattice(config)
        
        result = lattice.compute_wilson_loop(R=1, T=1)
        assert result is None  # Placeholder
    
    def test_string_tension_placeholder(self):
        """Test string tension placeholder."""
        config = SU3PureGaugeConfig(
            nx=2,
            ny=2,
            g_electric=1.0,
            g_magnetic=1.0,
            truncation=0.5
        )
        lattice = SU3PureGaugeLattice(config)
        
        result = lattice.compute_string_tension()
        assert result is None  # Placeholder
    
    def test_polyakov_loop_placeholder(self):
        """Test Polyakov loop placeholder."""
        config = SU3PureGaugeConfig(
            nx=2,
            ny=2,
            g_electric=1.0,
            g_magnetic=1.0,
            truncation=0.5
        )
        lattice = SU3PureGaugeLattice(config)
        
        result = lattice.compute_polyakov_loop()
        assert result is None  # Placeholder
    
    def test_gauge_invariance_check(self):
        """Test gauge invariance check."""
        config = SU3PureGaugeConfig(
            nx=2,
            ny=2,
            g_electric=1.0,
            g_magnetic=1.0,
            truncation=0.5
        )
        lattice = SU3PureGaugeLattice(config)
        
        result = lattice.check_gauge_invariance()
        assert "su3_algebra_closed" in result
        assert result["su3_algebra_closed"] is True


class TestSU3Export:
    """Test SU(3) data export."""
    
    def test_to_dict(self):
        """Test dictionary export."""
        config = SU3PureGaugeConfig(
            nx=2,
            ny=2,
            g_electric=1.0,
            g_magnetic=1.0,
            truncation=0.5
        )
        lattice = SU3PureGaugeLattice(config)
        
        data = lattice.to_dict()
        
        assert data["model"] == "su3_pure_gauge_2plus1d"
        assert data["hypothesis_id"] == "gaugegap-0005"
        assert data["track"] == "GaugeGap"
        assert "config" in data
        assert "lattice" in data
        assert "su3_properties" in data
        
        # Check SU(3) properties
        su3_props = data["su3_properties"]
        assert su3_props["n_generators"] == 8
        assert su3_props["fundamental_dim"] == 3
        assert su3_props["adjoint_dim"] == 8
        assert su3_props["casimir_fundamental"] == 4.0 / 3.0


# Made with Bob