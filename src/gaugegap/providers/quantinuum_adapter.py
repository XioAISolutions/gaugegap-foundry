"""Quantinuum H2/Helios adapter for GaugeGap experiments.

This adapter provides access to Quantinuum trapped-ion systems:
- H2-1: 56 qubits, all-to-all connectivity, 2q fidelity ~1e-3
- H2-1E: H2 emulator with realistic noise models
- Helios: 98 qubits, all-to-all connectivity, 2q fidelity ~8e-4

Official SU(2) lattice gauge theory examples exist for this platform.
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


class QuantinuumProvider(QuantumProvider):
    """Adapter for Quantinuum H2/Helios emulators and hardware.
    
    Supports:
    - H2-1E: Emulator with state-vector simulation up to 32 qubits
    - H2-1: 56-qubit trapped-ion hardware
    - Helios: 98-qubit trapped-ion hardware
    
    Emulator modes:
    - noiseless: Ideal state-vector simulation
    - realistic: Hardware-calibrated noise model (gate, leakage, crosstalk, dephasing)
    """
    
    # Known backend specifications
    BACKEND_SPECS = {
        "H2-1E": {
            "qubits": 32,  # State-vector emulation limit
            "connectivity": "all-to-all",
            "type": "emulator"
        },
        "H2-1": {
            "qubits": 56,
            "connectivity": "all-to-all",
            "t1": 1e6,  # ~1 second (very long for trapped ions)
            "t2": 1e5,  # ~100 ms
            "gate_fidelity_1q": 0.9999,
            "gate_fidelity_2q": 0.999,
            "type": "hardware"
        },
        "Helios": {
            "qubits": 98,
            "connectivity": "all-to-all",
            "t1": 1e6,
            "t2": 1e5,
            "gate_fidelity_1q": 0.9999,
            "gate_fidelity_2q": 0.9992,  # ~8e-4 error
            "type": "hardware"
        }
    }
    
    def __init__(self, backend_name: str = "H2-1E", credentials: Optional[Dict[str, str]] = None):
        """Initialize Quantinuum adapter.
        
        Args:
            backend_name: Backend name ("H2-1E", "H2-1", "Helios")
            credentials: Optional dict with "api_key" key
        """
        super().__init__(backend_name, credentials)
        
        if backend_name not in self.BACKEND_SPECS:
            raise ValueError(
                f"Unknown Quantinuum backend: {backend_name}. "
                f"Available: {list(self.BACKEND_SPECS.keys())}"
            )
        
        self.backend_spec = self.BACKEND_SPECS[backend_name]
        self._pytket_backend = None
    
    def check_credentials(self) -> bool:
        """Check if Quantinuum credentials are available.
        
        Returns:
            True if credentials are configured, False otherwise.
        """
        if self.credentials and "api_key" in self.credentials:
            return True
        
        # Check environment variable
        return os.getenv("QUANTINUUM_API_KEY") is not None
    
    def _load_pytket_backend(self):
        """Lazy-load pytket backend (requires pytket-quantinuum)."""
        if self._pytket_backend is not None:
            return self._pytket_backend
        
        try:
            from pytket.extensions.quantinuum import QuantinuumBackend
            
            if self.backend_spec["type"] == "emulator":
                # Emulator doesn't require credentials
                self._pytket_backend = QuantinuumBackend(
                    device_name=self.backend_name
                )
            else:
                # Hardware requires credentials
                if not self.check_credentials():
                    raise CredentialsError(
                        "Quantinuum hardware requires API key. "
                        "Set QUANTINUUM_API_KEY environment variable or pass credentials."
                    )
                
                api_key = (
                    self.credentials.get("api_key")
                    if self.credentials
                    else os.getenv("QUANTINUUM_API_KEY")
                )
                
                self._pytket_backend = QuantinuumBackend(
                    device_name=self.backend_name,
                    api_key=api_key
                )
            
            return self._pytket_backend
            
        except ImportError:
            raise ImportError(
                "pytket-quantinuum is required for Quantinuum integration. "
                "Install with: pip install pytket-quantinuum"
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
            t1_median=spec.get("t1"),
            t2_median=spec.get("t2"),
            gate_fidelity_1q=spec.get("gate_fidelity_1q"),
            gate_fidelity_2q=spec.get("gate_fidelity_2q"),
            additional_properties={
                "type": spec["type"],
                "provider": "quantinuum"
            }
        )
    
    def submit_emulator(
        self,
        circuit: Any,
        shots: int = 1024,
        noise_model: Optional[str] = None
    ) -> tuple[Any, JobMetadata]:
        """Submit circuit to Quantinuum emulator.
        
        Args:
            circuit: pytket Circuit object
            shots: Number of measurement shots
            noise_model: "realistic" for hardware-calibrated noise, None for noiseless
        
        Returns:
            (job_handle, metadata) tuple
        """
        backend = self._load_pytket_backend()
        
        # Compile circuit for backend
        compiled_circuit = backend.get_compiled_circuit(circuit)
        
        # Submit to emulator
        if noise_model == "realistic":
            # Use hardware-calibrated noise model
            job_handle = backend.process_circuit(
                compiled_circuit,
                n_shots=shots,
                noisy_simulation=True
            )
        else:
            # Noiseless state-vector simulation
            job_handle = backend.process_circuit(
                compiled_circuit,
                n_shots=shots,
                noisy_simulation=False
            )
        
        # Create metadata
        metadata = JobMetadata(
            job_id=str(job_handle),
            provider="quantinuum",
            backend_name=self.backend_name,
            hypothesis_id="",  # Will be set by caller
            circuit_depth=compiled_circuit.depth(),
            qubit_count=compiled_circuit.n_qubits,
            shots=shots,
            timestamp=datetime.utcnow().isoformat(),
            calibration=self.get_calibration_data(),
            mitigation_settings={"noise_model": noise_model}
        )
        
        return job_handle, metadata
    
    def submit_hardware(
        self,
        circuit: Any,
        shots: int = 1024,
        mitigation: Optional[Dict[str, Any]] = None
    ) -> tuple[Any, JobMetadata]:
        """Submit circuit to Quantinuum hardware.
        
        Args:
            circuit: pytket Circuit object
            shots: Number of measurement shots
            mitigation: Optional mitigation settings (Quantinuum-specific)
        
        Returns:
            (job_handle, metadata) tuple
        
        Raises:
            CredentialsError: If API key is not available
            HardwareNotReadyError: If hardware checks fail
        """
        if self.backend_spec["type"] == "emulator":
            raise ValueError(
                f"{self.backend_name} is an emulator. Use submit_emulator() instead."
            )
        
        if not self.check_credentials():
            raise CredentialsError(
                "Quantinuum hardware requires API key. "
                "Set QUANTINUUM_API_KEY environment variable."
            )
        
        backend = self._load_pytket_backend()
        
        # Compile circuit for hardware
        compiled_circuit = backend.get_compiled_circuit(circuit)
        
        # Submit to hardware
        job_handle = backend.process_circuit(
            compiled_circuit,
            n_shots=shots
        )
        
        # Create metadata
        metadata = JobMetadata(
            job_id=str(job_handle),
            provider="quantinuum",
            backend_name=self.backend_name,
            hypothesis_id="",  # Will be set by caller
            circuit_depth=compiled_circuit.depth(),
            qubit_count=compiled_circuit.n_qubits,
            shots=shots,
            timestamp=datetime.utcnow().isoformat(),
            calibration=self.get_calibration_data(),
            mitigation_settings=mitigation or {}
        )
        
        return job_handle, metadata
    
    def get_result(self, job: Any) -> Any:
        """Retrieve job result from Quantinuum.
        
        Args:
            job: Job handle returned from submit_emulator or submit_hardware
        
        Returns:
            pytket BackendResult object
        """
        backend = self._load_pytket_backend()
        return backend.get_result(job)
    
    @staticmethod
    def convert_from_qiskit(qiskit_circuit: Any) -> Any:
        """Convert Qiskit circuit to pytket format.
        
        Args:
            qiskit_circuit: Qiskit QuantumCircuit
        
        Returns:
            pytket Circuit
        """
        try:
            from pytket.extensions.qiskit import qiskit_to_tk
            return qiskit_to_tk(qiskit_circuit)
        except ImportError:
            raise ImportError(
                "pytket-qiskit is required for Qiskit conversion. "
                "Install with: pip install pytket-qiskit"
            )
    
    @staticmethod
    def convert_to_qiskit(pytket_circuit: Any) -> Any:
        """Convert pytket circuit to Qiskit format.
        
        Args:
            pytket_circuit: pytket Circuit
        
        Returns:
            Qiskit QuantumCircuit
        """
        try:
            from pytket.extensions.qiskit import tk_to_qiskit
            return tk_to_qiskit(pytket_circuit)
        except ImportError:
            raise ImportError(
                "pytket-qiskit is required for Qiskit conversion. "
                "Install with: pip install pytket-qiskit"
            )


def create_quantinuum_adapter(
    backend_name: str = "H2-1E",
    api_key: Optional[str] = None
) -> QuantinuumProvider:
    """Convenience function to create Quantinuum adapter.
    
    Args:
        backend_name: Backend name ("H2-1E", "H2-1", "Helios")
        api_key: Optional API key (will use environment variable if not provided)
    
    Returns:
        QuantinuumProvider instance
    """
    credentials = {"api_key": api_key} if api_key else None
    return QuantinuumProvider(backend_name, credentials)

# Made with Bob
