"""Single config-driven entry point for GaugeGap Foundry.

The CLI intentionally starts as a thin, auditable process orchestrator. Scientific
stage generalization belongs in ``unified_orchestrator`` (Phase 2); this module
eliminates parameter drift now without rewriting working science code.
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


def _as_string_list(value: Any, *, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value or not all(isinstance(x, str) for x in value):
        raise FoundryConfigError(f"{field} must be a non-empty list of strings")
    return tuple(value)


def load_config(path: Path | str = DEFAULT_CONFIG) -> FoundryConfig:
    """Load and validate the orchestration source of truth."""
    config_path = Path(path).resolve()
    try:
        raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FoundryConfigError(f"config not found: {config_path}") from exc
    except yaml.YAMLError as exc:
        raise FoundryConfigError(f"invalid YAML in {config_path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise FoundryConfigError("top-level config must be a mapping")
    if raw.get("version") != 1:
        raise FoundryConfigError("config version must be 1")

    raw_units = raw.get("units")
    if not isinstance(raw_units, dict) or not raw_units:
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

    raw_groups = raw.get("groups", {})
    if not isinstance(raw_groups, dict):
        raise FoundryConfigError("groups must be a mapping")
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
    run_parser.add_argument(
        "extra",
        nargs=argparse.REMAINDER,
        help="Extra arguments passed after '--' to a single unit.",
    )

    for verb in ("audit", "proofpack", "all"):
        command_parser = sub.add_parser(verb, help=f"Run the configured {verb} group.")
        command_parser.add_argument("--dry-run", action="store_true")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
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
            extra = list(args.extra)
            if extra[:1] == ["--"]:
                extra = extra[1:]
            return run_named(
                args.id,
                config,
                root=root,
                extra_args=extra,
                dry_run=args.dry_run,
            )

        return run_named(args.verb, config, root=root, dry_run=args.dry_run)
    except FoundryConfigError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
