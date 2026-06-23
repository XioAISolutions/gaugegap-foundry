"""Visualization tools.

- ``weight_diagrams`` / ``cy_projection`` / ``svg``: exact 2D projections of
  higher-dimensional structures (su(3) weight space, Calabi-Yau slices) — the
  "Geometry of GaugeGap" layer.
- ``cross_platform_comparison``: cross-provider comparison utilities (placeholder;
  prototype scaffold, known limitation).
"""
from gaugegap.visualization import weight_diagrams, cy_projection, svg

# The cross-platform comparison module is an optional/placeholder component (prototype
# scaffold; known limitation); never let its (in)completeness break importing the
# visualization package.
try:  # pragma: no cover - optional component
    from .cross_platform_comparison import (  # noqa: F401
        compare_providers,
        plot_gap_comparison,
        load_workflow_results,
        generate_comparison_report,
        ComparisonMetrics,
    )
except Exception:  # pragma: no cover
    pass

__all__ = ["weight_diagrams", "cy_projection", "svg"]
