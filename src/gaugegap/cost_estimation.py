"""Cost estimation utilities for quantum hardware jobs.

Provides pre-submission cost estimates based on circuit properties, shot counts,
and provider-specific pricing models. Helps users make informed decisions about
hardware resource allocation.

All estimates are approximate and based on publicly available pricing information.
Actual costs may vary based on account type, region, and current provider pricing.
"""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import warnings


@dataclass
class CostEstimate:
    """Cost estimate for a quantum job.
    
    Attributes:
        provider: Provider name (quantinuum, ibm, ionq, braket)
        backend: Specific backend/device name
        estimated_cost_usd: Estimated cost in USD
        cost_breakdown: Detailed breakdown of cost components
        assumptions: List of assumptions used in estimation
        confidence: Confidence level (low, medium, high)
        warnings: Any warnings about the estimate
    """
    provider: str
    backend: str
    estimated_cost_usd: float
    cost_breakdown: Dict[str, float]
    assumptions: list[str]
    confidence: str
    warnings: list[str]


class CostEstimator:
    """Estimate quantum job costs across providers.
    
    Pricing models as of 2026-05:
    - Quantinuum: H-System Credits (HSC) per circuit execution
    - IBM: Quantum Runtime seconds
    - IonQ: Per-gate pricing
    - AWS Braket: Per-shot + per-task pricing
    
    Note: All pricing is approximate and subject to change. Always verify
    current pricing with provider documentation before submitting jobs.
    """
    
    # Approximate pricing (USD, as of 2026-05)
    # These are representative values for estimation purposes only
    QUANTINUUM_HSC_RATE = 0.50  # USD per HSC
    IBM_RUNTIME_RATE = 1.60  # USD per second
    IONQ_GATE_RATE = 0.00003  # USD per gate
    BRAKET_SHOT_RATE = 0.00035  # USD per shot
    BRAKET_TASK_RATE = 0.30  # USD per task
    
    def __init__(self):
        """Initialize cost estimator."""
        self.pricing_warnings = []
    
    def estimate_quantinuum(
        self,
        backend: str,
        n_circuits: int,
        shots_per_circuit: int,
        circuit_depth: Optional[int] = None,
        two_qubit_gates: Optional[int] = None
    ) -> CostEstimate:
        """Estimate Quantinuum job cost.
        
        Quantinuum pricing is based on H-System Credits (HSC), which depend on
        circuit complexity and shot count. H2 and Helios have different HSC rates.
        
        Args:
            backend: Backend name (H2-1, H2-1E, Helios)
            n_circuits: Number of circuits to execute
            shots_per_circuit: Shots per circuit
            circuit_depth: Circuit depth (optional, improves estimate)
            two_qubit_gates: Number of 2-qubit gates (optional, improves estimate)
        
        Returns:
            CostEstimate with breakdown and assumptions
        """
        assumptions = [
            "Pricing based on publicly available H-System Credit rates",
            f"Backend: {backend}",
            f"Circuits: {n_circuits}, Shots per circuit: {shots_per_circuit}"
        ]
        
        warnings_list = []
        confidence = "medium"
        
        # Base HSC estimate (simplified model)
        # Real pricing depends on circuit complexity, connectivity, etc.
        if circuit_depth is not None and two_qubit_gates is not None:
            # More accurate estimate with circuit details
            base_hsc_per_circuit = 5 + (two_qubit_gates * 0.1) + (circuit_depth * 0.05)
            assumptions.append(f"Circuit depth: {circuit_depth}, 2Q gates: {two_qubit_gates}")
            confidence = "high"
        else:
            # Conservative estimate without circuit details
            base_hsc_per_circuit = 10
            warnings_list.append("No circuit details provided; using conservative estimate")
            confidence = "low"
        
        # Shot scaling (diminishing returns for large shot counts)
        shot_factor = min(1.0, shots_per_circuit / 1000)
        hsc_per_circuit = base_hsc_per_circuit * (0.5 + 0.5 * shot_factor)
        
        total_hsc = hsc_per_circuit * n_circuits
        estimated_cost = total_hsc * self.QUANTINUUM_HSC_RATE
        
        breakdown = {
            "hsc_per_circuit": hsc_per_circuit,
            "total_hsc": total_hsc,
            "hsc_rate_usd": self.QUANTINUUM_HSC_RATE,
            "total_usd": estimated_cost
        }
        
        return CostEstimate(
            provider="quantinuum",
            backend=backend,
            estimated_cost_usd=estimated_cost,
            cost_breakdown=breakdown,
            assumptions=assumptions,
            confidence=confidence,
            warnings=warnings_list
        )
    
    def estimate_ibm(
        self,
        backend: str,
        n_circuits: int,
        shots_per_circuit: int,
        estimated_runtime_seconds: Optional[float] = None,
        use_runtime: bool = True
    ) -> CostEstimate:
        """Estimate IBM Quantum job cost.
        
        IBM pricing is based on Quantum Runtime seconds for Premium/On-Demand access.
        Open Plan users have limited free access.
        
        Args:
            backend: Backend name (e.g., ibm_brisbane, ibm_kyoto)
            n_circuits: Number of circuits
            shots_per_circuit: Shots per circuit
            estimated_runtime_seconds: Estimated runtime (optional)
            use_runtime: Whether using Qiskit Runtime (vs legacy backend)
        
        Returns:
            CostEstimate with breakdown and assumptions
        """
        assumptions = [
            "Pricing based on IBM Quantum Premium/On-Demand rates",
            f"Backend: {backend}",
            f"Circuits: {n_circuits}, Shots per circuit: {shots_per_circuit}",
            f"Using Qiskit Runtime: {use_runtime}"
        ]
        
        warnings_list = []
        confidence = "medium"
        
        if not use_runtime:
            warnings_list.append("Legacy backend access may have different pricing")
            confidence = "low"
        
        if estimated_runtime_seconds is not None:
            runtime_seconds = estimated_runtime_seconds
            assumptions.append(f"Provided runtime estimate: {runtime_seconds:.1f}s")
            confidence = "high"
        else:
            # Rough estimate: ~0.1s per circuit per 100 shots
            runtime_seconds = n_circuits * (shots_per_circuit / 100) * 0.1
            warnings_list.append("No runtime estimate provided; using rough approximation")
            confidence = "low"
        
        estimated_cost = runtime_seconds * self.IBM_RUNTIME_RATE
        
        breakdown = {
            "runtime_seconds": runtime_seconds,
            "runtime_rate_usd_per_second": self.IBM_RUNTIME_RATE,
            "total_usd": estimated_cost
        }
        
        if estimated_cost == 0:
            warnings_list.append("May be covered by Open Plan free tier")
        
        return CostEstimate(
            provider="ibm",
            backend=backend,
            estimated_cost_usd=estimated_cost,
            cost_breakdown=breakdown,
            assumptions=assumptions,
            confidence=confidence,
            warnings=warnings_list
        )
    
    def estimate_ionq(
        self,
        backend: str,
        n_circuits: int,
        shots_per_circuit: int,
        n_gates: Optional[int] = None,
        n_qubits: Optional[int] = None
    ) -> CostEstimate:
        """Estimate IonQ job cost.
        
        IonQ pricing is per-gate, with rates depending on backend (Harmony, Aria, Forte).
        
        Args:
            backend: Backend name (harmony, aria-1, forte-1)
            n_circuits: Number of circuits
            shots_per_circuit: Shots per circuit
            n_gates: Total gates per circuit (optional, improves estimate)
            n_qubits: Number of qubits (optional)
        
        Returns:
            CostEstimate with breakdown and assumptions
        """
        assumptions = [
            "Pricing based on IonQ per-gate model",
            f"Backend: {backend}",
            f"Circuits: {n_circuits}, Shots per circuit: {shots_per_circuit}"
        ]
        
        warnings_list = []
        confidence = "medium"
        
        if n_gates is not None:
            gates_per_circuit = n_gates
            assumptions.append(f"Gates per circuit: {n_gates}")
            confidence = "high"
        elif n_qubits is not None:
            # Rough estimate: ~10 gates per qubit for typical circuits
            gates_per_circuit = n_qubits * 10
            assumptions.append(f"Estimated from {n_qubits} qubits")
            warnings_list.append("Gate count estimated from qubit count")
            confidence = "low"
        else:
            gates_per_circuit = 50  # Conservative default
            warnings_list.append("No circuit details; using conservative estimate")
            confidence = "low"
        
        # IonQ charges per gate per shot
        total_gates = gates_per_circuit * n_circuits * shots_per_circuit
        estimated_cost = total_gates * self.IONQ_GATE_RATE
        
        breakdown = {
            "gates_per_circuit": gates_per_circuit,
            "total_gates": total_gates,
            "gate_rate_usd": self.IONQ_GATE_RATE,
            "total_usd": estimated_cost
        }
        
        return CostEstimate(
            provider="ionq",
            backend=backend,
            estimated_cost_usd=estimated_cost,
            cost_breakdown=breakdown,
            assumptions=assumptions,
            confidence=confidence,
            warnings=warnings_list
        )
    
    def estimate_braket(
        self,
        backend: str,
        n_circuits: int,
        shots_per_circuit: int,
        device_type: str = "gate"
    ) -> CostEstimate:
        """Estimate AWS Braket job cost.
        
        Braket pricing includes per-task and per-shot charges. Rates vary by device.
        
        Args:
            backend: Backend name (e.g., Aquila, IonQ, Rigetti)
            n_circuits: Number of circuits (tasks)
            shots_per_circuit: Shots per circuit
            device_type: Device type (gate, annealer, ahs)
        
        Returns:
            CostEstimate with breakdown and assumptions
        """
        assumptions = [
            "Pricing based on AWS Braket public rates",
            f"Backend: {backend}",
            f"Device type: {device_type}",
            f"Tasks: {n_circuits}, Shots per task: {shots_per_circuit}"
        ]
        
        warnings_list = []
        confidence = "medium"
        
        # Task charges
        task_cost = n_circuits * self.BRAKET_TASK_RATE
        
        # Shot charges
        total_shots = n_circuits * shots_per_circuit
        shot_cost = total_shots * self.BRAKET_SHOT_RATE
        
        estimated_cost = task_cost + shot_cost
        
        breakdown = {
            "task_cost_usd": task_cost,
            "shot_cost_usd": shot_cost,
            "total_usd": estimated_cost,
            "task_rate": self.BRAKET_TASK_RATE,
            "shot_rate": self.BRAKET_SHOT_RATE
        }
        
        if device_type == "ahs":
            warnings_list.append("AHS pricing may differ from gate-based devices")
            confidence = "low"
        
        return CostEstimate(
            provider="braket",
            backend=backend,
            estimated_cost_usd=estimated_cost,
            cost_breakdown=breakdown,
            assumptions=assumptions,
            confidence=confidence,
            warnings=warnings_list
        )
    
    def compare_providers(
        self,
        n_circuits: int,
        shots_per_circuit: int,
        circuit_depth: Optional[int] = None,
        n_gates: Optional[int] = None,
        n_qubits: Optional[int] = None
    ) -> Dict[str, CostEstimate]:
        """Compare costs across all providers for similar job parameters.
        
        Args:
            n_circuits: Number of circuits
            shots_per_circuit: Shots per circuit
            circuit_depth: Circuit depth (optional)
            n_gates: Gate count (optional)
            n_qubits: Qubit count (optional)
        
        Returns:
            Dictionary mapping provider names to cost estimates
        """
        estimates = {}
        
        # Quantinuum H2
        estimates["quantinuum_h2"] = self.estimate_quantinuum(
            backend="H2-1",
            n_circuits=n_circuits,
            shots_per_circuit=shots_per_circuit,
            circuit_depth=circuit_depth,
            two_qubit_gates=n_gates // 2 if n_gates else None
        )
        
        # IBM
        estimates["ibm_runtime"] = self.estimate_ibm(
            backend="ibm_brisbane",
            n_circuits=n_circuits,
            shots_per_circuit=shots_per_circuit
        )
        
        # IonQ
        estimates["ionq_forte"] = self.estimate_ionq(
            backend="forte-1",
            n_circuits=n_circuits,
            shots_per_circuit=shots_per_circuit,
            n_gates=n_gates,
            n_qubits=n_qubits
        )
        
        # Braket
        estimates["braket_ionq"] = self.estimate_braket(
            backend="IonQ",
            n_circuits=n_circuits,
            shots_per_circuit=shots_per_circuit
        )
        
        return estimates
    
    def print_estimate(self, estimate: CostEstimate) -> None:
        """Print formatted cost estimate.
        
        Args:
            estimate: CostEstimate to print
        """
        print(f"\n{'='*60}")
        print(f"Cost Estimate: {estimate.provider.upper()} - {estimate.backend}")
        print(f"{'='*60}")
        print(f"\nEstimated Cost: ${estimate.estimated_cost_usd:.2f} USD")
        print(f"Confidence: {estimate.confidence.upper()}")
        
        print("\nCost Breakdown:")
        for key, value in estimate.cost_breakdown.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")
            else:
                print(f"  {key}: {value}")
        
        print("\nAssumptions:")
        for assumption in estimate.assumptions:
            print(f"  • {assumption}")
        
        if estimate.warnings:
            print("\n⚠️  Warnings:")
            for warning in estimate.warnings:
                print(f"  • {warning}")
        
        print(f"\n{'='*60}\n")
    
    def print_comparison(self, estimates: Dict[str, CostEstimate]) -> None:
        """Print comparison table of cost estimates.
        
        Args:
            estimates: Dictionary of provider estimates
        """
        print(f"\n{'='*80}")
        print("Cost Comparison Across Providers")
        print(f"{'='*80}\n")
        
        # Sort by cost
        sorted_estimates = sorted(
            estimates.items(),
            key=lambda x: x[1].estimated_cost_usd
        )
        
        print(f"{'Provider':<20} {'Backend':<15} {'Cost (USD)':<12} {'Confidence':<12}")
        print(f"{'-'*80}")
        
        for name, est in sorted_estimates:
            print(f"{name:<20} {est.backend:<15} ${est.estimated_cost_usd:>10.2f} {est.confidence:<12}")
        
        print(f"\n{'='*80}")
        print("Note: All estimates are approximate. Verify current pricing with providers.")
        print(f"{'='*80}\n")


