"""AWS Braket adapter for QuEra Aquila and other Braket backends.

This adapter provides access to AWS Braket quantum systems:
- QuEra Aquila: 256-qubit programmable neutral-atom array with AHS
- Local AHS simulator for protocol validation
- Other Braket backends (IonQ, Rigetti, etc.)

Best for analogue gauge-theory experiments and string-breaking dynamics.
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


class BraketProvider(QuantumProvider):
    """Adapter for AWS Braket quantum systems.
    
    Supports:
    - QuEra Aquila: arn:aws:braket:us-east-1::device/qpu/quera/Aquila
    - Local AHS simulator: braket_ahs (local)
    - Other Braket devices via ARN
    """
    
    DEVICE_ARNS = {
        "aquila": "arn:aws:braket:us-east-1::device/qpu/quera/Aquila",
        "ionq_aria": "arn:aws:braket:us-east-1::device/qpu/ionq/Aria-1",
        "rigetti_aspen": "arn:aws:braket:us-west-1::device/qpu/rigetti/Aspen-M-3",
    }
    
    def __init__(self, backend_name: str = "braket_ahs", credentials: Optional[Dict[str, str]] = None):
        """Initialize Braket adapter.
        
        Args:
            backend_name: Backend name ("aquila", "braket_ahs", or device ARN)
            credentials: Optional dict with AWS credentials
        """
        super().__init__(backend_name, credentials)
        self.is_local = backend_name == "braket_ahs"
        self.device_arn = self._resolve_device_arn(backend_name)
        self._device = None
    
    def _resolve_device_arn(self, backend_name: str) -> Optional[str]:
        """Resolve backend name to device ARN."""
        if backend_name == "braket_ahs":
            return None  # Local simulator
        
        if backend_name in self.DEVICE_ARNS:
            return self.DEVICE_ARNS[backend_name]
        
        if backend_name.startswith("arn:aws:braket:"):
            return backend_name
        
        raise ValueError(
            f"Unknown Braket backend: {backend_name}. "
            f"Available: {list(self.DEVICE_ARNS.keys())} or provide full ARN"
        )
    
    def check_credentials(self) -> bool:
        """Check if AWS credentials are available.
        
        Returns:
            True if credentials are configured, False otherwise.
        """
        if self.is_local:
            # Local simulator doesn't require credentials
            return True
        
        if self.credentials:
            return all(k in self.credentials for k in ["aws_access_key_id", "aws_secret_access_key"])
        
        # Check environment variables
        return all(os.getenv(k) for k in ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"])
    
    def _load_device(self):
        """Lazy-load Braket device."""
        if self._device is not None:
            return self._device
        
        try:
            from braket.devices import LocalSimulator
            from braket.aws import AwsDevice
        except ImportError:
            raise ImportError(
                "amazon-braket-sdk is required for Braket integration. "
                "Install with: pip install amazon-braket-sdk"
            )
        
        if self.is_local:
            self._device = LocalSimulator("braket_ahs")
            return self._device
        
        if not self.check_credentials():
            raise CredentialsError(
                "AWS credentials required for Braket hardware. "
                "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables."
            )
        
        self._device = AwsDevice(self.device_arn)
        return self._device
    
    def get_calibration_data(self) -> CalibrationData:
        """Retrieve current backend calibration data.
        
        Returns:
            CalibrationData with device properties.
        """
        if self.is_local:
            return CalibrationData(
                backend_name=self.backend_name,
                timestamp=datetime.utcnow().isoformat(),
                qubit_count=256,  # Aquila-like for local AHS
                connectivity="programmable-geometry",
                additional_properties={
                    "type": "local_simulator",
                    "provider": "braket_ahs"
                }
            )
        
        device = self._load_device()
        
        try:
            properties = device.properties
            
            # Extract device-specific properties
            if "aquila" in self.backend_name.lower() or "quera" in str(self.device_arn).lower():
                return CalibrationData(
                    backend_name=self.backend_name,
                    timestamp=datetime.utcnow().isoformat(),
                    qubit_count=256,
                    connectivity="programmable-geometry",
                    additional_properties={
                        "type": "neutral_atom",
                        "provider": "quera",
                        "paradigm": "analog_hamiltonian_simulation",
                        "properties": str(properties)
                    }
                )
            else:
                # Generic Braket device
                return CalibrationData(
                    backend_name=self.backend_name,
                    timestamp=datetime.utcnow().isoformat(),
                    qubit_count=getattr(properties, 'qubit_count', 0),
                    connectivity="device-specific",
                    additional_properties={
                        "type": "hardware",
                        "provider": "braket",
                        "properties": str(properties)
                    }
                )
        except Exception as e:
            return CalibrationData(
                backend_name=self.backend_name,
                timestamp=datetime.utcnow().isoformat(),
                qubit_count=0,
                connectivity="unknown",
                additional_properties={
                    "type": "hardware",
                    "provider": "braket",
                    "error": str(e)
                }
            )
    
    def submit_emulator(
        self,
        circuit: Any,
        shots: int = 1024,
        noise_model: Optional[str] = None
    ) -> tuple[Any, JobMetadata]:
        """Submit program to local Braket simulator.
        
        Args:
            circuit: Braket Circuit or AHS Program
            shots: Number of measurement shots
            noise_model: Not used for Braket local simulator
        
        Returns:
            (task, metadata) tuple
        """
        if not self.is_local:
            raise ValueError(
                f"{self.backend_name} is hardware. Use submit_hardware() instead."
            )
        
        device = self._load_device()
        
        # Run on local simulator
        task = device.run(circuit, shots=shots)
        
        # Create metadata
        metadata = JobMetadata(
            job_id=str(task.id),
            provider="braket_local",
            backend_name=self.backend_name,
            hypothesis_id="",  # Will be set by caller
            circuit_depth=getattr(circuit, 'depth', 0),
            qubit_count=getattr(circuit, 'qubit_count', 0),
            shots=shots,
            timestamp=datetime.utcnow().isoformat(),
            calibration=self.get_calibration_data(),
            mitigation_settings={}
        )
        
        return task, metadata
    
    def submit_hardware(
        self,
        circuit: Any,
        shots: int = 100,
        mitigation: Optional[Dict[str, Any]] = None
    ) -> tuple[Any, JobMetadata]:
        """Submit program to Braket hardware.
        
        Args:
            circuit: Braket Circuit or AHS Program
            shots: Number of measurement shots
            mitigation: Optional device-specific settings
        
        Returns:
            (task, metadata) tuple
        
        Raises:
            CredentialsError: If AWS credentials are not available
        """
        if self.is_local:
            raise ValueError(
                f"{self.backend_name} is a local simulator. Use submit_emulator() instead."
            )
        
        if not self.check_credentials():
            raise CredentialsError(
                "AWS credentials required for Braket hardware. "
                "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY."
            )
        
        device = self._load_device()
        
        # Submit to hardware
        task = device.run(circuit, shots=shots)
        
        # Create metadata
        metadata = JobMetadata(
            job_id=task.id,
            provider="braket",
            backend_name=self.backend_name,
            hypothesis_id="",  # Will be set by caller
            circuit_depth=getattr(circuit, 'depth', 0),
            qubit_count=getattr(circuit, 'qubit_count', 0),
            shots=shots,
            timestamp=datetime.utcnow().isoformat(),
            calibration=self.get_calibration_data(),
            mitigation_settings=mitigation or {}
        )
        
        return task, metadata
    
    def get_result(self, job: Any) -> Any:
        """Retrieve task result from Braket.
        
        Args:
            job: Task object returned from submit_emulator or submit_hardware
        
        Returns:
            Braket result object
        """
        return job.result()
    
    @staticmethod
    def create_ahs_program(
        geometry: Any,
        pulse_schedule: Any,
        **kwargs
    ) -> Any:
        """Create AHS program for Aquila.
        
        Args:
            geometry: AtomArrangement defining qubit positions
            pulse_schedule: Driving field schedule
            **kwargs: Additional AHS parameters
        
        Returns:
            AnalogHamiltonianSimulation program
        """
        try:
            from braket.ahs.analog_hamiltonian_simulation import AnalogHamiltonianSimulation
        except ImportError:
            raise ImportError(
                "amazon-braket-sdk is required for AHS programs. "
                "Install with: pip install amazon-braket-sdk"
            )
        
        return AnalogHamiltonianSimulation(
            register=geometry,
            hamiltonian=pulse_schedule,
            **kwargs
        )


def create_braket_adapter(
    backend_name: str = "braket_ahs",
    aws_access_key_id: Optional[str] = None,
    aws_secret_access_key: Optional[str] = None
) -> BraketProvider:
    """Convenience function to create Braket adapter.
    
    Args:
        backend_name: Backend name ("aquila", "braket_ahs", or ARN)
        aws_access_key_id: Optional AWS access key
        aws_secret_access_key: Optional AWS secret key
    
    Returns:
        BraketProvider instance
    """
    credentials = None
    if aws_access_key_id and aws_secret_access_key:
        credentials = {
            "aws_access_key_id": aws_access_key_id,
            "aws_secret_access_key": aws_secret_access_key
        }
    
    return BraketProvider(backend_name, credentials)

# Made with Bob
