"""Finite Menger sponge topology/fractal benchmark.

This module turns the Menger sponge explainer into a reproducible finite
artifact.  It checks stage-wise algebraic identities and convergence direction;
it does not prove continuum topology or manufacture a physical sponge.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import log
from typing import Any


CLAIM_BOUNDARY = (
    "finite Menger sponge stage benchmark only; reports algebraic stage "
    "identities and convergence direction, not a new theorem about the limit "
    "space or a physical material claim"
)

HAUSDORFF_DIMENSION = log(20.0) / log(3.0)
TOPOLOGICAL_DIMENSION_LABEL = (
    "literature-boundary: the ideal Menger sponge is a universal curve with "
    "topological dimension 1; this runner does not prove that theorem"
)
ALIASES = ("Menger sponge", "Menger cube", "Sierpinski sponge", "Menger universal curve")
CONSTRUCTION_RULE = (
    "start with one cube",
    "subdivide each retained cube into 27 cubes on a 3x3x3 grid",
    "remove any subcube whose local ternary coordinates have two or three center digits",
    "repeat on the retained subcubes",
)
SOURCES = (
    {
        "kind": "background_reference",
        "title": "Menger Sponge -- Wolfram MathWorld",
        "url": "https://mathworld.wolfram.com/MengerSponge.html",
        "scope": "construction, 3D Sierpinski-carpet analog, universal-curve background",
    },
    {
        "kind": "background_reference",
        "title": "Menger Universal Spaces lecture notes",
        "url": "https://www.its.caltech.edu/~matilde/FractalsUToronto7.pdf",
        "scope": "finite stage count, volume, surface-area, and Hausdorff-dimension formulas",
    },
)


@dataclass(frozen=True)
class MengerStage:
    """One finite construction stage."""

    stage: int
    grid_width: int
    retained_cubes: int
    removed_cubes: int
    side_length: float
    volume: float
    surface_area: float
    surface_to_volume: float
    porosity: float
    retained_fraction: float
    hausdorff_dimension_estimate: float

    def summary(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MengerReport:
    schema: str
    benchmark_id: str
    iterations: int
    stages: list[MengerStage]
    hausdorff_dimension: float
    topological_dimension_label: str
    volume_collapse_score: float
    surface_growth_score: float
    dimension_bridge_score: float
    voxel_sample: list[tuple[int, int, int]]
    voxel_sample_truncated: bool
    passed: bool
    claim_boundary: str = CLAIM_BOUNDARY

    def summary(self) -> dict[str, Any]:
        final = self.stages[-1]
        return {
            "schema": self.schema,
            "benchmark_id": self.benchmark_id,
            "aliases": list(ALIASES),
            "construction_rule": list(CONSTRUCTION_RULE),
            "iterations": self.iterations,
            "hausdorff_dimension": self.hausdorff_dimension,
            "topological_dimension_label": self.topological_dimension_label,
            "limit_trends": {
                "volume_limit": 0.0,
                "surface_area_diverges": True,
                "finite_stage_volume_is_positive": final.volume > 0.0,
                "finite_stage_surface_area_is_finite": final.surface_area < float("inf"),
                "limit_language_boundary": (
                    "zero volume and infinite surface area are ideal-limit claims, "
                    "not properties of any finite exported stage"
                ),
            },
            "volume_collapse_score": self.volume_collapse_score,
            "surface_growth_score": self.surface_growth_score,
            "dimension_bridge_score": self.dimension_bridge_score,
            "voxel_sample": [list(point) for point in self.voxel_sample],
            "voxel_sample_truncated": self.voxel_sample_truncated,
            "passed": self.passed,
            "stages": [stage.summary() for stage in self.stages],
            "sources": list(SOURCES),
            "claim_boundary": self.claim_boundary,
        }


def menger_stage(stage: int) -> MengerStage:
    """Return exact closed-form finite measurements for construction stage."""

    if stage < 0:
        raise ValueError("stage must be non-negative")
    grid_width = 3 ** stage
    retained = 20 ** stage
    total = 27 ** stage
    removed = total - retained
    side = 3.0 ** (-stage)
    volume = (20.0 / 27.0) ** stage
    surface = 2.0 * ((20.0 / 9.0) ** stage) + 4.0 * ((8.0 / 9.0) ** stage)
    dimension = 3.0 if stage == 0 else log(float(retained)) / log(1.0 / side)
    return MengerStage(
        stage=stage,
        grid_width=grid_width,
        retained_cubes=retained,
        removed_cubes=removed,
        side_length=side,
        volume=volume,
        surface_area=surface,
        surface_to_volume=surface / volume,
        porosity=1.0 - volume,
        retained_fraction=retained / total,
        hausdorff_dimension_estimate=dimension,
    )


def _ternary_digits(value: int, width: int) -> list[int]:
    digits = [0] * width
    current = value
    for index in range(width - 1, -1, -1):
        digits[index] = current % 3
        current //= 3
    return digits


def is_retained_voxel(x: int, y: int, z: int, stage: int) -> bool:
    """Return whether an integer voxel coordinate survives a finite stage."""

    if stage < 0:
        raise ValueError("stage must be non-negative")
    grid_width = 3 ** stage
    if not (0 <= x < grid_width and 0 <= y < grid_width and 0 <= z < grid_width):
        raise ValueError("voxel coordinate outside stage grid")
    x_digits = _ternary_digits(x, stage)
    y_digits = _ternary_digits(y, stage)
    z_digits = _ternary_digits(z, stage)
    for xd, yd, zd in zip(x_digits, y_digits, z_digits):
        if sum(digit == 1 for digit in (xd, yd, zd)) >= 2:
            return False
    return True


def retained_voxel_coordinates(stage: int, *, limit: int | None = None) -> list[tuple[int, int, int]]:
    """Return retained integer voxel coordinates for a finite stage.

    ``limit`` keeps exported artifacts compact.  The full count remains available
    as ``20**stage`` in the stage summary.
    """

    if stage < 0:
        raise ValueError("stage must be non-negative")
    if limit is not None and limit < 0:
        raise ValueError("limit must be non-negative")
    if limit == 0:
        return []
    grid_width = 3 ** stage
    retained: list[tuple[int, int, int]] = []
    for x in range(grid_width):
        for y in range(grid_width):
            for z in range(grid_width):
                if is_retained_voxel(x, y, z, stage):
                    retained.append((x, y, z))
                    if limit is not None and len(retained) >= limit:
                        return retained
    return retained


def run_menger_forge(iterations: int = 4, *, voxel_sample_limit: int = 512) -> MengerReport:
    """Evaluate the finite Menger sponge benchmark through ``iterations``."""

    if iterations < 1:
        raise ValueError("iterations must be at least 1")
    if voxel_sample_limit < 0:
        raise ValueError("voxel_sample_limit must be non-negative")
    stages = [menger_stage(index) for index in range(iterations + 1)]
    volumes = [stage.volume for stage in stages]
    surfaces = [stage.surface_area for stage in stages]
    retained_ok = all(stage.retained_cubes == 20 ** stage.stage for stage in stages)
    volume_decreases = all(left > right for left, right in zip(volumes, volumes[1:]))
    surface_increases = all(left < right for left, right in zip(surfaces, surfaces[1:]))
    dimension_ok = abs(stages[-1].hausdorff_dimension_estimate - HAUSDORFF_DIMENSION) < 1e-12
    final = stages[-1]
    voxel_sample = retained_voxel_coordinates(iterations, limit=voxel_sample_limit)
    volume_collapse_score = max(0.0, min(1.0, 1.0 - final.volume))
    surface_growth_score = max(0.0, min(1.0, 1.0 - stages[0].surface_area / final.surface_area))
    dimension_bridge_score = max(0.0, min(1.0, (HAUSDORFF_DIMENSION - 1.0) / 2.0))
    return MengerReport(
        schema="gaugegap.menger_sponge_forge.v1",
        benchmark_id="menger-0001",
        iterations=iterations,
        stages=stages,
        hausdorff_dimension=HAUSDORFF_DIMENSION,
        topological_dimension_label=TOPOLOGICAL_DIMENSION_LABEL,
        volume_collapse_score=volume_collapse_score,
        surface_growth_score=surface_growth_score,
        dimension_bridge_score=dimension_bridge_score,
        voxel_sample=voxel_sample,
        voxel_sample_truncated=len(voxel_sample) < final.retained_cubes,
        passed=retained_ok and volume_decreases and surface_increases and dimension_ok,
    )
