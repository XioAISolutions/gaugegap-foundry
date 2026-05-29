"""Emulator-to-hardware workflow for quantum experiments.

This module implements the standard verification ladder:
1. Run classical baseline
2. Run noiseless emulator
3. Run noisy emulator
4. Validate emulator vs classical
5. Check hardware readiness
6. Submit to hardware
7. Capture metadata and record in ledger
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, Optional
import json
import os

from ..providers import QuantumProvider, JobMetadata
from ..hardware_ready import verify_hardware_ready, HardwareReadinessError
from ..ledger import write_jsonl, utc_run_id, git_state, object_hash
from pathlib import Path


@dataclass
class WorkflowResult:
    """Result of an emulator-to-hardware workflow run."""
    
    hypothesis_id: str
    provider: str
    backend_name: str
    
    # Classical baseline
    classical_result: Dict[str, Any]
    
    # Emulator results
    emulator_noiseless_result: Optional[Dict[str, Any]] = None
    emulator_noisy_result: Optional[Dict[str, Any]] = None
    
    # Hardware result
    hardware_result: Optional[Dict[str, Any]] = None
    hardware_job_metadata: Optional[Dict[str, Any]] = None
    
    # Validation
    emulator_validated: bool = False
    hardware_ready_checks: Optional[list[Dict[str, Any]]] = None
    
    # Workflow metadata
    workflow_timestamp: str = ""
    workflow_status: str = "incomplete"
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    def save(self, output_path: str) -> None:
        """Save workflow result to JSON file."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class EmulatorToHardwareWorkflow:
    """Orchestrates the emulator-to-hardware verification workflow."""
    
    def __init__(
        self,
        provider: QuantumProvider,
        hypothesis_id: str,
        ledger_path: Optional[Path] = None
    ):
        """Initialize workflow.
        
        Args:
            provider: Quantum provider adapter
            hypothesis_id: Hypothesis ID for this experiment
            ledger_path: Optional path for ledger output
        """
        self.provider = provider
        self.hypothesis_id = hypothesis_id
        self.ledger_path = ledger_path
        self.ledger_records: list[Dict[str, Any]] = []
        
        self.result = WorkflowResult(
            hypothesis_id=hypothesis_id,
            provider=provider.__class__.__name__,
            backend_name=provider.backend_name,
            classical_result={},
            workflow_timestamp=datetime.utcnow().isoformat()
        )
    
    def set_classical_baseline(self, classical_result: Dict[str, Any]) -> None:
        """Set classical baseline result.
        
        Args:
            classical_result: Dictionary with classical observables
        """
        self.result.classical_result = classical_result
    
    def run_emulator_noiseless(
        self,
        circuit: Any,
        shots: int = 1024
    ) -> tuple[Any, JobMetadata]:
        """Run circuit on noiseless emulator.
        
        Args:
            circuit: Circuit object (provider-specific)
            shots: Number of measurement shots
        
        Returns:
            (job, metadata) tuple
        """
        job, metadata = self.provider.submit_emulator(
            circuit,
            shots=shots,
            noise_model=None
        )
        
        # Update metadata with hypothesis ID
        metadata.hypothesis_id = self.hypothesis_id
        
        return job, metadata
    
    def run_emulator_noisy(
        self,
        circuit: Any,
        shots: int = 1024,
        noise_model: str = "realistic"
    ) -> tuple[Any, JobMetadata]:
        """Run circuit on noisy emulator.
        
        Args:
            circuit: Circuit object (provider-specific)
            shots: Number of measurement shots
            noise_model: Noise model name ("realistic", "depolarizing", etc.)
        
        Returns:
            (job, metadata) tuple
        """
        job, metadata = self.provider.submit_emulator(
            circuit,
            shots=shots,
            noise_model=noise_model
        )
        
        # Update metadata with hypothesis ID
        metadata.hypothesis_id = self.hypothesis_id
        
        return job, metadata
    
    def validate_emulator(
        self,
        emulator_result: Dict[str, Any],
        tolerance: float = 0.1
    ) -> bool:
        """Validate emulator result against classical baseline.
        
        Args:
            emulator_result: Emulator observables
            tolerance: Relative tolerance for comparison
        
        Returns:
            True if validation passes
        """
        from ..hardware_ready import check_emulator_validated
        
        check = check_emulator_validated(
            self.hypothesis_id,
            self.result.classical_result,
            emulator_result,
            tolerance
        )
        
        self.result.emulator_validated = check.passed
        return check.passed
    
    def check_hardware_ready(
        self,
        circuit: Any,
        calibration_timestamp: str,
        max_depth: Optional[int] = None,
        tolerance: float = 0.1
    ) -> list[Dict[str, Any]]:
        """Run hardware readiness checks.
        
        Args:
            circuit: Circuit object
            calibration_timestamp: Backend calibration timestamp
            max_depth: Optional maximum circuit depth
            tolerance: Tolerance for emulator validation
        
        Returns:
            List of check results
        
        Raises:
            HardwareReadinessError: If any checks fail
        """
        calibration = self.provider.get_calibration_data()
        
        checks = verify_hardware_ready(
            hypothesis_id=self.hypothesis_id,
            provider_name=self.result.provider.lower(),
            circuit=circuit,
            backend_qubits=calibration.qubit_count,
            backend_connectivity=calibration.connectivity,
            calibration_timestamp=calibration_timestamp,
            classical_result=self.result.classical_result,
            emulator_result=self.result.emulator_noisy_result,
            max_depth=max_depth,
            tolerance=tolerance
        )
        
        self.result.hardware_ready_checks = [
            {
                "check_name": c.check_name,
                "passed": c.passed,
                "message": c.message,
                "details": c.details or {}
            }
            for c in checks
        ]
        
        return self.result.hardware_ready_checks
    
    def submit_hardware(
        self,
        circuit: Any,
        shots: int = 1024,
        mitigation: Optional[Dict[str, Any]] = None
    ) -> tuple[Any, JobMetadata]:
        """Submit circuit to hardware after readiness checks.
        
        Args:
            circuit: Circuit object (provider-specific)
            shots: Number of measurement shots
            mitigation: Optional mitigation settings
        
        Returns:
            (job, metadata) tuple
        
        Raises:
            HardwareReadinessError: If readiness checks fail
        """
        # Run readiness checks first
        calibration = self.provider.get_calibration_data()
        self.check_hardware_ready(
            circuit,
            calibration.timestamp
        )
        
        # Submit to hardware
        job, metadata = self.provider.submit_hardware(
            circuit,
            shots=shots,
            mitigation=mitigation
        )
        
        # Update metadata with hypothesis ID
        metadata.hypothesis_id = self.hypothesis_id
        
        # Store metadata
        self.result.hardware_job_metadata = metadata.to_dict()
        
        # Record in ledger
        if self.ledger_path:
            record = {
                "run_id": utc_run_id(),
                "hypothesis_id": self.hypothesis_id,
                "method": f"{self.result.provider}_hardware",
                "backend": self.provider.backend_name,
                "shots": shots,
                "mitigation": mitigation or {},
                "job_id": metadata.job_id,
                "timestamp": metadata.timestamp
            }
            self.ledger_records.append(record)
            write_jsonl(self.ledger_path, self.ledger_records)
        
        return job, metadata
    
    def finalize(
        self,
        hardware_result: Optional[Dict[str, Any]] = None,
        status: str = "complete",
        error_message: Optional[str] = None
    ) -> WorkflowResult:
        """Finalize workflow and return result.
        
        Args:
            hardware_result: Optional hardware observables
            status: Workflow status ("complete", "emulator_only", "failed")
            error_message: Optional error message
        
        Returns:
            WorkflowResult object
        """
        if hardware_result:
            self.result.hardware_result = hardware_result
        
        self.result.workflow_status = status
        self.result.error_message = error_message
        
        return self.result


