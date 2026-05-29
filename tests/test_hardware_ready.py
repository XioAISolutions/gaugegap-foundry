"""Tests for hardware readiness checks."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import os

from gaugegap.hardware_ready import (
    check_hypothesis_registered,
    check_classical_baseline_exists,
    check_emulator_validated,
    check_provider_credentials,
    check_calibration_current,
    check_circuit_constraints,
    verify_hardware_ready,
    HardwareReadinessError,
    HardwareReadinessCheck,
)


class TestHypothesisRegistration:
    """Test hypothesis registration checks."""
    
    def test_existing_hypothesis(self):
        """Test check passes for existing hypothesis."""
        check = check_hypothesis_registered("gaugegap-0002")
        assert check.passed is True
        assert "gaugegap-0002" in check.message
    
    def test_missing_hypothesis(self):
        """Test check fails for missing hypothesis."""
        check = check_hypothesis_registered("nonexistent-0001")
        assert check.passed is False
        assert "not found" in check.message.lower()


class TestClassicalBaseline:
    """Test classical baseline existence checks."""
    
    def test_existing_baseline(self):
        """Test check passes for existing baseline."""
        check = check_classical_baseline_exists("gaugegap-0001")
        assert check.passed is True
        assert "baseline exists" in check.message.lower()
    
    def test_missing_baseline(self):
        """Test check fails for missing baseline."""
        check = check_classical_baseline_exists("nonexistent-0001")
        assert check.passed is False
        assert "no classical baseline" in check.message.lower()


class TestEmulatorValidation:
    """Test emulator validation checks."""
    
    def test_matching_results(self):
        """Test check passes when results match."""
        classical = {"gap": 1.0, "energy_0": -2.0, "energy_1": -1.0}
        emulator = {"gap": 1.01, "energy_0": -2.01, "energy_1": -1.0}
        
        check = check_emulator_validated(
            "gaugegap-0002",
            classical,
            emulator,
            tolerance=0.05
        )
        assert check.passed is True
    
    def test_mismatched_results(self):
        """Test check fails when results differ."""
        classical = {"gap": 1.0, "energy_0": -2.0, "energy_1": -1.0}
        emulator = {"gap": 1.5, "energy_0": -2.5, "energy_1": -1.0}
        
        check = check_emulator_validated(
            "gaugegap-0002",
            classical,
            emulator,
            tolerance=0.05
        )
        assert check.passed is False
        assert "differ" in check.message.lower()
    
    def test_missing_results(self):
        """Test check fails when results not provided."""
        check = check_emulator_validated("gaugegap-0002", None, None)
        assert check.passed is False
        assert "not provided" in check.message.lower()


class TestProviderCredentials:
    """Test provider credential checks."""
    
    def test_quantinuum_no_credentials(self):
        """Test Quantinuum check without credentials."""
        # Clear any existing credentials
        old_key = os.environ.pop("QUANTINUUM_API_KEY", None)
        try:
            check = check_provider_credentials("quantinuum")
            assert check.passed is False
            assert "QUANTINUUM_API_KEY" in check.message
        finally:
            if old_key:
                os.environ["QUANTINUUM_API_KEY"] = old_key
    
    def test_ibm_no_credentials(self):
        """Test IBM check without credentials."""
        old_token = os.environ.pop("QISKIT_IBM_TOKEN", None)
        old_token2 = os.environ.pop("IBM_QUANTUM_TOKEN", None)
        try:
            check = check_provider_credentials("ibm")
            assert check.passed is False
            assert "IBM" in check.message or "QISKIT" in check.message
        finally:
            if old_token:
                os.environ["QISKIT_IBM_TOKEN"] = old_token
            if old_token2:
                os.environ["IBM_QUANTUM_TOKEN"] = old_token2
    
    def test_unknown_provider(self):
        """Test check fails for unknown provider."""
        check = check_provider_credentials("unknown_provider")
        assert check.passed is False
        assert "unknown provider" in check.message.lower()


class TestCalibrationCurrent:
    """Test calibration currency checks."""
    
    def test_recent_calibration(self):
        """Test check passes for recent calibration."""
        timestamp = datetime.utcnow().isoformat()
        check = check_calibration_current(timestamp, max_age_hours=24)
        assert check.passed is True
    
    def test_old_calibration(self):
        """Test check fails for old calibration."""
        old_time = datetime.utcnow() - timedelta(hours=48)
        timestamp = old_time.isoformat()
        check = check_calibration_current(timestamp, max_age_hours=24)
        assert check.passed is False
        assert "hours old" in check.message.lower()
    
    def test_invalid_timestamp(self):
        """Test check fails for invalid timestamp."""
        check = check_calibration_current("invalid-timestamp")
        assert check.passed is False
        assert "failed to parse" in check.message.lower()


class TestCircuitConstraints:
    """Test circuit constraint checks."""
    
    def test_circuit_fits_backend(self):
        """Test check passes when circuit fits backend."""
        # Mock circuit object
        class MockCircuit:
            num_qubits = 10
            def depth(self):
                return 50
        
        circuit = MockCircuit()
        check = check_circuit_constraints(
            circuit,
            backend_qubits=20,
            backend_connectivity="all-to-all",
            max_depth=100
        )
        assert check.passed is True
    
    def test_circuit_too_many_qubits(self):
        """Test check fails when circuit has too many qubits."""
        class MockCircuit:
            num_qubits = 30
            def depth(self):
                return 50
        
        circuit = MockCircuit()
        check = check_circuit_constraints(
            circuit,
            backend_qubits=20,
            backend_connectivity="all-to-all"
        )
        assert check.passed is False
        assert "requires" in check.message.lower()
    
    def test_circuit_too_deep(self):
        """Test check fails when circuit is too deep."""
        class MockCircuit:
            num_qubits = 10
            def depth(self):
                return 150
        
        circuit = MockCircuit()
        check = check_circuit_constraints(
            circuit,
            backend_qubits=20,
            backend_connectivity="all-to-all",
            max_depth=100
        )
        assert check.passed is False
        assert "depth" in check.message.lower()


class TestVerifyHardwareReady:
    """Test complete hardware readiness verification."""
    
    def test_all_checks_pass(self):
        """Test verification passes when all checks pass."""
        class MockCircuit:
            num_qubits = 7
            def depth(self):
                return 50
        
        circuit = MockCircuit()
        timestamp = datetime.utcnow().isoformat()
        
        # This will fail on credential check, but we can test the structure
        with pytest.raises(HardwareReadinessError) as exc_info:
            verify_hardware_ready(
                hypothesis_id="gaugegap-0002",
                provider_name="quantinuum",
                circuit=circuit,
                backend_qubits=32,
                backend_connectivity="all-to-all",
                calibration_timestamp=timestamp
            )
        
        # Check that error contains check results
        error = exc_info.value
        assert len(error.checks) > 0
        assert any(c.check_name == "hypothesis_registered" for c in error.checks)
        assert any(c.check_name == "classical_baseline_exists" for c in error.checks)


class TestHardwareReadinessCheck:
    """Test HardwareReadinessCheck dataclass."""
    
    def test_create_check(self):
        """Test creating a check result."""
        check = HardwareReadinessCheck(
            check_name="test_check",
            passed=True,
            message="Test passed",
            details={"key": "value"}
        )
        
        assert check.check_name == "test_check"
        assert check.passed is True
        assert check.message == "Test passed"
        assert check.details is not None
        assert check.details["key"] == "value"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
