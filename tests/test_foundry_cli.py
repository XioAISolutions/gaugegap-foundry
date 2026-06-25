from __future__ import annotations

from pathlib import Path
import sys

import pytest
import yaml

from gaugegap.cli import (
    FoundryConfigError,
    all_units,
    load_config,
    resolve_command,
    run_named,
)


ROOT = Path(__file__).resolve().parents[1]


def test_repository_config_loads_and_has_core_groups():
    config = load_config(ROOT / "config" / "foundry.yaml")
    assert {"audit", "smoke", "proofpack", "all"} <= set(config.groups)
    assert config.units["curverank-0001"].hypothesis == "curverank-0001"
    assert config.units["su3-prototype-smoke"].status == "prototype_scaffold"


def test_every_configured_command_resolves_to_strings():
    config = load_config(ROOT / "config" / "foundry.yaml")
    for unit in config.units.values():
        command = resolve_command(unit.command, ROOT)
        assert command
        assert all(isinstance(token, str) and token for token in command)
        assert "{python}" not in command
        assert command[0] == sys.executable or command[0] in {"bash", "coqc"}


def test_run_script_discovery_surfaces_unregistered_scripts():
    config = load_config(ROOT / "config" / "foundry.yaml")
    units = all_units(config, ROOT)
    assert "curverank-0001" in units
    assert any(unit.id.startswith("script:") for unit in units.values())


def test_unknown_unit_fails_closed():
    config = load_config(ROOT / "config" / "foundry.yaml")
    with pytest.raises(FoundryConfigError, match="unknown unit or group"):
        run_named("does-not-exist", config, root=ROOT, dry_run=True)


def test_group_cycle_is_rejected(tmp_path):
    path = tmp_path / "foundry.yaml"
    path.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "units": {
                    "ok": {
                        "track": "integrity",
                        "command": ["{python}", "-c", "print('ok')"],
                    }
                },
                "groups": {"a": ["b"], "b": ["a"]},
            }
        ),
        encoding="utf-8",
    )
    config = load_config(path)
    with pytest.raises(FoundryConfigError, match="group cycle"):
        run_named("a", config, root=ROOT, dry_run=True)


def test_invalid_command_shape_is_rejected(tmp_path):
    path = tmp_path / "foundry.yaml"
    path.write_text(
        "version: 1\nunits:\n  broken:\n    track: test\n    command: nope\n",
        encoding="utf-8",
    )
    with pytest.raises(FoundryConfigError, match="non-empty list"):
        load_config(path)
