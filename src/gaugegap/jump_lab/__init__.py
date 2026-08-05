"""GaugeGap Jump Lab: experience-to-axiom discovery experiments."""

from .axiom import compile_local_equivalence_axiom, verify_local_equivalence
from .contracts import Intervention, Observation, Transition
from .elevator import EinsteinElevatorWorld
from .executive import AbductiveExecutive
from .salience import SalienceCandidate, SalienceController

__all__ = [
    "AbductiveExecutive",
    "EinsteinElevatorWorld",
    "Intervention",
    "Observation",
    "SalienceCandidate",
    "SalienceController",
    "Transition",
    "compile_local_equivalence_axiom",
    "verify_local_equivalence",
]
