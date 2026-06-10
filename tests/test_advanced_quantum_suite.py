"""
Tests for Advanced Quantum Computing Suite

Verifies all advanced quantum techniques:
- Quantum information theory
- Topological quantum computing
- Adiabatic quantum computing
- Quantum optimal control
- Quantum metrology
- Quantum walks
- Advanced compilation
- Quantum complexity theory
"""

import numpy as np
import pytest

# Import all advanced quantum modules
from gaugegap.quantum import (
    quantum_information,
    topological_quantum,
    adiabatic_quantum,
    optimal_control,
    quantum_metrology,
    quantum_walks,
    advanced_compilation,
    quantum_complexity,
)


class TestQuantumInformation:
    """Test quantum information theory functions."""
    
    def test_von_neumann_entropy(self):
        """Test von Neumann entropy calculation."""
        # Pure state: entropy = 0
        pure_state = np.array([[1, 0], [0, 0]], dtype=complex)
        entropy = quantum_information.von_neumann_entropy(pure_state)
        assert abs(entropy) < 1e-10
        
        # Maximally mixed state: entropy = log(2)
        mixed_state = np.eye(2) / 2
        entropy = quantum_information.von_neumann_entropy(mixed_state)
        assert abs(entropy - np.log(2)) < 1e-10
    
    def test_entanglement_entropy(self):
        """Test entanglement entropy."""
        # Bell state
        bell_state = np.array([1, 0, 0, 1], dtype=complex) / np.sqrt(2)
        result = quantum_information.entanglement_entropy(
            bell_state, [0], 2
        )
        # Should be maximally entangled: S = log(2)
        assert result.value > 0.5
        assert result.subsystem_size == 1
    
    def test_quantum_fisher_information_pure(self):
        """Test quantum Fisher information for pure state."""
        state = np.array([1, 0], dtype=complex)
        observable = np.array([[1, 0], [0, -1]])
        F_Q = quantum_information.quantum_fisher_information_pure(state, observable)
        assert F_Q >= 0


class TestTopologicalQuantum:
    """Test topological quantum computing functions."""
    
    def test_fibonacci_braiding_matrix(self):
        """Fibonacci braid generators must be unitary and satisfy Yang-Baxter."""
        s1 = topological_quantum.fibonacci_braiding_matrix(0, 1)
        s2 = topological_quantum.fibonacci_braiding_matrix(1, 2)
        assert s1.shape == (2, 2) and s2.shape == (2, 2)
        # Braiding is a unitary operation (the old implementation divided the
        # R-matrix by sqrt(phi) and was NOT unitary).
        for B in (s1, s2):
            assert np.allclose(B @ B.conj().T, np.eye(2), atol=1e-12)
        # R-matrix eigenvalues are the standard Fibonacci phases.
        eigs = sorted(np.angle(np.linalg.eigvals(s1)) / np.pi)
        assert np.allclose(eigs, [-4 / 5, 3 / 5], atol=1e-12)
        # Braid relation (Yang-Baxter): s1 s2 s1 = s2 s1 s2.
        assert np.allclose(s1 @ s2 @ s1, s2 @ s1 @ s2, atol=1e-12)
        # The F-matrix is unitary and involutory.
        F = topological_quantum.fibonacci_f_matrix()
        assert np.allclose(F @ F.conj().T, np.eye(2), atol=1e-12)
        assert np.allclose(F @ F, np.eye(2), atol=1e-12)
    
    def test_braid_sequence(self):
        """Test braiding sequence."""
        initial_state = np.array([1, 0], dtype=complex)
        braid_word = [(0, 1), (1, 2)]
        result = topological_quantum.braid_sequence(
            initial_state, braid_word, "fibonacci"
        )
        assert result.fidelity >= 0
        assert result.fidelity <= 1
    
    def test_yang_baxter_check(self):
        """Test Yang-Baxter equation."""
        result = topological_quantum.yang_baxter_check("fibonacci")
        assert result["yang_baxter_satisfied"]


