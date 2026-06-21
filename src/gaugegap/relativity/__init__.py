"""Relativity layer: exact analysis of toy spacetime metrics.

Currently: the Alcubierre warp-drive metric and the rigorous fact that it requires
negative energy density (a certified energy-condition violation), plus the standard
Ford-Roman quantum-inequality obstruction. The GR/QFT sibling of the quantum speed
limit -- a rigorous bound-from-physics, not a claim that a warp drive is buildable.
"""
from gaugegap.relativity.alcubierre import (
    WarpAnalysis,
    analyze_warp_bubble,
    energy_density,
    ford_roman_bound,
    shape_function,
    shape_function_derivative,
    total_negative_energy,
)

__all__ = [
    "WarpAnalysis",
    "analyze_warp_bubble",
    "energy_density",
    "ford_roman_bound",
    "shape_function",
    "shape_function_derivative",
    "total_negative_energy",
]
