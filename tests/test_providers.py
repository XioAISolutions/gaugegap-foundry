"""Integration tests for quantum provider adapters.

These tests verify the provider adapter interface without requiring
actual hardware credentials. They test:
1. Provider instantiation
2. Credential checking
3. Calibration data retrieval
4. Emulator submission (where available)
"""

import pytest
from pathlib import Path

from gaugegap.providers import (
    get_provider,
    QuantumProvider,
    CalibrationData,
    JobMetadata,
    CredentialsError,
)


class TestProviderFactory:
    """Test the provider factory function."""
    
    def test_get_provider_quantinuum(self):
        """Test getting Quantinuum provider."""
        provider = get_provider("quantinuum", "H2-1E")
        assert provider is not None
        assert provider.backend_name == "H2-1E"
    
    def test_get_provider_ibm(self):
        """Test getting IBM provider."""
        provider = get_provider("ibm", "aer_simulator")
        assert provider is not None
        assert provider.backend_name == "aer_simulator"
    
    def test_get_provider_braket(self):
        """Test getting Braket provider."""
        provider = get_provider("braket", "braket_ahs")
        assert provider is not None
        assert provider.backend_name == "braket_ahs"
    
    def test_get_provider_ionq(self):
        """Test getting IonQ provider."""
        provider = get_provider("ionq", "ionq_simulator")
        assert provider is not None
        assert provider.backend_name == "ionq_simulator"
    
    def test_get_provider_unknown(self):
        """Test that unknown provider raises ValueError."""
        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider("unknown_provider", "backend")


class TestQuantinuumProvider:
    """Test Quantinuum provider adapter."""
    
    def test_instantiate_emulator(self):
        """Test instantiating H2 emulator."""
        provider = get_provider("quantinuum", "H2-1E")
        assert provider.backend_name == "H2-1E"
    
    def test_check_credentials_emulator(self):
        """Test that emulator doesn't require credentials."""
        provider = get_provider("quantinuum", "H2-1E")
        # Emulator should work without credentials
        assert isinstance(provider.check_credentials(), bool)
    
    def test_get_calibration_data(self):
        """Test getting calibration data."""
        provider = get_provider("quantinuum", "H2-1E")
        calibration = provider.get_calibration_data()
        
        assert isinstance(calibration, CalibrationData)
        assert calibration.backend_name == "H2-1E"
        assert calibration.qubit_count == 32  # State-vector limit
        assert calibration.connectivity == "all-to-all"
    
    def test_hardware_backend_specs(self):
        """Test H2 hardware backend specifications."""
        provider = get_provider("quantinuum", "H2-1")
        calibration = provider.get_calibration_data()
        
        assert calibration.qubit_count == 56
        assert calibration.connectivity == "all-to-all"
        assert calibration.gate_fidelity_2q is not None


class TestIBMProvider:
    """Test IBM provider adapter."""
    
    def test_instantiate_aer_simulator(self):
        """Test instantiating Aer simulator."""
        provider = get_provider("ibm", "aer_simulator")
        assert provider.backend_name == "aer_simulator"
    
    def test_check_credentials_simulator(self):
        """Test that Aer simulator doesn't require credentials."""
        provider = get_provider("ibm", "aer_simulator")
        # Aer should work without credentials
        assert provider.check_credentials() is True
    
    def test_get_calibration_data_simulator(self):
        """Test getting calibration data for simulator."""
        provider = get_provider("ibm", "aer_simulator")
        calibration = provider.get_calibration_data()
        
        assert isinstance(calibration, CalibrationData)
        assert calibration.backend_name == "aer_simulator"
        assert calibration.qubit_count == 32
        assert calibration.connectivity == "all-to-all"


