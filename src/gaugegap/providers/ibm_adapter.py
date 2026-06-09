"""IBM Qiskit Runtime adapter for FlowGap and GaugeGap experiments.

This adapter provides access to IBM Quantum systems via Qiskit Runtime:
- Local Aer simulators (statevector, sampler with noise models)
- IBM Runtime Estimator/Sampler with error mitigation
- IBM hardware backends (Heron, Eagle, etc.)

Supports QUICK-PDE for Burgers/Poisson benchmarks (Premium/Flex/On-Prem).

Qiskit 2.4+ compatible with proper session management and resource cleanup.
"""

import os
import logging
from typing import Any, Dict, Optional, List
from datetime import datetime, timezone
from contextlib import contextmanager

from . import (
    QuantumProvider,
    CalibrationData,
    JobMetadata,
    CredentialsError,
    HardwareNotReadyError,
)

logger = logging.getLogger(__name__)


class IBMRuntimeProvider(QuantumProvider):
    """Adapter for IBM Qiskit Runtime and Aer simulators.
    
    Supports:
    - Local Aer simulators: "aer_simulator", "aer_simulator_statevector"
    - IBM Runtime hardware: any operational IBM backend
    
    Mitigation options (Runtime):
    - resilience_level: 0 (none), 1 (basic), 2 (advanced)
    - dynamical_decoupling: enable/disable
    - twirling: enable_gates, enable_measure
    - ZNE: zero-noise extrapolation
    """
    
    def __init__(self, backend_name: str = "aer_simulator", credentials: Optional[Dict[str, str]] = None):
        """Initialize IBM Runtime adapter.
        
        Args:
            backend_name: Backend name ("aer_simulator", "ibm_brisbane", etc.)
            credentials: Optional dict with "token" and "instance" keys
        """
        super().__init__(backend_name, credentials)
        self._service = None
        self._backend = None
        self._session = None
        self.is_simulator = backend_name.startswith("aer_")
    
    def check_credentials(self) -> bool:
        """Check if IBM Quantum credentials are available.
        
        Returns:
            True if credentials are configured, False otherwise.
        """
        if self.is_simulator:
            # Aer simulators don't require credentials
            return True
        
        if self.credentials and "token" in self.credentials:
            return True
        
        # Check for saved account
        try:
            from qiskit_ibm_runtime import QiskitRuntimeService
            QiskitRuntimeService.saved_accounts()
            return True
        except Exception:
            return False
    
    def _load_service(self):
        """Lazy-load Qiskit Runtime service."""
        if self._service is not None:
            return self._service
        
        if self.is_simulator:
            # Aer simulators don't need service
            return None
        
        try:
            from qiskit_ibm_runtime import QiskitRuntimeService
            
            if self.credentials and "token" in self.credentials:
                # Qiskit 2.4+ channel parameter - use ibm_cloud for most cases
                # The instance parameter determines the actual hub/group/project
                self._service = QiskitRuntimeService(
                    token=self.credentials["token"],
                    instance=self.credentials.get("instance")
                )
            else:
                # Try to use saved account
                self._service = QiskitRuntimeService()
            
            return self._service
            
        except ImportError:
            raise ImportError(
                "qiskit-ibm-runtime is required for IBM integration. "
                "Install with: pip install qiskit-ibm-runtime"
            )
        except Exception as e:
            raise CredentialsError(
                f"Failed to load IBM Runtime service: {e}. "
                "Save account with: QiskitRuntimeService.save_account(token='...', instance='...')"
            )
    
    def _load_backend(self):
        """Lazy-load backend."""
        if self._backend is not None:
            return self._backend
        
        if self.is_simulator:
            try:
                from qiskit_aer import AerSimulator
                self._backend = AerSimulator()
                return self._backend
            except ImportError:
                raise ImportError(
                    "qiskit-aer is required for Aer simulators. "
                    "Install with: pip install qiskit-aer"
                )
        else:
            service = self._load_service()
            self._backend = service.backend(self.backend_name)
            return self._backend
    
    def get_calibration_data(self) -> CalibrationData:
        """Retrieve current backend calibration data.
        
        Returns:
            CalibrationData with backend properties.
        """
        if self.is_simulator:
            return CalibrationData(
                backend_name=self.backend_name,
                timestamp=datetime.now(timezone.utc).isoformat(),
                qubit_count=32,  # Typical Aer limit for statevector
                connectivity="all-to-all",
                additional_properties={
                    "type": "simulator",
                    "provider": "ibm_aer"
                }
            )
        
        backend = self._load_backend()
        
        try:
            # Qiskit 2.4+ uses backend.target for calibration data
            # backend.properties() and backend.configuration() are deprecated
            target = getattr(backend, 'target', None)
            num_qubits = backend.num_qubits if hasattr(backend, 'num_qubits') else 0
            
            # Try to extract T1/T2 from target if available
            t1_values = []
            t2_values = []
            gate_errors_1q = []
            gate_errors_2q = []
            readout_errors = []
            
            if target is not None:
                # Extract qubit properties from target
                for qubit in range(num_qubits):
                    try:
                        # Get T1 if available
                        t1 = target.qubit_properties(qubit).t1 if target.qubit_properties(qubit) else None
                        if t1 is not None:
                            t1_values.append(t1)
                        
                        # Get T2 if available
                        t2 = target.qubit_properties(qubit).t2 if target.qubit_properties(qubit) else None
                        if t2 is not None:
                            t2_values.append(t2)
                    except (AttributeError, TypeError):
                        pass
                
                # Extract gate errors from target
                for instruction_name in target.operation_names:
                    try:
                        for qargs in target.qargs_for_operation_name(instruction_name):
                            props = target[instruction_name].get(qargs, None)
                            if props and hasattr(props, 'error') and props.error is not None:
                                if len(qargs) == 1:
                                    gate_errors_1q.append(props.error)
                                elif len(qargs) == 2:
                                    gate_errors_2q.append(props.error)
                    except (AttributeError, TypeError, KeyError):
                        pass
            
            # Get basis gates
            basis_gates = list(target.operation_names) if target else []
            
            # Get coupling map
            coupling_map = getattr(backend, 'coupling_map', None)
            connectivity = "all-to-all" if coupling_map is None else f"{len(coupling_map)} edges"
            
            return CalibrationData(
                backend_name=self.backend_name,
                timestamp=datetime.now(timezone.utc).isoformat(),
                qubit_count=num_qubits,
                connectivity=connectivity,
                t1_median=sum(t1_values) / len(t1_values) if t1_values else None,
                t2_median=sum(t2_values) / len(t2_values) if t2_values else None,
                gate_fidelity_1q=1.0 - (sum(gate_errors_1q) / len(gate_errors_1q)) if gate_errors_1q else None,
                gate_fidelity_2q=1.0 - (sum(gate_errors_2q) / len(gate_errors_2q)) if gate_errors_2q else None,
                readout_error=sum(readout_errors) / len(readout_errors) if readout_errors else None,
                additional_properties={
                    "type": "hardware",
                    "provider": "ibm_quantum",
                    "basis_gates": basis_gates[:10] if len(basis_gates) > 10 else basis_gates  # Limit for readability
                }
            )
        except Exception as e:
            logger.warning(f"Failed to extract detailed calibration data: {e}")
            # Fallback if properties not available
            return CalibrationData(
                backend_name=self.backend_name,
                timestamp=datetime.now(timezone.utc).isoformat(),
                qubit_count=backend.num_qubits if hasattr(backend, 'num_qubits') else 0,
                connectivity="unknown",
                additional_properties={
                    "type": "hardware",
                    "provider": "ibm_quantum",
                    "error": str(e)
                }
            )
    
    def submit_emulator(
        self,
        circuit: Any,
        shots: int = 1024,
        noise_model: Optional[str] = None
    ) -> tuple[Any, JobMetadata]:
        """Submit circuit to Aer simulator.
        
        Args:
            circuit: Qiskit QuantumCircuit
            shots: Number of measurement shots
            noise_model: "depolarizing" for simple noise, None for noiseless
        
        Returns:
            (job, metadata) tuple
        """
        try:
            from qiskit_aer import AerSimulator
            from qiskit_aer.noise import NoiseModel, depolarizing_error
        except ImportError:
            raise ImportError(
                "qiskit-aer is required for Aer simulation. "
                "Install with: pip install qiskit-aer"
            )
        
        # Create simulator
        if noise_model == "depolarizing":
            # Simple depolarizing noise model
            noise = NoiseModel()
            error_1q = depolarizing_error(0.001, 1)
            error_2q = depolarizing_error(0.01, 2)
            noise.add_all_qubit_quantum_error(error_1q, ['u1', 'u2', 'u3'])
            noise.add_all_qubit_quantum_error(error_2q, ['cx'])
            
            simulator = AerSimulator(noise_model=noise)
        else:
            simulator = AerSimulator()
        
        # Run simulation
        job = simulator.run(circuit, shots=shots)
        
        # Create metadata
        metadata = JobMetadata(
            job_id=job.job_id(),
            provider="ibm_aer",
            backend_name=self.backend_name,
            hypothesis_id="",  # Will be set by caller
            circuit_depth=circuit.depth(),
            qubit_count=circuit.num_qubits,
            shots=shots,
            timestamp=datetime.now(timezone.utc).isoformat(),
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
        """Submit circuit to IBM Runtime hardware.
        
        Args:
            circuit: Qiskit QuantumCircuit
            shots: Number of measurement shots
            mitigation: Optional mitigation settings:
                - resilience_level: 0, 1, or 2
                - dynamical_decoupling: bool
                - twirling_gates: bool
                - twirling_measure: bool
        
        Returns:
            (job, metadata) tuple
        
        Raises:
            CredentialsError: If credentials are not available
        """
        if self.is_simulator:
            raise ValueError(
                f"{self.backend_name} is a simulator. Use submit_emulator() instead."
            )
        
        if not self.check_credentials():
            raise CredentialsError(
                "IBM Quantum credentials required. "
                "Save account with: QiskitRuntimeService.save_account(token='...', instance='...')"
            )
        
        try:
            from qiskit_ibm_runtime import SamplerV2 as Sampler
            from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
        except ImportError:
            raise ImportError(
                "qiskit-ibm-runtime is required for IBM Runtime. "
                "Install with: pip install qiskit-ibm-runtime"
            )
        
        backend = self._load_backend()
        
        # Transpile circuit for backend
        pm = generate_preset_pass_manager(backend=backend, optimization_level=3)
        transpiled = pm.run(circuit)
        
        # Create Sampler with mitigation settings
        # Qiskit 2.4+ SamplerV2 uses mode parameter
        sampler = Sampler(mode=backend)
        
        # Apply mitigation settings for Qiskit 2.4+
        # Options are set as attributes, not via update()
        if mitigation:
            try:
                resilience_level = mitigation.get("resilience_level", 1)
                # Set resilience level directly
                if hasattr(sampler.options, 'resilience_level'):
                    sampler.options.resilience_level = resilience_level
                
                # Set dynamical decoupling if available
                if mitigation.get("dynamical_decoupling", False):
                    if hasattr(sampler.options, 'dynamical_decoupling'):
                        sampler.options.dynamical_decoupling.enable = True
                
                # Set twirling options if available
                if mitigation.get("twirling_gates", False):
                    if hasattr(sampler.options, 'twirling'):
                        sampler.options.twirling.enable_gates = True
                
                if mitigation.get("twirling_measure", False):
                    if hasattr(sampler.options, 'twirling'):
                        sampler.options.twirling.enable_measure = True
                        
            except (AttributeError, TypeError) as e:
                logger.warning(f"Failed to apply some mitigation settings: {e}")
        
        # Submit job
        job = sampler.run([transpiled], shots=shots)
        
        # Create metadata
        metadata = JobMetadata(
            job_id=job.job_id(),
            provider="ibm_quantum",
            backend_name=self.backend_name,
            hypothesis_id="",  # Will be set by caller
            circuit_depth=transpiled.depth(),
            qubit_count=transpiled.num_qubits,
            shots=shots,
            timestamp=datetime.now(timezone.utc).isoformat(),
            calibration=self.get_calibration_data(),
            mitigation_settings=mitigation or {}
        )
        
        return job, metadata
    
    def get_result(self, job: Any) -> Any:
        """Retrieve job result.
        
        Args:
            job: Job object returned from submit_emulator or submit_hardware
        
        Returns:
            Result object (Aer or Runtime format)
        """
        try:
            return job.result()
        except Exception as e:
            logger.error(f"Failed to retrieve job result: {e}")
            raise
    
    def close_session(self):
        """Close any open sessions and cleanup resources.
        
        This should be called when done with the provider to ensure
        proper resource cleanup, especially for Runtime sessions.
        """
        if self._session is not None:
            try:
                if hasattr(self._session, 'close'):
                    self._session.close()
                logger.info("IBM Runtime session closed")
            except Exception as e:
                logger.warning(f"Error closing session: {e}")
            finally:
                self._session = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close_session()
        return False
    
    @staticmethod
    def least_busy_backend(
        service: Any = None,
        min_qubits: int = 5,
        operational: bool = True,
        simulator: bool = False
    ) -> str:
        """Find least busy operational backend.
        
        Args:
            service: QiskitRuntimeService instance (will create if None)
            min_qubits: Minimum number of qubits required
            operational: Only return operational backends
            simulator: Include simulators in search
        
        Returns:
            Backend name
        """
        if service is None:
            from qiskit_ibm_runtime import QiskitRuntimeService
            service = QiskitRuntimeService()
        
        backend = service.least_busy(
            min_num_qubits=min_qubits,
            operational=operational,
            simulator=simulator
        )
        
        return backend.name


def create_ibm_adapter(
    backend_name: str = "aer_simulator",
    token: Optional[str] = None,
    instance: Optional[str] = None
) -> IBMRuntimeProvider:
    """Convenience function to create IBM Runtime adapter.
    
    Args:
        backend_name: Backend name ("aer_simulator", "ibm_brisbane", etc.)
        token: Optional IBM Quantum token
        instance: Optional IBM Quantum instance (hub/group/project)
    
    Returns:
        IBMRuntimeProvider instance
    """
    credentials = None
    if token:
        credentials = {"token": token}
        if instance:
            credentials["instance"] = instance
    
    return IBMRuntimeProvider(backend_name, credentials)

# Made with Bob
