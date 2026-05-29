"""Hardware-ready boundary checks for quantum provider submissions.

This module implements the verification ladder before hardware submission:
1. Classical baseline exists and is validated
2. Hypothesis is registered with kill criteria
3. Emulator results match classical baseline within tolerance
4. Provider credentials are available
5. Backend calibration is current
6. Circuit meets backend constraints
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import os
import json


@dataclass
class HardwareReadinessCheck:
    """Result of a hardware readiness check."""
    
    check_name: str
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class HardwareReadinessError(Exception):
    """Raised when hardware readiness checks fail."""
    
    def __init__(self, checks: list[HardwareReadinessCheck]):
        self.checks = checks
        failed = [c for c in checks if not c.passed]
        messages = [f"  - {c.check_name}: {c.message}" for c in failed]
        super().__init__(
            f"Hardware not ready. Failed checks ({len(failed)}/{len(checks)}):\n" +
            "\n".join(messages)
        )


def check_hypothesis_registered(hypothesis_id: str) -> HardwareReadinessCheck:
    """Check if hypothesis is registered with kill criteria.
    
    Args:
        hypothesis_id: Hypothesis ID (e.g., "gaugegap-0002")
    
    Returns:
        HardwareReadinessCheck result
    """
    hypothesis_file = f"hypotheses/{hypothesis_id}.yaml"
    
    if not os.path.exists(hypothesis_file):
        return HardwareReadinessCheck(
            check_name="hypothesis_registered",
            passed=False,
            message=f"Hypothesis file not found: {hypothesis_file}",
            details={"hypothesis_id": hypothesis_id}
        )
    
    try:
        import yaml
        with open(hypothesis_file) as f:
            hypothesis = yaml.safe_load(f)
        
        required_fields = ["id", "track", "scope", "claim", "kill_criteria"]
        missing = [f for f in required_fields if f not in hypothesis]
        
        if missing:
            return HardwareReadinessCheck(
                check_name="hypothesis_registered",
                passed=False,
                message=f"Hypothesis missing required fields: {missing}",
                details={"hypothesis_id": hypothesis_id, "missing_fields": missing}
            )
        
        return HardwareReadinessCheck(
            check_name="hypothesis_registered",
            passed=True,
            message=f"Hypothesis {hypothesis_id} is properly registered",
            details={"hypothesis_id": hypothesis_id, "track": hypothesis["track"]}
        )
        
    except Exception as e:
        return HardwareReadinessCheck(
            check_name="hypothesis_registered",
            passed=False,
            message=f"Failed to load hypothesis: {e}",
            details={"hypothesis_id": hypothesis_id, "error": str(e)}
        )


def check_classical_baseline_exists(hypothesis_id: str) -> HardwareReadinessCheck:
    """Check if classical baseline results exist.
    
    Args:
        hypothesis_id: Hypothesis ID
    
    Returns:
        HardwareReadinessCheck result
    """
    baseline_patterns = [
        f"results/baselines/{hypothesis_id}-*.jsonl",
        f"results/baselines/{hypothesis_id}-*.csv",
    ]
    
    import glob
    found_files = []
    for pattern in baseline_patterns:
        found_files.extend(glob.glob(pattern))
    
    if not found_files:
        return HardwareReadinessCheck(
            check_name="classical_baseline_exists",
            passed=False,
            message=f"No classical baseline found for {hypothesis_id}",
            details={"hypothesis_id": hypothesis_id, "searched_patterns": baseline_patterns}
        )
    
    return HardwareReadinessCheck(
        check_name="classical_baseline_exists",
        passed=True,
        message=f"Classical baseline exists: {len(found_files)} files",
        details={"hypothesis_id": hypothesis_id, "files": found_files}
    )


def check_emulator_validated(
    hypothesis_id: str,
    classical_result: Optional[Dict[str, Any]] = None,
    emulator_result: Optional[Dict[str, Any]] = None,
    tolerance: float = 0.1
) -> HardwareReadinessCheck:
    """Check if emulator results match classical baseline.
    
    Args:
        hypothesis_id: Hypothesis ID
        classical_result: Classical baseline result dict
        emulator_result: Emulator result dict
        tolerance: Relative tolerance for comparison
    
    Returns:
        HardwareReadinessCheck result
    """
    if classical_result is None or emulator_result is None:
        return HardwareReadinessCheck(
            check_name="emulator_validated",
            passed=False,
            message="Classical or emulator results not provided for comparison",
            details={"hypothesis_id": hypothesis_id}
        )
    
    # Extract key observables for comparison
    observables = ["gap", "energy_0", "energy_1", "mass_gap"]
    
    mismatches = []
    for obs in observables:
        if obs in classical_result and obs in emulator_result:
            classical_val = classical_result[obs]
            emulator_val = emulator_result[obs]
            
            if classical_val == 0:
                rel_error = abs(emulator_val - classical_val)
            else:
                rel_error = abs(emulator_val - classical_val) / abs(classical_val)
            
            if rel_error > tolerance:
                mismatches.append({
                    "observable": obs,
                    "classical": classical_val,
                    "emulator": emulator_val,
                    "rel_error": rel_error
                })
    
    if mismatches:
        return HardwareReadinessCheck(
            check_name="emulator_validated",
            passed=False,
            message=f"Emulator results differ from classical baseline (tolerance={tolerance})",
            details={"hypothesis_id": hypothesis_id, "mismatches": mismatches}
        )
    
    return HardwareReadinessCheck(
        check_name="emulator_validated",
        passed=True,
        message=f"Emulator results match classical baseline within tolerance={tolerance}",
        details={"hypothesis_id": hypothesis_id, "tolerance": tolerance}
    )


def check_provider_credentials(provider_name: str) -> HardwareReadinessCheck:
    """Check if provider credentials are available.
    
    Args:
        provider_name: Provider name ("quantinuum", "ibm", "braket", "ionq")
    
    Returns:
        HardwareReadinessCheck result
    """
    credential_checks = {
        "quantinuum": ["QUANTINUUM_API_KEY"],
        "ibm": ["QISKIT_IBM_TOKEN", "IBM_QUANTUM_TOKEN"],
        "braket": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"],
        "ionq": ["IONQ_API_KEY"],
    }
    
    if provider_name not in credential_checks:
        return HardwareReadinessCheck(
            check_name="provider_credentials",
            passed=False,
            message=f"Unknown provider: {provider_name}",
            details={"provider": provider_name}
        )
    
    env_vars = credential_checks[provider_name]
    found = [var for var in env_vars if os.getenv(var)]
    
    if not found:
        return HardwareReadinessCheck(
            check_name="provider_credentials",
            passed=False,
            message=f"No credentials found for {provider_name}. Set one of: {env_vars}",
            details={"provider": provider_name, "required_env_vars": env_vars}
        )
    
    return HardwareReadinessCheck(
        check_name="provider_credentials",
        passed=True,
        message=f"Credentials found for {provider_name}: {found[0]}",
        details={"provider": provider_name, "credential_source": found[0]}
    )


def check_calibration_current(
    calibration_timestamp: str,
    max_age_hours: int = 24
) -> HardwareReadinessCheck:
    """Check if backend calibration is recent.
    
    Args:
        calibration_timestamp: ISO 8601 timestamp of calibration
        max_age_hours: Maximum age in hours
    
    Returns:
        HardwareReadinessCheck result
    """
    try:
        cal_time = datetime.fromisoformat(calibration_timestamp.replace('Z', '+00:00'))
        now = datetime.now(cal_time.tzinfo)
        age = now - cal_time
        
        if age > timedelta(hours=max_age_hours):
            return HardwareReadinessCheck(
                check_name="calibration_current",
                passed=False,
                message=f"Calibration is {age.total_seconds()/3600:.1f} hours old (max: {max_age_hours})",
                details={
                    "calibration_timestamp": calibration_timestamp,
                    "age_hours": age.total_seconds() / 3600,
                    "max_age_hours": max_age_hours
                }
            )
        
        return HardwareReadinessCheck(
            check_name="calibration_current",
            passed=True,
            message=f"Calibration is {age.total_seconds()/3600:.1f} hours old",
            details={
                "calibration_timestamp": calibration_timestamp,
                "age_hours": age.total_seconds() / 3600
            }
        )
        
    except Exception as e:
        return HardwareReadinessCheck(
            check_name="calibration_current",
            passed=False,
            message=f"Failed to parse calibration timestamp: {e}",
            details={"calibration_timestamp": calibration_timestamp, "error": str(e)}
        )


def check_circuit_constraints(
    circuit: Any,
    backend_qubits: int,
    backend_connectivity: str,
    max_depth: Optional[int] = None
) -> HardwareReadinessCheck:
    """Check if circuit meets backend constraints.
    
    Args:
        circuit: Circuit object (provider-specific)
        backend_qubits: Number of qubits available on backend
        backend_connectivity: Connectivity type
        max_depth: Optional maximum circuit depth
    
    Returns:
        HardwareReadinessCheck result
    """
    circuit_qubits = getattr(circuit, 'num_qubits', getattr(circuit, 'qubit_count', 0))
    circuit_depth = getattr(circuit, 'depth', lambda: 0)()
    
    issues = []
    
    if circuit_qubits > backend_qubits:
        issues.append(f"Circuit requires {circuit_qubits} qubits, backend has {backend_qubits}")
    
    if max_depth and circuit_depth > max_depth:
        issues.append(f"Circuit depth {circuit_depth} exceeds maximum {max_depth}")
    
    if issues:
        return HardwareReadinessCheck(
            check_name="circuit_constraints",
            passed=False,
            message="; ".join(issues),
            details={
                "circuit_qubits": circuit_qubits,
                "circuit_depth": circuit_depth,
                "backend_qubits": backend_qubits,
                "backend_connectivity": backend_connectivity
            }
        )
    
    return HardwareReadinessCheck(
        check_name="circuit_constraints",
        passed=True,
        message=f"Circuit fits backend: {circuit_qubits}/{backend_qubits} qubits, depth={circuit_depth}",
        details={
            "circuit_qubits": circuit_qubits,
            "circuit_depth": circuit_depth,
            "backend_qubits": backend_qubits
        }
    )


def verify_hardware_ready(
    hypothesis_id: str,
    provider_name: str,
    circuit: Any,
    backend_qubits: int,
    backend_connectivity: str,
    calibration_timestamp: str,
    classical_result: Optional[Dict[str, Any]] = None,
    emulator_result: Optional[Dict[str, Any]] = None,
    max_depth: Optional[int] = None,
    tolerance: float = 0.1
) -> list[HardwareReadinessCheck]:
    """Run all hardware readiness checks.
    
    Args:
        hypothesis_id: Hypothesis ID
        provider_name: Provider name
        circuit: Circuit object
        backend_qubits: Backend qubit count
        backend_connectivity: Backend connectivity type
        calibration_timestamp: Calibration timestamp
        classical_result: Optional classical baseline result
        emulator_result: Optional emulator result
        max_depth: Optional maximum circuit depth
        tolerance: Tolerance for emulator validation
    
    Returns:
        List of HardwareReadinessCheck results
    
    Raises:
        HardwareReadinessError: If any checks fail
    """
    checks = [
        check_hypothesis_registered(hypothesis_id),
        check_classical_baseline_exists(hypothesis_id),
        check_provider_credentials(provider_name),
        check_calibration_current(calibration_timestamp),
        check_circuit_constraints(circuit, backend_qubits, backend_connectivity, max_depth),
    ]
    
    # Only check emulator validation if results are provided
    if classical_result and emulator_result:
        checks.append(
            check_emulator_validated(hypothesis_id, classical_result, emulator_result, tolerance)
        )
    
    # Raise if any checks failed
    if not all(c.passed for c in checks):
        raise HardwareReadinessError(checks)
    
    return checks


def save_readiness_report(
    checks: list[HardwareReadinessCheck],
    output_path: str
) -> None:
    """Save hardware readiness report to JSON.
    
    Args:
        checks: List of check results
        output_path: Output file path
    """
    report = {
        "timestamp": datetime.utcnow().isoformat(),
        "all_passed": all(c.passed for c in checks),
        "checks": [
            {
                "check_name": c.check_name,
                "passed": c.passed,
                "message": c.message,
                "details": c.details or {}
            }
            for c in checks
        ]
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

# Made with Bob
