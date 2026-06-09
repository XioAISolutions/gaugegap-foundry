"""
Tests for advanced quantum computing implementations.

Tests cover:
- Advanced Hamiltonian simulation (Trotter, qDRIFT)
- Gauge theory ansätze
- Shadow tomography
- Quantum subspace methods
"""

import numpy as np
import pytest

from src.gaugegap.quantum.advanced_hamiltonian_simulation import (
    first_order_trotter,
    second_order_trotter,
    fourth_order_trotter,
    qdrift_simulation,
    adaptive_trotter,
    compare_simulation_methods,
    gauge_theory_trotter_terms,
)

from src.gaugegap.quantum.gauge_theory_ansatz import (
    gauge_invariant_hardware_efficient_ansatz,
    plaquette_based_ansatz,
    adaptive_ansatz_step,
    compare_ansatze,
)

from src.gaugegap.quantum.shadow_tomography import (
    classical_shadow_pauli,
    classical_shadow_clifford,
    adaptive_shadow_tomography,
    shadow_norm,
    estimate_sample_complexity,
    compare_shadow_methods,
)

from src.gaugegap.quantum.quantum_subspace_methods import (
    quantum_subspace_expansion,
    quantum_krylov_method,
    subspace_search_vqe,
    quantum_imaginary_time_evolution,
    compare_subspace_methods,
)


class TestAdvancedHamiltonianSimulation:
    """Test advanced Hamiltonian simulation methods."""
    
    def test_first_order_trotter(self):
        """Test first-order Trotter decomposition."""
        # Simple 2-qubit Hamiltonian: H = Z⊗Z + X⊗I
        H1 = np.diag([1, -1, -1, 1])  # Z⊗Z
        H2 = np.array([[0, 1, 0, 0],
                       [1, 0, 0, 0],
                       [0, 0, 0, 1],
                       [0, 0, 1, 0]])  # X⊗I
        
        terms = [H1, H2]
        initial_state = np.array([1, 0, 0, 0], dtype=complex)
        
        result = first_order_trotter(terms, initial_state, time=0.1, n_steps=10)
        
        assert result.method == "first_order_trotter"
        assert result.n_steps == 10
        assert np.abs(np.linalg.norm(result.final_state) - 1.0) < 1e-10
        assert result.error_estimate > 0
    
    def test_second_order_trotter(self):
        """Test second-order Trotter has better accuracy."""
        # Same Hamiltonian as above
        H1 = np.diag([1, -1, -1, 1])
        H2 = np.array([[0, 1, 0, 0],
                       [1, 0, 0, 0],
                       [0, 0, 0, 1],
                       [0, 0, 1, 0]])
        
        terms = [H1, H2]
        initial_state = np.array([1, 0, 0, 0], dtype=complex)
        
        result_1st = first_order_trotter(terms, initial_state, time=0.5, n_steps=5)
        result_2nd = second_order_trotter(terms, initial_state, time=0.5, n_steps=5)
        
        # Second-order should have smaller error estimate
        assert result_2nd.error_estimate < result_1st.error_estimate
    
    def test_fourth_order_trotter(self):
        """Test fourth-order Trotter."""
        H1 = np.diag([1, -1, -1, 1])
        H2 = np.array([[0, 1, 0, 0],
                       [1, 0, 0, 0],
                       [0, 0, 0, 1],
                       [0, 0, 1, 0]])
        
        terms = [H1, H2]
        initial_state = np.array([1, 0, 0, 0], dtype=complex)
        
        result = fourth_order_trotter(terms, initial_state, time=0.1, n_steps=2)
        
        assert result.method == "fourth_order_trotter"
        assert np.abs(np.linalg.norm(result.final_state) - 1.0) < 1e-10
    
    def test_qdrift_simulation(self):
        """Test qDRIFT randomized Trotter."""
        H1 = np.diag([1, -1, -1, 1])
        H2 = np.array([[0, 1, 0, 0],
                       [1, 0, 0, 0],
                       [0, 0, 0, 1],
                       [0, 0, 1, 0]])
        
        terms = [H1, H2]
        initial_state = np.array([1, 0, 0, 0], dtype=complex)
        
        result = qdrift_simulation(terms, initial_state, time=0.1, n_samples=20, seed=42)
        
        assert result.method == "qdrift"
        assert result.n_steps == 20
        assert np.abs(np.linalg.norm(result.final_state) - 1.0) < 1e-10
        assert "lambda_total" in result.metadata
    
    def test_adaptive_trotter(self):
        """Test adaptive Trotter with error target."""
        H1 = np.diag([1, -1, -1, 1])
        H2 = np.array([[0, 1, 0, 0],
                       [1, 0, 0, 0],
                       [0, 0, 0, 1],
                       [0, 0, 1, 0]])
        
        terms = [H1, H2]
        initial_state = np.array([1, 0, 0, 0], dtype=complex)
        
        result = adaptive_trotter(terms, initial_state, time=0.1, target_error=0.01)
        
        assert result.metadata["adaptive"] is True
        assert result.error_estimate <= result.metadata["target_error"] * 2  # Allow some margin


