"""GaugeGap Jump Lab: experience-to-axiom discovery experiments."""

from .axiom import compile_local_equivalence_axiom, verify_local_equivalence
from .benchmark import run_benchmark
from .contracts import Intervention, Observation, Transition
from .elevator import EinsteinElevatorWorld
from .executive import AbductiveExecutive, ExecutiveConfig
from .report import render_benchmark_html, render_discovery_html, write_html
from .salience import SalienceCandidate, SalienceController

__all__ = [
    "AbductiveExecutive",
    "EinsteinElevatorWorld",
    "ExecutiveConfig",
    "Intervention",
    "Observation",
    "SalienceCandidate",
    "SalienceController",
    "Transition",
    "compile_local_equivalence_axiom",
    "render_benchmark_html",
    "render_discovery_html",
    "run_benchmark",
    "verify_local_equivalence",
    "write_html",
]
