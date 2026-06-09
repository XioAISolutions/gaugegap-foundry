"""Tests for Pauli operator grouping."""

import unittest
from gaugegap.quantum.pauli_grouping import (
    pauli_commutes,
    group_pauli_terms,
    estimate_measurement_reduction,
    qiskit_grouped_measurement,
)


class PauliCommutationTests(unittest.TestCase):
    """Test Pauli commutation checking."""
    
    def test_identical_paulis_commute(self):
        """Identical Pauli operators commute."""
        self.assertTrue(pauli_commutes("IXYZ", "IXYZ"))
        self.assertTrue(pauli_commutes("ZZZZ", "ZZZZ"))
        self.assertTrue(pauli_commutes("I", "I"))
    
    def test_all_identity_commutes(self):
        """All-identity operators commute with everything."""
        self.assertTrue(pauli_commutes("IIII", "XYZX"))
        self.assertTrue(pauli_commutes("XYZX", "IIII"))
    
    def test_single_difference_anticommutes(self):
        """Single non-I difference means anticommutation."""
        self.assertFalse(pauli_commutes("IXII", "IYII"))
        self.assertFalse(pauli_commutes("XI", "YI"))
        self.assertFalse(pauli_commutes("ZI", "XI"))
    
    def test_two_differences_commute(self):
        """Two non-I differences means commutation."""
        self.assertTrue(pauli_commutes("XIXI", "IXIX"))
        self.assertTrue(pauli_commutes("XYXY", "YXYX"))
    
    def test_z_operators_commute(self):
        """All-Z operators commute."""
        self.assertTrue(pauli_commutes("ZIZI", "IZIZ"))
        self.assertTrue(pauli_commutes("ZZZZ", "ZIII"))
    
    def test_length_mismatch_raises(self):
        """Different length Pauli strings raise error."""
        with self.assertRaises(ValueError):
            pauli_commutes("XY", "XYZ")


class PauliGroupingTests(unittest.TestCase):
    """Test Pauli operator grouping."""
    
    def test_empty_terms(self):
        """Empty term list returns empty groups."""
        groups = group_pauli_terms([])
        self.assertEqual(len(groups), 0)
    
    def test_single_term(self):
        """Single term creates single group."""
        groups = group_pauli_terms([("XY", 1.0)])
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]), 1)
    
    def test_all_commuting_terms(self):
        """All commuting terms go in one group."""
        terms = [("IZ", 1.0), ("ZI", 1.0), ("ZZ", 1.0)]
        groups = group_pauli_terms(terms)
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0]), 3)
    
    def test_no_commuting_terms(self):
        """Non-commuting terms create separate groups."""
        terms = [("XI", 1.0), ("YI", 1.0), ("ZI", 1.0)]
        groups = group_pauli_terms(terms)
        # Each should be in separate group
        self.assertEqual(len(groups), 3)
    
    def test_mixed_commutation(self):
        """Mixed commutation creates multiple groups."""
        terms = [
            ("IZ", 1.0),  # Group 1
            ("ZI", 1.0),  # Group 1 (commutes with IZ)
            ("XX", 1.0),  # Group 2 (doesn't commute with IZ or ZI)
        ]
        groups = group_pauli_terms(terms)
        self.assertEqual(len(groups), 2)
    
    def test_greedy_strategy(self):
        """Greedy strategy works correctly."""
        terms = [("IZ", 1.0), ("ZI", 1.0), ("XX", 1.0)]
        groups = group_pauli_terms(terms, strategy="greedy")
        self.assertEqual(len(groups), 2)
    
    def test_sorted_strategy(self):
        """Sorted strategy prioritizes larger coefficients."""
        terms = [
            ("IZ", 0.1),
            ("ZI", 0.1),
            ("XX", 10.0),  # Large coefficient
        ]
        groups = group_pauli_terms(terms, strategy="sorted")
        # XX should be in first group due to sorting
        self.assertEqual(groups[0][0][0], "XX")
    
    def test_unknown_strategy_raises(self):
        """Unknown strategy raises error."""
        with self.assertRaises(ValueError):
            group_pauli_terms([("X", 1.0)], strategy="unknown")


class MeasurementReductionTests(unittest.TestCase):
    """Test measurement reduction estimation."""
    
    def test_empty_terms_stats(self):
        """Empty terms return zero stats."""
        stats = estimate_measurement_reduction([])
        self.assertEqual(stats["n_terms"], 0)
        self.assertEqual(stats["n_groups"], 0)
    
    def test_single_term_no_reduction(self):
        """Single term has no reduction."""
        stats = estimate_measurement_reduction([("X", 1.0)])
        self.assertEqual(stats["n_terms"], 1)
        self.assertEqual(stats["n_groups"], 1)
        self.assertEqual(stats["reduction_factor"], 1.0)
    
    def test_all_commuting_max_reduction(self):
        """All commuting terms give maximum reduction."""
        terms = [("IZ", 1.0), ("ZI", 1.0), ("ZZ", 1.0)]
        stats = estimate_measurement_reduction(terms)
        self.assertEqual(stats["n_terms"], 3)
        self.assertEqual(stats["n_groups"], 1)
        self.assertEqual(stats["reduction_factor"], 3.0)
    
    def test_no_commuting_no_reduction(self):
        """No commuting terms give no reduction."""
        terms = [("XI", 1.0), ("YI", 1.0), ("ZI", 1.0)]
        stats = estimate_measurement_reduction(terms)
        self.assertEqual(stats["n_terms"], 3)
        self.assertEqual(stats["n_groups"], 3)
        self.assertEqual(stats["reduction_factor"], 1.0)
    
    def test_partial_reduction(self):
        """Partial commutation gives partial reduction."""
        terms = [
            ("IZ", 1.0),
            ("ZI", 1.0),  # Commutes with IZ
            ("XX", 1.0),  # Separate group
        ]
        stats = estimate_measurement_reduction(terms)
        self.assertEqual(stats["n_terms"], 3)
        self.assertEqual(stats["n_groups"], 2)
        self.assertAlmostEqual(stats["reduction_factor"], 1.5)


class QiskitIntegrationTests(unittest.TestCase):
    """Test Qiskit integration."""
    
    def test_qiskit_grouped_measurement_without_qiskit(self):
        """Without Qiskit, raises helpful error."""
        # This test may pass if Qiskit is installed
        try:
            import qiskit  # noqa: F401
            self.skipTest("Qiskit is installed")
        except ImportError:
            pass
        
        with self.assertRaises(RuntimeError) as ctx:
            qiskit_grouped_measurement([("X", 1.0)])
        self.assertIn("Qiskit", str(ctx.exception))
    
    def test_qiskit_grouped_measurement_with_qiskit(self):
        """With Qiskit, creates SparsePauliOp groups."""
        try:
            from qiskit.quantum_info import SparsePauliOp
        except ImportError:
            self.skipTest("Qiskit not installed")
        
        terms = [("IZ", 1.0), ("ZI", 1.0), ("XX", 1.0)]
        groups = qiskit_grouped_measurement(terms)
        
        # Should create 2 groups
        self.assertEqual(len(groups), 2)
        
        # Each should be a SparsePauliOp
        for group in groups:
            self.assertIsInstance(group, SparsePauliOp)


if __name__ == "__main__":
    unittest.main()

# Made with Bob
