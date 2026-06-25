"""Single config-driven entry point for GaugeGap Foundry.

The CLI intentionally starts as a thin, auditable process orchestrator. Scientific
stage generalization belongs in ``unified_orchestrator`` (Phase 2); this module
eliminates parameter drift now without rewriting working science code.

The base ``config/foundry.yaml`` may be extended by sorted YAML fragments in
``config/foundry.d/``.  Duplicate unit or group IDs fail closed, so modularity
does not create a second ambiguous source of truth.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping, Sequence

import yaml


PACKAGE_ROOT = Path(__file__).resolve().parents[2]


def _default_root() -> Path:
    """Prefer the current checkout when the package is installed from a wheel."""
    cwd = Path.cwd().resolve()
    if (cwd / "config" / "foundry.yaml").exists():
        return cwd
    return PACKAGE_ROOT


ROOT = _default_root()
DEFAULT_CONFIG = ROOT / "config" / "foundry.yaml"


class FoundryConfigError(RuntimeError):
    """Raised when the orchestration configuration is malformed."""


@dataclass(frozen=True)
class UnitSpec:
    id: str
    track: str
    command: tuple[str, ...]
    description: str = ""
    hypothesis: str | None = None
    status: str = "production"
    environment: Mapping[str, str] | None = None


@dataclass(frozen=True)
class FoundryConfig:
    path: Path
    units: Mapping[str, UnitSpec]
    groups: Mapping[str, tuple[str, ...]]
    discovery_enabled: bool = True
    discovery_glob: str = "scripts/run_*.py"
    sources: tuple[Path, ...] = ()


def _as_string_list(value: Any, *, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or not all(isinstance(x, str) for x in value):
        raise FoundryConfigError(f"{field} must be a non-empty list of strings")
    return tuple(value)


def _read_yaml_mapping(path: Path, *, require_version: bool) -> dict[str, Any]:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FoundryConfigError(f"config not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise FoundryConfigError(f"invalid YAML in {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise FoundryConfigError(f"top-level config must be a mapping: {path}")
    if require_version and raw.get("version") != 1:
        raise FoundryConfigError(f"config version must be 1: {path}")
    if not require_version and "version" in raw and raw.get("version") != 1:
        raise FoundryConfigError(f"fragment version must be 1 when present: {path}")
    return raw


def _merge_named_mapping(
    target: dict[str, Any],
    incoming: Any,
    *,
    field: str,
    source: Path,
) -> None:
    if incoming is None:
        return
    if not isinstance(incoming, dict):
        raise FoundryConfigError(f"{field} must be a mapping: {source}")
    duplicates = sorted(set(target) & set(incoming))
    if duplicates:
        raise FoundryConfigError(
            f"duplicate {field} IDs in {source}: {', '.join(duplicates)}"
        )
    target.update(incoming)


def load_config(path: Path | str = DEFAULT_CONFIG) -> FoundryConfig:
    """Load the base configuration plus deterministic ``foundry.d`` fragments."""
    config_path = Path(path).resolve()
    raw = _read_yaml_mapping(config_path, require_version=True)
    sources = [config_path]

    raw_units: dict[str, Any] = {}
    raw_groups: dict[str, Any] = {}
    _merge_named_mapping(raw_units, raw.get("units"), field="units", source=config_path)
    _merge_named_mapping(raw_groups, raw.get("groups", {}), field="groups", source=config_path)

    fragment_dir = config_path.parent / "foundry.d"
    fragments = sorted((*fragment_dir.glob("*.yaml"), *fragment_dir.glob("*.yml")))
    for fragment in fragments:
        payload = _read_yaml_mapping(fragment, require_version=False)
        unknown = set(payload) - {"version", "units", "groups"}
        if unknown:
            raise FoundryConfigError(
                f"unsupported fragment fields in {fragment}: {sorted(unknown)}"
            )
        _merge_named_mapping(raw_units, payload.get("units"), field="units", source=fragment)
        _merge_named_mapping(raw_groups, payload.get("groups"), field="groups", source=fragment)
        sources.append(fragment)

    if not raw_units:
        raise FoundryConfigError("units must be a non-empty mapping")

    units: dict[str, UnitSpec] = {}
    for unit_id, payload in raw_units.items():
        if not isinstance(unit_id, str) or not unit_id.strip():
            raise FoundryConfigError("unit IDs must be non-empty strings")
        if not isinstance(payload, dict):
            raise FoundryConfigError(f"unit {unit_id!r} must be a mapping")
        command = _as_string_list(payload.get("command"), field=f"units.{unit_id}.command")
        track = payload.get("track")
        if not isinstance(track, str) or not track:
            raise FoundryConfigError(f"units.{unit_id}.track must be a non-empty string")
        environment = payload.get("environment")
        if environment is not None:
            if not isinstance(environment, dict) or not all(
                isinstance(k, str) and isinstance(v, (str, int, float))
                for k, v in environment.items()
            ):
                raise FoundryConfigError(
                    f"units.{unit_id}.environment must map strings to scalar values"
                )
            environment = {k: str(v) for k, v in environment.items()}
        units[unit_id] = UnitSpec(
            id=unit_id,
            track=track,
            command=command,
            description=str(payload.get("description", "")),
            hypothesis=payload.get("hypothesis"),
            status=str(payload.get("status", "production")),
            environment=environment,
        )

    groups = {
        name: _as_string_list(items, field=f"groups.{name}")
        for name, items in raw_groups.items()
    }

    discovery = raw.get("discovery", {})
    if not isinstance(discovery, dict):
        raise FoundryConfigError("discovery must be a mapping")
    return FoundryConfig(
        path=config_path,
        units=units,
        groups=groups,
        discovery_enabled=bool(discovery.get("enabled", True)),
        discovery_glob=str(discovery.get("glob", "scripts/run_*.py")),
        sources=tuple(sources),
    )


def discover_units(config: FoundryConfig, root: Path = ROOT) -> dict[str, UnitSpec]:
    """Surface unregistered run scripts instead of letting them remain invisible."""
    if not config.discovery_enabled:
        return {}
    configured_scripts = {
        token
        for unit in config.units.values()
        for token in unit.command
        if token.startswith("scripts/") and token.endswith(".py")
    }
    discovered: dict[str, UnitSpec] = {}
    for script in sorted(root.glob(config.discovery_glob)):
        relative = script.relative_to(root).as_posix()
        if relative in configured_scripts:
            continue
        unit_id = f"script:{script.stem}"
        discovered[unit_id] = UnitSpec(
            id=unit_id,
            track="unclassified",
            command=("{python}", relative),
            description="Auto-discovered legacy run script; classify before promoting.",
            status="unclassified",
        )
    return discovered


def all_units(config: FoundryConfig, root: Path = ROOT) -> dict[str, UnitSpec]:
    merged = dict(config.units)
    merged.update(discover_units(config, root))
    return merged


def resolve_command(command: Sequence[str], root: Path = ROOT) -> list[str]:
    substitutions = {
        "{python}": sys.executable,
        "{root}": str(root),
    }
    return [substitutions.get(token, token) for token in command]


def _run_unit(
    unit: UnitSpec,
    *,
    root: Path,
    extra_args: Sequence[str] = (),
    dry_run: bool = False,
) -> int:
    command = resolve_command(unit.command, root) + list(extra_args)
    print(f"[foundry] {unit.id} ({unit.track}/{unit.status})")
    print("[foundry] $ " + " ".join(command))
    if dry_run:
        return 0
    environment = os.environ.copy()
    if unit.environment:
        environment.update(unit.environment)
    completed = subprocess.run(command, cwd=root, env=environment, check=False)
    return int(completed.returncode)


def run_named(
    name: str,
    config: FoundryConfig,
    *,
    root: Path = ROOT,
    extra_args: Sequence[str] = (),
    dry_run: bool = False,
    _stack: tuple[str, ...] = (),
) -> int:
    """Run one unit or recursively execute one group, failing closed."""
    units = all_units(config, root)
    if name in units:
        return _run_unit(units[name], root=root, extra_args=extra_args, dry_run=dry_run)
    if name not in config.groups:
        raise FoundryConfigError(f"unknown unit or group: {name}")
    if extra_args:
        raise FoundryConfigError("extra arguments can only be passed to a single unit")
    if name in _stack:
        cycle = " -> ".join((*_stack, name))
        raise FoundryConfigError(f"group cycle detected: {cycle}")
    for child in config.groups[name]:
        rc = run_named(
            child,
            config,
            root=root,
            dry_run=dry_run,
            _stack=(*_stack, name),
        )
        if rc:
            return rc
    return 0


def _list_payload(config: FoundryConfig, root: Path) -> dict[str, Any]:
    units = all_units(config, root)
    return {
        "config": str(config.path),
        "config_sources": [str(path) for path in config.sources],
        "units": [
            {
                "id": unit.id,
                "track": unit.track,
                "hypothesis": unit.hypothesis,
                "status": unit.status,
                "description": unit.description,
                "command": resolve_command(unit.command, root),
            }
            for unit in sorted(units.values(), key=lambda item: (item.track, item.id))
        ],
        "groups": {name: list(items) for name, items in sorted(config.groups.items())},
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="foundry",
        description="Config-driven GaugeGap Foundry orchestration.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Path to foundry YAML configuration.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help=argparse.SUPPRESS,
    )
    sub = parser.add_subparsers(dest="verb", required=True)

    list_parser = sub.add_parser("list", help="List configured and discovered runnable units.")
    list_parser.add_argument("--json", action="store_true", dest="as_json")

    run_parser = sub.add_parser("run", help="Run a configured unit or group.")
    run_parser.add_argument("id")
    run_parser.add_argument("--dry-run", action="store_true")

    for verb in ("audit", "proofpack", "all"):
        command_parser = sub.add_parser(verb, help=f"Run the configured {verb} group.")
        command_parser.add_argument("--dry-run", action="store_true")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args, extra = parser.parse_known_args(argv)
    if args.verb != "run" and extra:
        parser.error("unrecognized arguments: " + " ".join(extra))
    try:
        config = load_config(args.config)
        root = args.root.resolve()

        if args.verb == "list":
            payload = _list_payload(config, root)
            if args.as_json:
                print(json.dumps(payload, indent=2, sort_keys=True))
            else:
                for unit in payload["units"]:
                    hypothesis = f" hypothesis={unit['hypothesis']}" if unit["hypothesis"] else ""
                    print(
                        f"{unit['id']:<38} track={unit['track']:<16} "
                        f"status={unit['status']}{hypothesis}"
                    )
                print("\nGroups:")
                for name, members in payload["groups"].items():
                    print(f"{name:<38} " + ", ".join(members))
            return 0

        if args.verb == "run":
            forwarded = list(extra)
            if forwarded[:1] == ["--"]:
                forwarded = forwarded[1:]
            return run_named(
                args.id,
                config,
                root=root,
                extra_args=forwarded,
                dry_run=args.dry_run,
            )

        return run_named(args.verb, config, root=root, dry_run=args.dry_run)
    except FoundryConfigError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