class TestGaugeTheoryAnsatz:
    """Test gauge theory-inspired ansätze."""
    
    def test_gauge_invariant_hardware_efficient(self):
        """Test gauge-invariant hardware-efficient ansatz."""
        n_qubits = 4
        n_layers = 2
        
        state_fn, n_params, result = gauge_invariant_hardware_efficient_ansatz(
            n_qubits, n_layers, "linear"
        )
        
        assert n_params == 2 * n_qubits * n_layers
        assert result.gauge_invariant is True
        assert result.n_parameters == n_params
        
        # Test state generation
        params = np.random.randn(n_params)
        state = state_fn(params)
        
        assert len(state) == 2**n_qubits
        assert np.abs(np.linalg.norm(state) - 1.0) < 1e-10
    
    def test_plaquette_based_ansatz(self):
        """Test plaquette-based ansatz."""
        n_plaquettes = 1
        n_layers = 2
        
        state_fn, n_params, result = plaquette_based_ansatz(n_plaquettes, n_layers)
        
        assert result.gauge_invariant is True
        assert result.metadata["type"] == "plaquette_based"
        
        # Test state generation
        params = np.random.randn(n_params)
        state = state_fn(params)
        
        assert np.abs(np.linalg.norm(state) - 1.0) < 1e-10
    
    def test_compare_ansatze(self):
        """Test ansatz comparison."""
        n_qubits = 4
        H = np.random.randn(2**n_qubits, 2**n_qubits)
        H = (H + H.T) / 2  # Make Hermitian
        
        results = compare_ansatze(n_qubits, H, n_layers=2)
        
        assert "hardware_efficient" in results
        assert results["hardware_efficient"]["gauge_invariant"] is True


class TestShadowTomography:
    """Test shadow tomography methods."""
    
    def test_classical_shadow_pauli(self):
        """Test Pauli shadow tomography."""
        # Simple 2-qubit state
        state = np.array([1, 0, 0, 0], dtype=complex)
        
        # Observables
        Z0 = np.diag([1, 1, -1, -1])
        Z1 = np.diag([1, -1, 1, -1])
        observables = {"Z0": Z0, "Z1": Z1}
        
        result = classical_shadow_pauli(state, observables, n_snapshots=100, seed=42)
        
        assert result.method == "pauli_shadow"
        assert result.n_snapshots == 100
        assert "Z0" in result.observable_estimates
        assert "Z1" in result.observable_estimates
        
        # Check estimates are reasonable (|00⟩ has Z0=Z1=1)
        assert abs(result.observable_estimates["Z0"] - 1.0) < 0.5
        assert abs(result.observable_estimates["Z1"] - 1.0) < 0.5
    
    def test_shadow_norm(self):
        """Test shadow norm computation."""
        # Pauli Z on 2 qubits
        Z = np.diag([1, 1, -1, -1])
        norm = shadow_norm(Z)
        
        assert norm > 0
        assert np.isfinite(norm)
    
    def test_estimate_sample_complexity(self):
        """Test sample complexity estimation."""
        Z0 = np.diag([1, 1, -1, -1])
        Z1 = np.diag([1, -1, 1, -1])
        observables = {"Z0": Z0, "Z1": Z1}
        
        complexity = estimate_sample_complexity(observables, target_error=0.1)
        
        assert "max_complexity" in complexity
        assert "shadow_norms" in complexity
        assert complexity["max_complexity"] > 0
    
    def test_adaptive_shadow_tomography(self):
        """Test adaptive shadow tomography."""
        state = np.array([1, 0, 0, 0], dtype=complex)
        Z0 = np.diag([1, 1, -1, -1])
        observables = {"Z0": Z0}
        
        result = adaptive_shadow_tomography(
            state, observables, target_error=0.1, max_snapshots=1000, seed=42
        )
        
        assert result.metadata["adaptive"] is True


