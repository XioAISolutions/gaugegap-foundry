"""GaugeGap Jump Lab: experience-to-axiom discovery experiments."""

from .axiom import compile_local_equivalence_axiom, verify_local_equivalence
from .benchmark import run_benchmark
from .cart_axiom import compile_force_mass_ratio_axiom, verify_force_mass_ratio
from .cart_executive import CartAbductiveExecutive
from .contracts import Intervention, Observation, Transition
from .elevator import EinsteinElevatorWorld
from .executive import AbductiveExecutive, ExecutiveConfig
from .force_cart import ForceMassCartWorld
from .report import render_benchmark_html, render_discovery_html, write_html
from .salience import SalienceCandidate, SalienceController
from .suite import registered_tasks, render_suite_html, run_suite

__all__ = [
    "AbductiveExecutive",
    "CartAbductiveExecutive",
    "EinsteinElevatorWorld",
    "ExecutiveConfig",
    "ForceMassCartWorld",
    "Intervention",
    "Observation",
    "SalienceCandidate",
    "SalienceController",
    "Transition",
    "compile_force_mass_ratio_axiom",
    "compile_local_equivalence_axiom",
    "registered_tasks",
    "render_benchmark_html",
    "render_discovery_html",
    "render_suite_html",
    "run_benchmark",
    "run_suite",
    "verify_force_mass_ratio",
    "verify_local_equivalence",
    "write_html",
]
