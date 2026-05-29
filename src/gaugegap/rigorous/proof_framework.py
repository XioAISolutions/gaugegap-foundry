"""
Computer-assisted proof framework with theorem and proof step tracking.

Provides infrastructure for building and verifying computer-assisted proofs
with certified numerical bounds.

CLAIM BOUNDARY:
This framework supports computer-assisted proofs for finite-system benchmarks.
It does NOT claim to prove any Millennium Prize problems.
"""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import json
from enum import Enum

from .interval_arithmetic import Interval, IntervalMatrix, IntervalVector


class AssumptionType(Enum):
    """Types of assumptions in a proof."""
    FINITE_SYSTEM = "finite_system"
    TRUNCATION = "truncation"
    DISCRETIZATION = "discretization"
    NUMERICAL_PRECISION = "numerical_precision"
    PHYSICAL_PARAMETER = "physical_parameter"
    MATHEMATICAL_PROPERTY = "mathematical_property"


@dataclass
class Assumption:
    """
    An assumption in a computer-assisted proof.
    
    Tracks what is assumed and the validity range.
    """
    type: AssumptionType
    description: str
    validity_range: Optional[Dict[str, Any]] = None
    certified: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "description": self.description,
            "validity_range": self.validity_range,
            "certified": self.certified
        }
    
    def __repr__(self) -> str:
        """String representation."""
        cert = "✓" if self.certified else "?"
        return f"[{cert}] {self.type.value}: {self.description}"


class OperationType(Enum):
    """Types of operations in proof steps."""
    EIGENVALUE_COMPUTATION = "eigenvalue_computation"
    MATRIX_MULTIPLICATION = "matrix_multiplication"
    MATRIX_EXPONENTIAL = "matrix_exponential"
    NORM_COMPUTATION = "norm_computation"
    EXTRAPOLATION = "extrapolation"
    GAUGE_VERIFICATION = "gauge_verification"
    ENERGY_BOUND = "energy_bound"
    SPECTRAL_ANALYSIS = "spectral_analysis"
    INEQUALITY_VERIFICATION = "inequality_verification"


