"""
Combined tests for hypothesis pruning, tensor networks, and error mitigation.

This file tests:
- Hypothesis pruning with Bayesian model comparison
- Tensor network baseline methods
- Advanced error mitigation techniques
"""

import pytest
import numpy as np
from datetime import datetime

# Hypothesis pruning imports
from src.gaugegap.analysis.hypothesis_pruning import (
    Hypothesis,
    HypothesisPruner,
    BayesianModelComparison,
    compute_evidence_ratio,
    information_criteria,
    likelihood_ratio_test,
)

# Tensor network imports
from src.gaugegap.classical.tensor_networks import (
    DMRGSolver,
    PEPSSolver,
    TEBDSolver,
    compute_entanglement_entropy,
    truncation_error_bound,
)

# Error mitigation imports
from src.gaugegap.mitigation.advanced_mitigation import (
    ProbabilisticErrorCancellation,
    CliffordDataRegression,
    SymmetryVerification,
    VirtualDistillation,
    AdaptiveMitigation,
)


# ============================================================================
# Hypothesis Pruning Tests
# ============================================================================

class TestHypothesis:
    """Test Hypothesis dataclass and methods."""
    
    def test_hypothesis_creation(self):
        """Test creating a hypothesis."""
        h = Hypothesis(
            id="test-001",
            description="Test hypothesis",
            track="gaugegap",
            n_parameters=2,
        )
        
        assert h.id == "test-001"
        assert h.status == "active"
        assert h.log_evidence == 0.0
    
    def test_evidence_update(self):
        """Test updating hypothesis evidence."""
        h = Hypothesis(id="h1", description="Test", track="gaugegap")
        
        h.update_evidence(5.0)
        assert h.log_evidence == 5.0
        assert len(h.evidence_history) == 1
        
        h.update_evidence(-3.0)
        assert h.log_evidence == 2.0
        assert len(h.evidence_history) == 2
    
    def test_falsification(self):
        """Test automatic falsification."""
        h = Hypothesis(
            id="h1",
            description="Test",
            track="gaugegap",
            falsification_threshold=-10.0,
        )
        
        h.update_evidence(-15.0)
        assert h.status == "falsified"
    
    def test_bayes_factor(self):
        """Test Bayes factor computation."""
        h1 = Hypothesis(id="h1", description="H1", track="gaugegap")
        h2 = Hypothesis(id="h2", description="H2", track="gaugegap")
        
        h1.log_evidence = 5.0
        h2.log_evidence = 2.0
        
        bf = h1.bayes_factor(h2)
        assert abs(bf - np.exp(3.0)) < 1e-6


class TestHypothesisPruner:
    """Test hypothesis pruning engine."""
    
    def test_register_hypothesis(self):
        """Test registering hypotheses."""
        pruner = HypothesisPruner()
        
        h1 = Hypothesis(id="h1", description="Test 1", track="gaugegap")
        h2 = Hypothesis(id="h2", description="Test 2", track="gaugegap")
        
        pruner.register_hypothesis(h1)
        pruner.register_hypothesis(h2)
        
        assert len(pruner.hypotheses) == 2
    
    def test_prune_falsified(self):
        """Test pruning falsified hypotheses."""
        pruner = HypothesisPruner(falsification_threshold=-10.0)
        
        h1 = Hypothesis(id="h1", description="Good", track="gaugegap")
        h2 = Hypothesis(id="h2", description="Bad", track="gaugegap")
        
        pruner.register_hypothesis(h1)
        pruner.register_hypothesis(h2)
        
        pruner.update_evidence("h1", 5.0)
        pruner.update_evidence("h2", -15.0)
        
        falsified = pruner.prune_falsified()
        
        assert "h2" in falsified
        assert pruner.hypotheses["h2"].status == "falsified"
    
    def test_status_summary(self):
        """Test getting status summary."""
        pruner = HypothesisPruner()
        
        h1 = Hypothesis(id="h1", description="Active", track="gaugegap")
        h2 = Hypothesis(id="h2", description="Falsified", track="gaugegap")
        
        pruner.register_hypothesis(h1)
        pruner.register_hypothesis(h2)
        
        pruner.update_evidence("h2", -15.0)
        pruner.prune_falsified()
        
        summary = pruner.get_status_summary()
        
        assert summary["total"] == 2
        assert summary["active"] == 1
        assert summary["falsified"] == 1


