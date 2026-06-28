"""Track-agnostic registry built from the canonical Foundry configuration."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from gaugegap.cli import DEFAULT_CONFIG, ROOT, FoundryConfig, UnitSpec, all_units, load_config


class RegistryError(RuntimeError):
    pass


@dataclass(frozen=True)
class TrackSpec:
    name: str
    units: tuple[UnitSpec, ...]

    @property
    def hypotheses(self) -> tuple[str, ...]:
        return tuple(sorted({u.hypothesis for u in self.units if u.hypothesis}))

    @property
    def statuses(self) -> tuple[str, ...]:
        return tuple(sorted({u.status for u in self.units}))


def build_registry(
    config_path: Path | str = DEFAULT_CONFIG,
    *,
    root: Path = ROOT,
) -> dict[str, TrackSpec]:
    config = load_config(config_path)
    grouped: dict[str, list[UnitSpec]] = {}
    for unit in all_units(config, root).values():
        grouped.setdefault(unit.track, []).append(unit)
    if not grouped:
        raise RegistryError("no tracks resolved from Foundry configuration")
    return {
        track: TrackSpec(track, tuple(sorted(units, key=lambda u: u.id)))
        for track, units in sorted(grouped.items())
    }


def validate_registry(
    config: FoundryConfig,
    registry: Mapping[str, TrackSpec],
    *,
    root: Path = ROOT,
) -> None:
    units = all_units(config, root)
    registered = {u.id for track in registry.values() for u in track.units}
    missing = sorted(set(units) - registered)
    duplicates = len(registered) != sum(len(t.units) for t in registry.values())
    unknown_group_refs = sorted(
        {child for children in config.groups.values() for child in children}
        - set(units)
        - set(config.groups)
    )
    if missing or duplicates or unknown_group_refs:
        raise RegistryError(
            f"invalid unified registry: missing={missing}, duplicates={duplicates}, "
            f"unknown_group_refs={unknown_group_refs}"
        )


def get_track(name: str, registry: Mapping[str, TrackSpec] | None = None) -> TrackSpec:
    registry = registry or build_registry()
    try:
        return registry[name]
    except KeyError as exc:
        raise RegistryError(f"unknown track: {name}") from exc