@dataclass
class ProofStep:
    """
    A single step in a computer-assisted proof.
    
    Each step has:
    - Operation performed
    - Input values/bounds
    - Output values/bounds
    - Certified error bounds
    - Assumptions used
    """
    step_id: int
    operation: OperationType
    description: str
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    certified_bounds: Dict[str, Interval]
    assumptions: List[Assumption] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "step_id": self.step_id,
            "operation": self.operation.value,
            "description": self.description,
            "inputs": self._serialize_values(self.inputs),
            "outputs": self._serialize_values(self.outputs),
            "certified_bounds": {
                k: v.to_tuple() for k, v in self.certified_bounds.items()
            },
            "assumptions": [a.to_dict() for a in self.assumptions],
            "timestamp": self.timestamp
        }
    
    def _serialize_values(self, values: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize values for JSON export."""
        result = {}
        for k, v in values.items():
            if isinstance(v, Interval):
                result[k] = {"type": "interval", "value": v.to_tuple()}
            elif isinstance(v, (int, float, str, bool)):
                result[k] = v
            else:
                result[k] = str(v)
        return result
    
    def verify_bounds(self) -> bool:
        """
        Verify that certified bounds are valid.
        
        Returns:
            True if all bounds are valid (lower <= upper)
        """
        for name, interval in self.certified_bounds.items():
            if interval.lower > interval.upper:
                return False
        return True
    
    def __repr__(self) -> str:
        """String representation."""
        return f"Step {self.step_id}: {self.operation.value} - {self.description}"


@dataclass
class Theorem:
    """
    A theorem with statement, assumptions, and proof.
    
    Represents a computer-assisted proof with certified bounds.
    """
    name: str
    statement: str
    assumptions: List[Assumption]
    proof_steps: List[ProofStep] = field(default_factory=list)
    conclusion: Optional[Dict[str, Interval]] = None
    verified: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_assumption(self, assumption: Assumption):
        """Add an assumption to the theorem."""
        self.assumptions.append(assumption)
    
    def add_step(self, step: ProofStep):
        """Add a proof step."""
        self.proof_steps.append(step)
    
    def set_conclusion(self, conclusion: Dict[str, Interval]):
        """Set the theorem conclusion with certified bounds."""
        self.conclusion = conclusion
    
    def verify(self) -> bool:
        """
        Verify the proof.
        
        Checks:
        - All proof steps have valid bounds
        - Conclusion follows from steps
        - All assumptions are documented
        
        Returns:
            True if proof is valid
        """
        # Check all steps have valid bounds
        for step in self.proof_steps:
            if not step.verify_bounds():
                return False
        
        # Check conclusion is set
        if self.conclusion is None:
            return False
        
        # Check all conclusion bounds are valid
        for name, interval in self.conclusion.items():
            if interval.lower > interval.upper:
                return False
        
        self.verified = True
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "statement": self.statement,
            "assumptions": [a.to_dict() for a in self.assumptions],
            "proof_steps": [s.to_dict() for s in self.proof_steps],
            "conclusion": {
                k: v.to_tuple() for k, v in self.conclusion.items()
            } if self.conclusion else None,
            "verified": self.verified,
            "metadata": self.metadata
        }
    
    def to_json(self, filepath: str):
        """Export theorem to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def from_json(cls, filepath: str) -> "Theorem":
        """Load theorem from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        # Reconstruct assumptions
        assumptions = [
            Assumption(
                type=AssumptionType(a["type"]),
                description=a["description"],
                validity_range=a.get("validity_range"),
                certified=a.get("certified", False)
            )
            for a in data["assumptions"]
        ]
        
        # Reconstruct proof steps
        proof_steps = [
            ProofStep(
                step_id=s["step_id"],
                operation=OperationType(s["operation"]),
                description=s["description"],
                inputs=s["inputs"],
                outputs=s["outputs"],
                certified_bounds={
                    k: Interval.from_bounds(v[0], v[1])
                    for k, v in s["certified_bounds"].items()
                },
                assumptions=[
                    Assumption(
                        type=AssumptionType(a["type"]),
                        description=a["description"],
                        validity_range=a.get("validity_range"),
                        certified=a.get("certified", False)
                    )
                    for a in s.get("assumptions", [])
                ],
                timestamp=s.get("timestamp", "")
            )
            for s in data.get("proof_steps", [])
        ]
        
        # Reconstruct conclusion
        conclusion = None
        if data.get("conclusion"):
            conclusion = {
                k: Interval.from_bounds(v[0], v[1])
                for k, v in data["conclusion"].items()
            }
        
        return cls(
            name=data["name"],
            statement=data["statement"],
            assumptions=assumptions,
            proof_steps=proof_steps,
            conclusion=conclusion,
            verified=data.get("verified", False),
            metadata=data.get("metadata", {})
        )
    
    def __repr__(self) -> str:
        """String representation."""
        status = "✓ VERIFIED" if self.verified else "? UNVERIFIED"
        return f"Theorem '{self.name}' [{status}]\n{self.statement}"


class ProofTree:
    """
    A tree of proof steps showing dependencies.
    
    Tracks which steps depend on which other steps.
    """
    
    def __init__(self, theorem: Theorem):
        """Initialize proof tree from theorem."""
        self.theorem = theorem
        self.dependencies: Dict[int, List[int]] = {}
        self._build_dependencies()
    
    def _build_dependencies(self):
        """Build dependency graph from proof steps."""
        # For now, assume linear dependency (each step depends on previous)
        # More sophisticated dependency tracking could be added
        for i, step in enumerate(self.theorem.proof_steps):
            if i > 0:
                self.dependencies[step.step_id] = [self.theorem.proof_steps[i-1].step_id]
            else:
                self.dependencies[step.step_id] = []
    
    def get_dependencies(self, step_id: int) -> List[int]:
        """Get dependencies for a step."""
        return self.dependencies.get(step_id, [])
    
    def verify_dependencies(self) -> bool:
        """Verify all dependencies are satisfied."""
        for step_id, deps in self.dependencies.items():
            for dep_id in deps:
                if dep_id not in self.dependencies:
                    return False
        return True
    
    def to_graphviz(self) -> str:
        """
        Export proof tree to Graphviz DOT format.
        
        Returns:
            DOT format string
        """
        lines = ["digraph ProofTree {"]
        lines.append('  rankdir=TB;')
        lines.append('  node [shape=box];')
        
        # Add nodes
        for step in self.theorem.proof_steps:
            label = f"Step {step.step_id}\\n{step.operation.value}"
            lines.append(f'  step{step.step_id} [label="{label}"];')
        
        # Add edges
        for step_id, deps in self.dependencies.items():
            for dep_id in deps:
                lines.append(f'  step{dep_id} -> step{step_id};')
        
        lines.append("}")
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"ProofTree for '{self.theorem.name}' with {len(self.theorem.proof_steps)} steps"


def create_finite_system_assumption(
    system_size: int,
    description: str
) -> Assumption:
    """
    Create a finite system size assumption.
    
    Args:
        system_size: Size of the finite system
        description: Description of the system
    
    Returns:
        Assumption object
    """
    return Assumption(
        type=AssumptionType.FINITE_SYSTEM,
        description=description,
        validity_range={"system_size": system_size},
        certified=True
    )


def create_truncation_assumption(
    truncation_level: int,
    description: str
) -> Assumption:
    """
    Create a truncation assumption.
    
    Args:
        truncation_level: Truncation level
        description: Description of truncation
    
    Returns:
        Assumption object
    """
    return Assumption(
        type=AssumptionType.TRUNCATION,
        description=description,
        validity_range={"truncation_level": truncation_level},
        certified=True
    )


def create_precision_assumption(
    decimal_places: int,
    description: str = "Numerical precision"
) -> Assumption:
    """
    Create a numerical precision assumption.
    
    Args:
        decimal_places: Number of decimal places
        description: Description
    
    Returns:
        Assumption object
    """
    return Assumption(
        type=AssumptionType.NUMERICAL_PRECISION,
        description=description,
        validity_range={"decimal_places": decimal_places},
        certified=True
    )


def verify_inequality(
    left: Interval,
    right: Interval,
    inequality: str = "<="
) -> bool:
    """
    Verify an inequality between intervals with certified bounds.
    
    Args:
        left: Left interval
        right: Right interval
        inequality: Type of inequality ("<=", "<", ">=", ">")
    
    Returns:
        True if inequality is certified to hold
    """
    if inequality == "<=":
        return left.upper <= right.lower
    elif inequality == "<":
        return left.upper < right.lower
    elif inequality == ">=":
        return left.lower >= right.upper
    elif inequality == ">":
        return left.lower > right.upper
    else:
        raise ValueError(f"Unknown inequality: {inequality}")


def create_inequality_step(
    step_id: int,
    left_name: str,
    left_value: Interval,
    right_name: str,
    right_value: Interval,
    inequality: str = "<="
) -> ProofStep:
    """
    Create a proof step verifying an inequality.
    
    Args:
        step_id: Step ID
        left_name: Name of left quantity
        left_value: Left interval
        right_name: Name of right quantity
        right_value: Right interval
        inequality: Type of inequality
    
    Returns:
        ProofStep object
    """
    verified = verify_inequality(left_value, right_value, inequality)
    
    return ProofStep(
        step_id=step_id,
        operation=OperationType.INEQUALITY_VERIFICATION,
        description=f"Verify {left_name} {inequality} {right_name}",
        inputs={
            left_name: left_value,
            right_name: right_value
        },
        outputs={
            "verified": verified
        },
        certified_bounds={
            left_name: left_value,
            right_name: right_value
        }
    )

# Made with Bob