class TestBayesianModelComparison:
    """Test Bayesian model comparison."""
    
    def test_compare_hypotheses(self):
        """Test comparing multiple hypotheses."""
        h1 = Hypothesis(id="h1", description="Model 1", track="gaugegap", n_parameters=2)
        h2 = Hypothesis(id="h2", description="Model 2", track="gaugegap", n_parameters=3)
        
        h1.log_evidence = 10.0
        h2.log_evidence = 8.0
        
        comparator = BayesianModelComparison()
        data = np.random.randn(100)
        
        result = comparator.compare([h1, h2], data)
        
        assert result.best_hypothesis == "h1"
        assert "h1" in result.posterior_probabilities
        assert result.posterior_probabilities["h1"] > result.posterior_probabilities["h2"]
    
    def test_information_criteria(self):
        """Test information criteria computation."""
        ic = information_criteria(
            log_likelihood=100.0,
            n_parameters=3,
            n_data=50,
        )
        
        assert "AIC" in ic
        assert "BIC" in ic
        assert "DIC" in ic
        assert ic["BIC"] > ic["AIC"]  # BIC penalizes complexity more


class TestLikelihoodRatioTest:
    """Test likelihood ratio test."""
    
    def test_nested_models(self):
        """Test LRT for nested models."""
        log_l_full = 100.0
        log_l_reduced = 95.0
        df_diff = 2
        
        lr_stat, p_value, reject = likelihood_ratio_test(
            log_l_full, log_l_reduced, df_diff
        )
        
        assert lr_stat > 0
        assert 0 <= p_value <= 1
        assert isinstance(reject, bool)


# ============================================================================
# Tensor Network Tests
# ============================================================================

class TestDMRGSolver:
    """Test DMRG solver."""
    
    def test_small_system(self):
        """Test DMRG on small system."""
        # Simple 2-site Hamiltonian
        n_sites = 2
        local_dim = 2
        dim = local_dim**n_sites
        
        # Heisenberg-like Hamiltonian
        H = np.random.randn(dim, dim)
        H = (H + H.T) / 2  # Make Hermitian
        
        solver = DMRGSolver(max_bond_dim=10)
        result = solver.solve(H, n_sites, local_dim)
        
        assert result.method == "DMRG"
        assert result.system_size == n_sites
        assert result.ground_state_energy < 0  # Should find lowest eigenvalue
    
    def test_entanglement_computation(self):
        """Test entanglement entropy computation."""
        # Create simple product state
        state = np.zeros(4)
        state[0] = 1.0  # |00⟩
        
        entropy = compute_entanglement_entropy(state, partition_size=1, local_dim=2)
        
        # Product state should have zero entanglement
        assert abs(entropy) < 1e-10
    
    def test_entangled_state(self):
        """Test entanglement of Bell state."""
        # Bell state: (|00⟩ + |11⟩)/√2
        state = np.zeros(4)
        state[0] = 1.0 / np.sqrt(2)
        state[3] = 1.0 / np.sqrt(2)
        
        entropy = compute_entanglement_entropy(state, partition_size=1, local_dim=2)
        
        # Bell state should have maximal entanglement: ln(2)
        assert abs(entropy - np.log(2)) < 0.1


class TestTruncationError:
    """Test truncation error bounds."""
    
    def test_no_truncation(self):
        """Test when no truncation needed."""
        singular_values = np.array([0.9, 0.3, 0.1])
        max_bond_dim = 5
        
        error = truncation_error_bound(singular_values, max_bond_dim)
        
        assert error == 0.0
    
    def test_with_truncation(self):
        """Test truncation error bound."""
        singular_values = np.array([0.9, 0.3, 0.1, 0.05, 0.02])
        max_bond_dim = 3
        
        error = truncation_error_bound(singular_values, max_bond_dim)
        
        # Should be sqrt(0.05² + 0.02²)
        expected = np.sqrt(0.05**2 + 0.02**2)
        assert abs(error - expected) < 1e-10


class TestTEBDSolver:
    """Test TEBD time evolution."""
    
    def test_time_evolution(self):
        """Test basic time evolution."""
        n_sites = 2
        local_dim = 2
        dim = local_dim**n_sites
        
        # Simple Hamiltonian
        H = np.random.randn(dim, dim)
        H = (H + H.T) / 2
        
        # Initial state
        initial_state = np.zeros(dim)
        initial_state[0] = 1.0
        
        solver = TEBDSolver(max_bond_dim=10, time_step=0.01)
        result = solver.evolve(initial_state, H, total_time=0.1, n_sites=n_sites)
        
        assert result.method == "TEBD"
        assert len(result.convergence_history) > 0


# ============================================================================
# Error Mitigation Tests
# ============================================================================

class TestProbabilisticErrorCancellation:
    """Test PEC method."""
    
    def test_basic_mitigation(self):
        """Test basic PEC mitigation."""
        pec = ProbabilisticErrorCancellation()
        
        # Simulate noisy measurements
        circuit_results = [0.9, 0.85, 0.95, 0.88]
        circuit_depth = 10
        gate_types = ["rx", "ry", "cnot"]
        
        result = pec.mitigate(circuit_results, circuit_depth, gate_types)
        
        assert result.method == "PEC"
        assert result.mitigation_overhead > 1.0
        assert result.mitigated_value != result.raw_value