def run_emulator_to_hardware(
    provider: QuantumProvider,
    hypothesis_id: str,
    circuit: Any,
    classical_result: Dict[str, Any],
    shots: int = 1024,
    noise_model: str = "realistic",
    mitigation: Optional[Dict[str, Any]] = None,
    tolerance: float = 0.1,
    hardware: bool = True,
    output_dir: Optional[str] = None
) -> WorkflowResult:
    """Run complete emulator-to-hardware workflow.
    
    Args:
        provider: Quantum provider adapter
        hypothesis_id: Hypothesis ID
        circuit: Circuit object
        classical_result: Classical baseline observables
        shots: Number of measurement shots
        noise_model: Noise model for emulator
        mitigation: Optional hardware mitigation settings
        tolerance: Validation tolerance
        hardware: Whether to submit to hardware (False = emulator only)
        output_dir: Optional directory to save workflow result
    
    Returns:
        WorkflowResult object
    """
    workflow = EmulatorToHardwareWorkflow(provider, hypothesis_id)
    workflow.set_classical_baseline(classical_result)
    
    try:
        # Step 1: Noiseless emulator
        print(f"Running noiseless emulator...")
        job_noiseless, meta_noiseless = workflow.run_emulator_noiseless(circuit, shots)
        result_noiseless = provider.get_result(job_noiseless)
        workflow.result.emulator_noiseless_result = {"job_id": meta_noiseless.job_id}
        
        # Step 2: Noisy emulator
        print(f"Running noisy emulator (noise_model={noise_model})...")
        job_noisy, meta_noisy = workflow.run_emulator_noisy(circuit, shots, noise_model)
        result_noisy = provider.get_result(job_noisy)
        workflow.result.emulator_noisy_result = {"job_id": meta_noisy.job_id}
        
        # Step 3: Validate emulator
        print(f"Validating emulator results...")
        validated = workflow.validate_emulator(
            workflow.result.emulator_noisy_result,
            tolerance
        )
        
        if not validated:
            print(f"Warning: Emulator validation failed")
        
        # Step 4: Hardware submission (if requested)
        if hardware:
            print(f"Checking hardware readiness...")
            calibration = provider.get_calibration_data()
            checks = workflow.check_hardware_ready(
                circuit,
                calibration.timestamp,
                tolerance=tolerance
            )
            
            print(f"Submitting to hardware...")
            job_hw, meta_hw = workflow.submit_hardware(circuit, shots, mitigation)
            result_hw = provider.get_result(job_hw)
            workflow.result.hardware_result = {"job_id": meta_hw.job_id}
            
            result = workflow.finalize(
                hardware_result=workflow.result.hardware_result,
                status="complete"
            )
        else:
            result = workflow.finalize(status="emulator_only")
        
    except HardwareReadinessError as e:
        print(f"Hardware readiness check failed: {e}")
        result = workflow.finalize(
            status="failed",
            error_message=str(e)
        )
    except Exception as e:
        print(f"Workflow error: {e}")
        result = workflow.finalize(
            status="failed",
            error_message=str(e)
        )
    
    # Save result if output directory specified
    if output_dir:
        output_path = os.path.join(
            output_dir,
            f"{hypothesis_id}-workflow-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.json"
        )
        result.save(output_path)
        print(f"Workflow result saved to {output_path}")
    
    return result

# Made with Bob