class TestQuantumSubspaceMethods:
    """Test quantum subspace methods."""
    
    def test_quantum_subspace_expansion(self):
        """Test quantum subspace expansion."""
        # 2-qubit Hamiltonian
        H = np.diag([0, 1, 1, 2])
        
        # Reference state (not ground state)
        ref_state = np.array([0, 1, 0, 0], dtype=complex)
        
        # Operators to generate subspace
        X0 = np.array([[0, 1, 0, 0],
                       [1, 0, 0, 0],
                       [0, 0, 0, 1],
                       [0, 0, 1, 0]])
        operators = [X0]
        
        result = quantum_subspace_expansion(ref_state, H, operators, n_states=2)
        
        assert result.method == "quantum_subspace_expansion"
        assert result.subspace_dimension >= 2
        assert result.ground_state_energy() <= 1.0  # Should improve from ref
    
    def test_quantum_krylov_method(self):
        """Test quantum Krylov method."""
        # Simple Hamiltonian
        H = np.diag([0, 1, 2, 3])
        initial_state = np.array([0.5, 0.5, 0.5, 0.5])
        initial_state /= np.linalg.norm(initial_state)
        
        result = quantum_krylov_method(initial_state, H, n_iterations=4, n_states=2)
        
        assert result.method == "quantum_krylov"
        assert result.subspace_dimension <= 4
        assert abs(result.ground_state_energy() - 0.0) < 0.1  # Should find ground state
    
    def test_quantum_imaginary_time_evolution(self):
        """Test quantum imaginary time evolution."""
        # Hamiltonian with known ground state
        H = np.diag([0, 1, 2, 3])
        
        # Start from excited state
        initial_state = np.array([0, 1, 0, 0], dtype=complex)
        
        result = quantum_imaginary_time_evolution(
            initial_state, H, beta=5.0, n_steps=10
        )
        
        assert result.method == "quantum_imaginary_time_evolution"
        # Should converge toward ground state (E=0)
        assert result.ground_state_energy() < 1.0
    
    def test_compare_subspace_methods(self):
        """Test comparison of subspace methods."""
        H = np.diag([0, 1, 2, 3])
        initial_state = np.array([0.5, 0.5, 0.5, 0.5])
        initial_state /= np.linalg.norm(initial_state)
        
        X = np.array([[0, 1, 0, 0],
                      [1, 0, 0, 0],
                      [0, 0, 0, 1],
                      [0, 0, 1, 0]])
        operators = [X]
        
        results = compare_subspace_methods(
            H, initial_state, operators, exact_ground_energy=0.0
        )
        
        assert "krylov" in results
        assert "qse" in results
        assert "imaginary_time" in results
        
        # All methods should find ground state reasonably well
        for method in results:
            assert results[method]["error_vs_exact"] < 0.5


class TestIntegration:
    """Integration tests combining multiple techniques."""
    
    def test_z2_gauge_theory_workflow(self):
        """Test complete workflow for Z2 gauge theory."""
        from src.gaugegap.models.z2_plaquette import (
            hamiltonian_dense,
            ground_state,
        )
        
        # Small Z2 system
        n_plaquettes = 1
        H = hamiltonian_dense(n_plaquettes, plaquette_coupling=1.0, transverse_field=0.2)
        exact_energies, exact_ground = ground_state(n_plaquettes, 1.0, 0.2)
        exact_gs_energy = exact_energies[0]
        
        # Test Hamiltonian simulation
        terms = gauge_theory_trotter_terms(1.0, 0.2, n_plaquettes)
        initial_state = np.zeros(len(exact_ground), dtype=complex)
        initial_state[0] = 1.0
        
        sim_result = second_order_trotter(terms, initial_state, time=1.0, n_steps=10)
        assert np.linalg.norm(sim_result.final_state) > 0.9
        
        # Test ansatz
        n_qubits = len(exact_ground).bit_length() - 1
        state_fn, n_params, ansatz_result = gauge_invariant_hardware_efficient_ansatz(
            n_qubits, n_layers=2
        )
        assert ansatz_result.gauge_invariant is True
        
        # Test subspace method
        krylov_result = quantum_krylov_method(exact_ground, H, n_iterations=5)
        assert abs(krylov_result.ground_state_energy() - exact_gs_energy) < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
