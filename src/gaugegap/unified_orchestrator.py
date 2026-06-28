"""Common execution stages for every configured Foundry unit and group."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import subprocess
import time
from typing import Sequence

from gaugegap.cli import DEFAULT_CONFIG, ROOT, FoundryConfigError, all_units, load_config, resolve_command
from gaugegap.unified_registry import build_registry, validate_registry

STAGES = ("S0-resolve", "S1-execute", "S2-collect", "S3-cross-validate", "S4-formal-gate", "S5-claim-boundary")


@dataclass(frozen=True)
class UnitRun:
    id: str
    track: str
    status: str
    hypothesis: str | None
    command: tuple[str, ...]
    returncode: int
    duration_seconds: float


@dataclass(frozen=True)
class PipelineResult:
    target: str
    stages: tuple[str, ...]
    runs: tuple[UnitRun, ...]
    success: bool
    digest: str

    def to_dict(self) -> dict[str, object]:
        return {
            "target": self.target,
            "stages": list(self.stages),
            "runs": [asdict(run) for run in self.runs],
            "success": self.success,
            "digest": self.digest,
        }


def _flatten(name: str, config, root: Path, *, stack: tuple[str, ...] = ()) -> list[str]:
    units = all_units(config, root)
    if name in units:
        return [name]
    if name not in config.groups:
        raise FoundryConfigError(f"unknown unit or group: {name}")
    if name in stack:
        raise FoundryConfigError("group cycle: " + " -> ".join((*stack, name)))
    result: list[str] = []
    for child in config.groups[name]:
        result.extend(_flatten(child, config, root, stack=(*stack, name)))
    return result


def _stable_run(run: UnitRun) -> dict[str, object]:
    return {
        "id": run.id,
        "track": run.track,
        "status": run.status,
        "hypothesis": run.hypothesis,
        "command": list(run.command),
        "returncode": run.returncode,
    }


class UnifiedOrchestrator:
    def __init__(self, config_path: Path | str = DEFAULT_CONFIG, *, root: Path = ROOT):
        self.root = Path(root).resolve()
        self.config = load_config(config_path)
        self.registry = build_registry(config_path, root=self.root)
        validate_registry(self.config, self.registry, root=self.root)

    def run(
        self,
        target: str,
        *,
        dry_run: bool = False,
        extra_args: Sequence[str] = (),
        output: Path | None = None,
    ) -> PipelineResult:
        leaf_ids = _flatten(target, self.config, self.root)
        if extra_args and len(leaf_ids) != 1:
            raise FoundryConfigError("extra arguments require a single leaf unit")
        units = all_units(self.config, self.root)
        records: list[UnitRun] = []
        for unit_id in leaf_ids:
            unit = units[unit_id]
            command = resolve_command(unit.command, self.root) + list(extra_args)
            started = time.perf_counter()
            rc = 0 if dry_run else subprocess.run(command, cwd=self.root, check=False).returncode
            records.append(UnitRun(unit.id, unit.track, unit.status, unit.hypothesis, tuple(command), int(rc), time.perf_counter() - started))
            if rc:
                break
        success = bool(records) and all(record.returncode == 0 for record in records)
        stable_payload = {
            "target": target,
            "stages": STAGES,
            "runs": [_stable_run(record) for record in records],
            "success": success,
        }
        digest = hashlib.sha256(json.dumps(stable_payload, sort_keys=True).encode()).hexdigest()
        result = PipelineResult(target, STAGES, tuple(records), success, digest)
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return result
