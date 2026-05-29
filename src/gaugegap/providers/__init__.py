"""Quantum provider adapters for hardware and emulator access.

This module provides a unified interface for submitting circuits to different
quantum computing providers (Quantinuum, IBM, AWS Braket, IonQ) while capturing
calibration metadata and maintaining the hardware-ready boundary.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, List
import json


@dataclass
class CalibrationData:
    """Backend calibration metadata."""
    
    backend_name: str
    timestamp: str
    qubit_count: int
    connectivity: str  # "all-to-all", "heavy-hex", "linear", etc.
    t1_median: Optional[float] = None
    t2_median: Optional[float] = None
    gate_fidelity_1q: Optional[float] = None
    gate_fidelity_2q: Optional[float] = None
    readout_error: Optional[float] = None
    additional_properties: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "backend_name": self.backend_name,
            "timestamp": self.timestamp,
            "qubit_count": self.qubit_count,
            "connectivity": self.connectivity,
            "t1_median": self.t1_median,
            "t2_median": self.t2_median,
            "gate_fidelity_1q": self.gate_fidelity_1q,
            "gate_fidelity_2q": self.gate_fidelity_2q,
            "readout_error": self.readout_error,
            "additional_properties": self.additional_properties or {}
        }


@dataclass
class JobMetadata:
    """Metadata for a submitted quantum job."""
    
    job_id: str
    provider: str
    backend_name: str
    hypothesis_id: str
    circuit_depth: int
    qubit_count: int
    shots: int
    timestamp: str
    calibration: CalibrationData
    mitigation_settings: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "job_id": self.job_id,
            "provider": self.provider,
            "backend_name": self.backend_name,
            "hypothesis_id": self.hypothesis_id,
            "circuit_depth": self.circuit_depth,
            "qubit_count": self.qubit_count,
            "shots": self.shots,
            "timestamp": self.timestamp,
            "calibration": self.calibration.to_dict(),
            "mitigation_settings": self.mitigation_settings or {}
        }


class QuantumProvider(ABC):
    """Base class for quantum provider adapters.
    
    All provider implementations must:
    1. Support emulator/simulator mode without credentials
    2. Capture full calibration metadata before hardware submission
    3. Return standardized JobMetadata
    4. Implement credential checking without requiring credentials
    """
    
    def __init__(self, backend_name: str, credentials: Optional[Dict[str, str]] = None):
        """Initialize provider adapter.
        
        Args:
            backend_name: Name of the backend (e.g., "H2-1E", "ibm_brisbane")
            credentials: Optional credentials dict. If None, will attempt to load
                        from environment or config file.
        """
        self.backend_name = backend_name
        self.credentials = credentials
        self._backend = None
    
    @abstractmethod
    def check_credentials(self) -> bool:
        """Check if credentials are available without requiring them.
        
        Returns:
            True if credentials are configured, False otherwise.
        """
        pass
    
    @abstractmethod
    def get_calibration_data(self) -> CalibrationData:
        """Retrieve current backend calibration data.
        
        Returns:
            CalibrationData object with current backend properties.
        """
        pass
    
    @abstractmethod
    def submit_emulator(
        self,
        circuit: Any,
        shots: int = 1024,
        noise_model: Optional[str] = None
    ) -> tuple[Any, JobMetadata]:
        """Submit circuit to emulator/simulator.
        
        Args:
            circuit: Circuit object (provider-specific format)
            shots: Number of measurement shots
            noise_model: Optional noise model ("realistic", "depolarizing", None)
        
        Returns:
            (job, metadata) tuple
        """
        pass
    
    @abstractmethod
    def submit_hardware(
        self,
        circuit: Any,
        shots: int = 1024,
        mitigation: Optional[Dict[str, Any]] = None
    ) -> tuple[Any, JobMetadata]:
        """Submit circuit to hardware backend.
        
        Args:
            circuit: Circuit object (provider-specific format)
            shots: Number of measurement shots
            mitigation: Optional mitigation settings (provider-specific)
        
        Returns:
            (job, metadata) tuple
        
        Raises:
            CredentialsError: If credentials are not available
            HardwareNotReadyError: If hardware readiness checks fail
        """
        pass
    
    @abstractmethod
    def get_result(self, job: Any) -> Any:
        """Retrieve job result.
        
        Args:
            job: Job object returned from submit_emulator or submit_hardware
        
        Returns:
            Result object (provider-specific format)
        """
        pass
    
    def is_hardware_available(self) -> bool:
        """Check if hardware backend is currently available.
        
        Returns:
            True if hardware is operational, False otherwise.
        """
        if not self.check_credentials():
            return False
        try:
            calibration = self.get_calibration_data()
            return calibration.qubit_count > 0
        except Exception:
            return False


class ProviderError(Exception):
    """Base exception for provider errors."""
    pass


class CredentialsError(ProviderError):
    """Raised when credentials are missing or invalid."""
    pass


class HardwareNotReadyError(ProviderError):
    """Raised when hardware readiness checks fail."""
    
    def __init__(self, checks: Dict[str, bool]):
        self.checks = checks
        failed = [k for k, v in checks.items() if not v]
        super().__init__(f"Hardware not ready. Failed checks: {failed}")


def get_provider(
    provider_name: str,
    backend_name: str,
    credentials: Optional[Dict[str, str]] = None
) -> QuantumProvider:
    """Factory function to get provider adapter.
    
    Args:
        provider_name: Provider name ("quantinuum", "ibm", "braket", "ionq")
        backend_name: Backend name (provider-specific)
        credentials: Optional credentials dict
    
    Returns:
        QuantumProvider instance
    
    Raises:
        ValueError: If provider_name is not recognized
    """
    from .quantinuum_adapter import QuantinuumProvider
    from .ibm_adapter import IBMRuntimeProvider
    from .braket_adapter import BraketProvider
    from .ionq_adapter import IonQProvider
    
    providers = {
        "quantinuum": QuantinuumProvider,
        "ibm": IBMRuntimeProvider,
        "braket": BraketProvider,
        "ionq": IonQProvider,
    }
    
    if provider_name.lower() not in providers:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Available: {list(providers.keys())}"
        )
    
    return providers[provider_name.lower()](backend_name, credentials)


__all__ = [
    "QuantumProvider",
    "CalibrationData",
    "JobMetadata",
    "ProviderError",
    "CredentialsError",
    "HardwareNotReadyError",
    "get_provider",
]

# Made with Bob