class TestAdiabaticQuantum:
    """Test adiabatic quantum computing functions."""
    
    def test_linear_schedule(self):
        """Test linear annealing schedule."""
        s = adiabatic_quantum.linear_schedule(0.5, 1.0)
        assert abs(s - 0.5) < 1e-10
    
    def test_adiabatic_evolution(self):
        """Test adiabatic evolution."""
        H_initial = np.array([[1, 0], [0, -1]])
        H_final = np.array([[0, 1], [1, 0]])
        initial_state = np.array([1, 0], dtype=complex)
        
        result = adiabatic_quantum.adiabatic_evolution(
            H_initial, H_final, initial_state, T=1.0, n_steps=10
        )
        assert result.ground_state_fidelity >= 0
        assert result.ground_state_fidelity <= 1
    
    def test_landau_zener_probability(self):
        """Test Landau-Zener formula."""
        P = adiabatic_quantum.landau_zener_probability(gap=0.1, velocity=1.0)
        assert 0 <= P <= 1


class TestOptimalControl:
    """Test quantum optimal control functions."""
    
    def test_quantum_speed_limit(self):
        """Test quantum speed limits."""
        initial = np.array([1, 0], dtype=complex)
        target = np.array([0, 1], dtype=complex)
        H = np.array([[1, 0], [0, -1]])
        
        qsl = optimal_control.quantum_speed_limit(initial, target, H)
        assert qsl["quantum_speed_limit"] > 0
        assert qsl["mandelstam_tamm_bound"] > 0
    
    def test_grape_optimization(self):
        """Test GRAPE optimization."""
        H_drift = np.array([[0, 0], [0, 0]])
        H_control = [np.array([[0, 1], [1, 0]])]
        initial = np.array([1, 0], dtype=complex)
        target = np.array([0, 1], dtype=complex)
        
        result = optimal_control.grape_optimization(
            H_drift, H_control, initial, target, T=1.0, 
            n_steps=10, max_iterations=5
        )
        assert result.final_fidelity >= 0
        assert result.method == "GRAPE"


class TestQuantumMetrology:
    """Test quantum metrology functions."""
    
    def test_quantum_cramer_rao_bound(self):
        """Test quantum Cramér-Rao bound."""
        rho = np.eye(2) / 2
        generator = np.array([[1, 0], [0, -1]])
        
        bound = quantum_metrology.quantum_cramer_rao_bound(
            rho, generator, n_measurements=10
        )
        assert bound > 0
    
    def test_heisenberg_limit_protocol(self):
        """Test Heisenberg-limited metrology."""
        H = np.array([[1, 0], [0, -1]])
        result = quantum_metrology.heisenberg_limit_protocol(
            H, parameter=0.5, n_particles=4, evolution_time=1.0
        )
        assert result.heisenberg_limited
        assert result.protocol == "heisenberg_limit"


class TestQuantumWalks:
    """Test quantum walk functions."""
    
    def test_discrete_time_quantum_walk_1d(self):
        """Test 1D discrete-time quantum walk."""
        result = quantum_walks.discrete_time_quantum_walk_1d(
            n_steps=10, n_sites=20, initial_position=10
        )
        assert result.walk_type == "discrete_time_1d"
        assert len(result.probability_distribution) == 20
        assert abs(np.sum(result.probability_distribution) - 1.0) < 1e-10
    
    def test_continuous_time_quantum_walk(self):
        """Test continuous-time quantum walk."""
        # Line graph
        n = 5
        adjacency = np.zeros((n, n))
        for i in range(n-1):
            adjacency[i, i+1] = 1
            adjacency[i+1, i] = 1
        
        result = quantum_walks.continuous_time_quantum_walk(
            adjacency, time=1.0, initial_vertex=0
        )
        assert result.walk_type == "continuous_time"
        assert abs(np.sum(result.probability_distribution) - 1.0) < 1e-10
    
    def test_quantum_walk_search(self):
        """Test quantum walk search."""
        n = 10
        adjacency = np.ones((n, n)) - np.eye(n)  # Complete graph
        marked = [5]
        
        result = quantum_walks.quantum_walk_search(
            adjacency, marked, max_time=5.0, n_time_steps=20
        )
        assert result["max_probability_marked"] > 0