class TestCliffordDataRegression:
    """Test CDR method."""
    
    def test_training_and_mitigation(self):
        """Test CDR training and application."""
        cdr = CliffordDataRegression(n_training_circuits=10)
        
        # Generate synthetic training data
        noisy_values = np.array([0.9, 0.85, 0.95, 0.88, 0.92])
        exact_values = np.array([1.0, 0.95, 1.05, 0.98, 1.02])
        features = np.array([[5], [8], [6], [10], [7]])  # Circuit depths
        
        cdr.train(noisy_values, exact_values, features)
        
        # Apply to new data
        result = cdr.mitigate(0.87, np.array([9]))
        
        assert result.method == "CDR"
        assert result.mitigated_value != result.raw_value


class TestSymmetryVerification:
    """Test symmetry-based mitigation."""
    
    def test_symmetry_check(self):
        """Test symmetry verification."""
        # Define symmetry operator (e.g., parity)
        dim = 4
        parity = np.diag([1, -1, -1, 1])
        
        verifier = SymmetryVerification([parity])
        
        # Even parity state
        state_even = np.array([1.0, 0, 0, 0])
        is_valid, violations = verifier.verify(state_even)
        
        assert is_valid or violations[0] < 0.1
    
    def test_post_selection(self):
        """Test post-selection on valid measurements."""
        dim = 4
        identity = np.eye(dim)
        
        verifier = SymmetryVerification([identity], tolerance=0.1)
        
        # Create measurements (state, value)
        state1 = np.array([1.0, 0, 0, 0])
        state2 = np.array([0, 1.0, 0, 0])
        
        measurements = [(state1, 1.0), (state2, 0.8)]
        
        result = verifier.mitigate(measurements)
        
        assert result.method == "SymmetryVerification"
        assert result.mitigation_overhead >= 1.0


class TestVirtualDistillation:
    """Test virtual distillation."""
    
    def test_distillation(self):
        """Test virtual distillation with multiple copies."""
        distiller = VirtualDistillation(n_copies=2)
        
        # Create noisy states
        dim = 4
        state1 = np.array([0.9, 0.1, 0, 0])
        state1 /= np.linalg.norm(state1)
        state2 = np.array([0.85, 0.15, 0, 0])
        state2 /= np.linalg.norm(state2)
        
        observable = np.diag([1, 0, 0, 0])
        
        result = distiller.mitigate([state1, state2], observable)
        
        assert result.method == "VirtualDistillation"
        assert result.mitigation_overhead == 2.0


class TestAdaptiveMitigation:
    """Test adaptive mitigation strategy selection."""
    
    def test_strategy_selection(self):
        """Test automatic strategy selection."""
        adaptive = AdaptiveMitigation()
        
        # Test different scenarios
        strategy1 = adaptive.select_strategy(
            circuit_depth=5,
            has_symmetries=True,
            has_training_data=False,
            n_copies=1,
            max_overhead=10.0,
        )
        assert strategy1 == "symmetry"
        
        strategy2 = adaptive.select_strategy(
            circuit_depth=8,
            has_symmetries=False,
            has_training_data=False,
            n_copies=1,
            max_overhead=20.0,
        )
        assert strategy2 in ["pec", "cdr"]
    
    def test_forced_strategy(self):
        """Test forcing specific strategy."""
        adaptive = AdaptiveMitigation()
        
        # Configure CDR
        adaptive.cdr.coefficients = np.array([1.0, 0.1])
        
        data = 0.9
        result = adaptive.mitigate(
            data,
            strategy="cdr",
            features=np.array([5]),
        )
        
        assert result.method == "CDR"


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Test integration between modules."""
    
    def test_hypothesis_with_tensor_network(self):
        """Test using tensor network results for hypothesis testing."""
        # Create hypothesis
        h = Hypothesis(
            id="tn-test",
            description="Tensor network prediction",
            track="gaugegap",
            n_parameters=1,
        )
        
        # Simulate tensor network calculation
        dim = 4
        H = np.random.randn(dim, dim)
        H = (H + H.T) / 2
        
        solver = DMRGSolver(max_bond_dim=10)
        result = solver.solve(H, n_sites=2, local_dim=2)
        
        # Update hypothesis with result
        log_likelihood = -abs(result.ground_state_energy - 0.5)  # Compare to prediction
        h.update_evidence(log_likelihood)
        
        assert h.log_evidence != 0.0
    
    def test_mitigation_with_hypothesis(self):
        """Test error mitigation improving hypothesis evidence."""
        # Create hypothesis
        h = Hypothesis(id="mit-test", description="Mitigated", track="gaugegap")
        
        # Simulate noisy quantum result
        pec = ProbabilisticErrorCancellation()
        circuit_results = [0.48, 0.52, 0.49, 0.51]
        
        result = pec.mitigate(circuit_results, circuit_depth=5, gate_types=["rx"])
        
        # Use mitigated result for hypothesis
        log_likelihood = -abs(result.mitigated_value - 0.5)
        h.update_evidence(log_likelihood)
        
        assert h.log_evidence > -1.0  # Should be close to prediction


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
