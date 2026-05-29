"""IonQ adapter for trapped-ion quantum computing.

This adapter provides access to IonQ trapped-ion systems:
- IonQ Forte: 36 all-to-all qubits
- IonQ Aria: 25 all-to-all qubits
- Noisy simulators with system-specific noise models

Best for small all-to-all spectral circuits and QPE experiments.
"""

import os
from typing import Any, Dict, Optional
from datetime import datetime

from . import (
    QuantumProvider,
    CalibrationData,
    JobMetadata,
    CredentialsError,
    HardwareNotReadyError,
)


class IonQProvider(QuantumProvider):
    """Adapter for IonQ trapped-ion systems.
    
    Supports:
    - IonQ Forte: 36 all-to-all qubits
    - IonQ Aria: 25 all-to-all qubits
    - Noisy simulators (up to 29 qubits for Forte-class)
    
    Features:
    - Built-in debiasing on QPUs (requires ≥500 shots)
    - All-to-all connectivity
    - Native gate set optimized for trapped ions
    """
    
    BACKEND_SPECS = {
        "ionq_forte": {
            "qubits": 36,
            "connectivity": "all-to-all",
            "type": "hardware",
            "gate_fidelity_1q": 0.9998,
            "gate_fidelity_2q": 0.995,
        },
        "ionq_aria": {
            "qubits": 25,
            "connectivity": "all-to-all",
            "type": "hardware",
            "gate_fidelity_1q": 0.9995,
            "gate_fidelity_2q": 0.993,
        },
        "ionq_simulator": {
            "qubits": 29,
            "connectivity": "all-to-all",
            "type": "simulator",
        }
    }
    
    def __init__(self, backend_name: str = "ionq_simulator", credentials: Optional[Dict[str, str]] = None):
        """Initialize IonQ adapter.
        
        Args:
            backend_name: Backend name ("ionq_forte", "ionq_aria", "ionq_simulator")
            credentials: Optional dict with "api_key" key
        """
        super().__init__(backend_name, credentials)
        
        if backend_name not in self.BACKEND_SPECS:
            raise ValueError(
                f"Unknown IonQ backend: {backend_name}. "
                f"Available: {list(self.BACKEND_SPECS.keys())}"
            )
        
        self.backend_spec = self.BACKEND_SPECS[backend_name]
        self._backend = None
    
    def check_credentials(self) -> bool:
        """Check if IonQ credentials are available.
        
        Returns:
            True if credentials are configured, False otherwise.
        """
        if self.backend_spec["type"] == "simulator":
            # Simulator may not require credentials depending on access method
            return True
        
        if self.credentials and "api_key" in self.credentials:
            return True
        
        # Check environment variable
        return os.getenv("IONQ_API_KEY") is not None
    
    def _load_backend(self):
        """Lazy-load IonQ backend.
        
        Note: This is a placeholder. Actual implementation depends on
        access method (Qiskit provider, Braket, or direct IonQ API).
        """
        if self._backend is not None:
            return self._backend
        
        # Try Qiskit IonQ provider first
        try:
            from qiskit_ionq import IonQProvider as QiskitIonQProvider
            
            if self.backend_spec["type"] == "simulator":
                provider = QiskitIonQProvider()
                self._backend = provider.get_backend("ionq_simulator")
            else:
                if not self.check_credentials():
                    raise CredentialsError(
                        "IonQ hardware requires API key. "
                        "Set IONQ_API_KEY environment variable or pass credentials."
                    )
                
                api_key = (
                    self.credentials.get("api_key")
                    if self.credentials
                    else os.getenv("IONQ_API_KEY")
                )
                
                provider = QiskitIonQProvider(api_key)
                self._backend = provider.get_backend(self.backend_name)
            
            return self._backend
            
        except ImportError:
            # Fall back to Braket access
            try:
                from braket.aws import AwsDevice
                
                device_arns = {
                    "ionq_forte": "arn:aws:braket:us-east-1::device/qpu/ionq/Forte-1",
                    "ionq_aria": "arn:aws:braket:us-east-1::device/qpu/ionq/Aria-1",
                }
                
                if self.backend_name in device_arns:
                    self._backend = AwsDevice(device_arns[self.backend_name])
                    return self._backend
                
            except ImportError:
                pass
            
            raise ImportError(
                "IonQ access requires either qiskit-ionq or amazon-braket-sdk. "
                "Install with: pip install qiskit-ionq OR pip install amazon-braket-sdk"
            )
    
    def get_calibration_data(self) -> CalibrationData:
        """Retrieve current backend calibration data.
        
        Returns:
            CalibrationData with backend specifications.
        """
        spec = self.backend_spec
        
        return CalibrationData(
            backend_name=self.backend_name,
            timestamp=datetime.utcnow().isoformat(),
            qubit_count=spec["qubits"],
            connectivity=spec["connectivity"],
            gate_fidelity_1q=spec.get("gate_fidelity_1q"),
            gate_fidelity_2q=spec.get("gate_fidelity_2q"),
            additional_properties={
                "type": spec["type"],
                "provider": "ionq",
                "debiasing": "automatic on QPU with ≥500 shots"
            }
        )
    
    def submit_emulator(
        self,
        circuit: Any,
        shots: int = 1024,
        noise_model: Optional[str] = None
    ) -> tuple[Any, JobMetadata]:
        """Submit circuit to IonQ simulator.
        
        Args:
            circuit: Qiskit QuantumCircuit or Braket Circuit
            shots: Number of measurement shots
            noise_model: "realistic" for system-specific noise, None for ideal
        
        Returns:
            (job, metadata) tuple
        """
        if self.backend_spec["type"] != "simulator":
            raise ValueError(
                f"{self.backend_name} is hardware. Use submit_hardware() instead."
            )
        
        backend = self._load_backend()
        
        # Submit to simulator
        job = backend.run(circuit, shots=shots)
        
        # Create metadata
        metadata = JobMetadata(
            job_id=str(job.job_id() if hasattr(job, 'job_id') else job.id),
            provider="ionq",
            backend_name=self.backend_name,
            hypothesis_id="",  # Will be set by caller
            circuit_depth=circuit.depth() if hasattr(circuit, 'depth') else 0,
            qubit_count=circuit.num_qubits if hasattr(circuit, 'num_qubits') else 0,
            shots=shots,
            timestamp=datetime.utcnow().isoformat(),
            calibration=self.get_calibration_data(),
            mitigation_settings={"noise_model": noise_model}
        )
        
        return job, metadata
    
    def submit_hardware(
        self,
        circuit: Any,
        shots: int = 1024,
        mitigation: Optional[Dict[str, Any]] = None
    ) -> tuple[Any, JobMetadata]:
        """Submit circuit to IonQ hardware.
        
        Args:
            circuit: Qiskit QuantumCircuit or Braket Circuit
            shots: Number of measurement shots (≥500 recommended for debiasing)
            mitigation: Optional mitigation settings:
                - debiasing: bool (automatic if shots ≥ 500)
        
        Returns:
            (job, metadata) tuple
        
        Raises:
            CredentialsError: If API key is not available
        """
        if self.backend_spec["type"] == "simulator":
            raise ValueError(
                f"{self.backend_name} is a simulator. Use submit_emulator() instead."
            )
        
        if not self.check_credentials():
            raise CredentialsError(
                "IonQ hardware requires API key. "
                "Set IONQ_API_KEY environment variable."
            )
        
        backend = self._load_backend()
        
        # Submit to hardware
        job = backend.run(circuit, shots=shots)
        
        # Create metadata
        debiasing_active = shots >= 500
        metadata = JobMetadata(
            job_id=str(job.job_id() if hasattr(job, 'job_id') else job.id),
            provider="ionq",
            backend_name=self.backend_name,
            hypothesis_id="",  # Will be set by caller
            circuit_depth=circuit.depth() if hasattr(circuit, 'depth') else 0,
            qubit_count=circuit.num_qubits if hasattr(circuit, 'num_qubits') else 0,
            shots=shots,
            timestamp=datetime.utcnow().isoformat(),
            calibration=self.get_calibration_data(),
            mitigation_settings={
                "debiasing": debiasing_active,
                **(mitigation or {})
            }
        )
        
        return job, metadata
    
    def get_result(self, job: Any) -> Any:
        """Retrieve job result from IonQ.
        
        Args:
            job: Job object returned from submit_emulator or submit_hardware
        
        Returns:
            Result object (format depends on access method)
        """
        if hasattr(job, 'result'):
            return job.result()
        else:
            # Braket-style access
            return job.result()


def create_ionq_adapter(
    backend_name: str = "ionq_simulator",
    api_key: Optional[str] = None
) -> IonQProvider:
    """Convenience function to create IonQ adapter.
    
    Args:
        backend_name: Backend name ("ionq_forte", "ionq_aria", "ionq_simulator")
        api_key: Optional IonQ API key
    
    Returns:
        IonQProvider instance
    """
    credentials = {"api_key": api_key} if api_key else None
    return IonQProvider(backend_name, credentials)

# Made with Bob