class TestAdvancedCompilation:
    """Test advanced compilation functions."""
    
    def test_kak_decomposition(self):
        """KAK local (Makhlin) invariants on known two-qubit gates."""
        CNOT = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=complex)
        SWAP = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=complex)
        local = np.kron(np.array([[0, 1], [1, 0]], dtype=complex), np.eye(2, dtype=complex))

        cases = {  # (G1, G2)
            id(CNOT): (CNOT, (0.0, 1.0), True),
            id(SWAP): (SWAP, (-1.0, -3.0), True),
            id(local): (local, (1.0, 3.0), False),
        }
        for U, (g1, g2), entangling in cases.values():
            res = advanced_compilation.kak_decomposition(U)
            inv = res["makhlin_invariants"]
            assert np.isclose(inv["G1"].real, g1, atol=1e-9)
            assert np.isclose(inv["G2"].real, g2, atol=1e-9)
            assert res["is_entangling"] is entangling
    
    def test_shannon_decomposition(self):
        """Test Shannon decomposition."""
        U = np.eye(4, dtype=complex)
        result = advanced_compilation.shannon_decomposition(U, n_qubits=2)
        assert result.method == "shannon"
        assert result.fidelity == 1.0
    
    def test_compile_gauge_invariant_operation(self):
        """Test gauge-invariant compilation."""
        result = advanced_compilation.compile_gauge_invariant_operation(
            "plaquette", n_qubits=4
        )
        assert result.metadata["gauge_invariant"]
        assert result.two_qubit_gates > 0


class TestQuantumComplexity:
    """Test quantum complexity theory functions."""
    
    def test_bqp_verification(self):
        """Test BQP complexity analysis."""
        result = quantum_complexity.bqp_verification(
            problem_size=10, algorithm_type="phase_estimation"
        )
        assert result.complexity_class == "BQP"
        assert result.quantum_advantage
    
    def test_quantum_query_complexity(self):
        """Test query complexity analysis."""
        result = quantum_complexity.quantum_query_complexity(
            "search", n_elements=100
        )
        assert result["quantum_queries"] < result["classical_queries"]
        assert result["speedup"] == "quadratic"
    
    def test_gauge_theory_complexity_analysis(self):
        """Test gauge theory complexity."""
        result = quantum_complexity.gauge_theory_complexity_analysis(
            n_sites=10, gauge_group="Z2"
        )
        assert result["ground_state_complexity"] == "QMA-complete"
        assert result["evolution_complexity"] == "BQP"


class TestIntegration:
    """Test integration between modules."""
    
    def test_metrology_with_information_theory(self):
        """Test combining metrology and information theory."""
        # Create a superposition state (not an eigenstate)
        state = np.array([1, 1], dtype=complex) / np.sqrt(2)
        H = np.array([[1, 0], [0, -1]])
        
        # Compute Fisher information
        F_Q = quantum_information.quantum_fisher_information_pure(state, H)
        
        # Use in metrology
        rho = np.outer(state, state.conj())
        bound = quantum_metrology.quantum_cramer_rao_bound(rho, H)
        
        assert F_Q > 0  # Should be non-zero for superposition state
        assert bound > 0
    
    def test_adiabatic_with_optimal_control(self):
        """Test combining adiabatic and optimal control."""
        H_initial = np.array([[1, 0], [0, -1]])
        H_final = np.array([[0, 1], [1, 0]])
        
        # Analyze gap structure
        gap_analysis = adiabatic_quantum.analyze_gap_structure(
            H_initial, H_final, n_points=10
        )
        
        # Use quantum speed limit
        initial = np.array([1, 0], dtype=complex)
        target = np.array([0, 1], dtype=complex)
        qsl = optimal_control.quantum_speed_limit(initial, target, H_final)
        
        assert gap_analysis["min_gap"] > 0
        assert qsl["quantum_speed_limit"] > 0


def test_all_modules_importable():
    """Test that all modules can be imported."""
    assert quantum_information is not None
    assert topological_quantum is not None
    assert adiabatic_quantum is not None
    assert optimal_control is not None
    assert quantum_metrology is not None
    assert quantum_walks is not None
    assert advanced_compilation is not None
    assert quantum_complexity is not None


# Made with Bob