def estimate_job_cost(
    provider: str,
    backend: str,
    n_circuits: int,
    shots_per_circuit: int,
    **kwargs
) -> CostEstimate:
    """Convenience function to estimate job cost.
    
    Args:
        provider: Provider name (quantinuum, ibm, ionq, braket)
        backend: Backend name
        n_circuits: Number of circuits
        shots_per_circuit: Shots per circuit
        **kwargs: Additional provider-specific parameters
    
    Returns:
        CostEstimate
    
    Example:
        >>> est = estimate_job_cost(
        ...     provider="quantinuum",
        ...     backend="H2-1",
        ...     n_circuits=10,
        ...     shots_per_circuit=1000,
        ...     circuit_depth=50,
        ...     two_qubit_gates=20
        ... )
        >>> print(f"Estimated cost: ${est.estimated_cost_usd:.2f}")
    """
    estimator = CostEstimator()
    
    if provider.lower() == "quantinuum":
        return estimator.estimate_quantinuum(backend, n_circuits, shots_per_circuit, **kwargs)
    elif provider.lower() == "ibm":
        return estimator.estimate_ibm(backend, n_circuits, shots_per_circuit, **kwargs)
    elif provider.lower() == "ionq":
        return estimator.estimate_ionq(backend, n_circuits, shots_per_circuit, **kwargs)
    elif provider.lower() == "braket":
        return estimator.estimate_braket(backend, n_circuits, shots_per_circuit, **kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}")

# Made with Bob