class TestBraketProvider:
    """Test Braket provider adapter."""
    
    def test_instantiate_local_ahs(self):
        """Test instantiating local AHS simulator."""
        provider = get_provider("braket", "braket_ahs")
        assert provider.backend_name == "braket_ahs"
    
    def test_check_credentials_local(self):
        """Test that local simulator doesn't require credentials."""
        provider = get_provider("braket", "braket_ahs")
        # Local simulator should work without credentials
        assert provider.check_credentials() is True
    
    def test_get_calibration_data(self):
        """Test getting calibration data."""
        provider = get_provider("braket", "braket_ahs")
        calibration = provider.get_calibration_data()
        
        assert isinstance(calibration, CalibrationData)
        assert calibration.backend_name == "braket_ahs"
        assert calibration.qubit_count == 256  # Aquila-like
        assert calibration.connectivity == "programmable-geometry"
    
    def test_aquila_device_arn(self):
        """Test Aquila device ARN resolution."""
        from gaugegap.providers.braket_adapter import BraketProvider
        provider = get_provider("braket", "aquila")
        assert isinstance(provider, BraketProvider)
        assert provider.device_arn is not None
        assert "Aquila" in provider.device_arn


class TestIonQProvider:
    """Test IonQ provider adapter."""
    
    def test_instantiate_simulator(self):
        """Test instantiating IonQ simulator."""
        provider = get_provider("ionq", "ionq_simulator")
        assert provider.backend_name == "ionq_simulator"
    
    def test_check_credentials_simulator(self):
        """Test that simulator may not require credentials."""
        provider = get_provider("ionq", "ionq_simulator")
        # Simulator should work without credentials (depending on access method)
        assert isinstance(provider.check_credentials(), bool)
    
    def test_get_calibration_data(self):
        """Test getting calibration data."""
        provider = get_provider("ionq", "ionq_simulator")
        calibration = provider.get_calibration_data()
        
        assert isinstance(calibration, CalibrationData)
        assert calibration.backend_name == "ionq_simulator"
        assert calibration.qubit_count == 29
        assert calibration.connectivity == "all-to-all"
    
    def test_forte_backend_specs(self):
        """Test Forte hardware backend specifications."""
        provider = get_provider("ionq", "ionq_forte")
        calibration = provider.get_calibration_data()
        
        assert calibration.qubit_count == 36
        assert calibration.connectivity == "all-to-all"
        assert calibration.gate_fidelity_2q is not None


class TestCalibrationData:
    """Test CalibrationData dataclass."""
    
    def test_to_dict(self):
        """Test converting calibration data to dict."""
        calibration = CalibrationData(
            backend_name="test_backend",
            timestamp="2026-05-28T19:00:00Z",
            qubit_count=10,
            connectivity="all-to-all",
            t1_median=100.0,
            t2_median=50.0,
            gate_fidelity_1q=0.999,
            gate_fidelity_2q=0.99,
            readout_error=0.01,
            additional_properties={"test": "value"}
        )
        
        data = calibration.to_dict()
        assert data["backend_name"] == "test_backend"
        assert data["qubit_count"] == 10
        assert data["t1_median"] == 100.0
        assert data["additional_properties"]["test"] == "value"


class TestJobMetadata:
    """Test JobMetadata dataclass."""
    
    def test_to_dict(self):
        """Test converting job metadata to dict."""
        calibration = CalibrationData(
            backend_name="test_backend",
            timestamp="2026-05-28T19:00:00Z",
            qubit_count=10,
            connectivity="all-to-all"
        )
        
        metadata = JobMetadata(
            job_id="test_job_123",
            provider="test_provider",
            backend_name="test_backend",
            hypothesis_id="gaugegap-0002",
            circuit_depth=50,
            qubit_count=10,
            shots=1024,
            timestamp="2026-05-28T19:00:00Z",
            calibration=calibration,
            mitigation_settings={"resilience_level": 2}
        )
        
        data = metadata.to_dict()
        assert data["job_id"] == "test_job_123"
        assert data["provider"] == "test_provider"
        assert data["shots"] == 1024
        assert data["mitigation_settings"]["resilience_level"] == 2
        assert data["calibration"]["backend_name"] == "test_backend"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
