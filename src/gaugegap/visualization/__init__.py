"""Visualization tools for cross-platform quantum experiment comparison.

This module provides utilities for:
- Comparing results across providers (Quantinuum, IBM, Braket, IonQ)
- Visualizing emulator vs hardware performance
- Plotting calibration drift over time
- Generating publication-ready comparison figures
"""

from .cross_platform_comparison import (
    compare_providers,
    plot_gap_comparison,
    load_workflow_results,
    generate_comparison_report,
    ComparisonMetrics,
)

__all__ = [
    "compare_providers",
    "plot_gap_comparison",
    "load_workflow_results",
    "generate_comparison_report",
    "ComparisonMetrics",
]

# Made with Bob
