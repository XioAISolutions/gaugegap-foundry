from __future__ import annotations

from pathlib import Path
import sys

import pytest
import yaml

from gaugegap.cli import (
    FoundryConfigError,
    all_units,
    build_parser,
    load_config,
    main,
    resolve_command,
    run_named,
    unresolved_hypotheses,
)
from gaugegap.hypothesis_registry import load_registry


ROOT = Path(__file__).resolve().parents[1]


def test_repository_config_loads_and_has_core_groups():
    config = load_config(ROOT / "config" / "foundry.yaml")
    assert {"audit", "smoke", "proofpack", "all", "attractor-forge"} <= set(config.groups)
    assert config.units["curverank-0001"].hypothesis == "curverank-0001"
    assert config.units["su3-prototype-smoke"].status == "prototype_scaffold"
    assert config.units["flowgap-0002-rossler"].hypothesis == "flowgap-0002"
    assert any(path.name == "attractor-forge.yaml" for path in config.sources)


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
    assert "flowgap-0002-rossler" in units
    assert "script:run_attractor_forge" not in units
    assert any(unit.id.startswith("script:") for unit in units.values())


def test_run_dry_run_is_not_forwarded_to_child():
    parser = build_parser()
    args, extra = parser.parse_known_args(["run", "curverank-0001", "--dry-run"])
    assert args.dry_run is True
    assert extra == []


def test_child_arguments_are_forwardable_after_separator():
    parser = build_parser()
    args, extra = parser.parse_known_args(
        ["run", "curverank-0001", "--", "--output-dir", "/tmp/custom"]
    )
    assert args.dry_run is False
    assert extra == ["--output-dir", "/tmp/custom"]


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


def test_every_config_hypothesis_reference_is_registered():
    # The cross-reference gate: no unit may point at a hypothesis that does not
    # exist in hypotheses/. This is also enforced as a `foundry hypotheses --check`.
    config = load_config(ROOT / "config" / "foundry.yaml")
    registry = load_registry(ROOT / "hypotheses")
    assert unresolved_hypotheses(config, registry) == []


def test_hypotheses_check_passes_on_repository(capsys):
    rc = main(["hypotheses", "--check"])
    assert rc == 0
    assert "all hypothesis references resolve" in capsys.readouterr().out


def test_hypotheses_json_lists_registered_records(capsys):
    rc = main(["hypotheses", "--json"])
    assert rc == 0
    import json

    payload = json.loads(capsys.readouterr().out)
    ids = {record["id"] for record in payload["hypotheses"]}
    assert "curverank-0001" in ids
    assert payload["unresolved_references"] == []


def test_invalid_command_shape_is_rejected(tmp_path):
    path = tmp_path / "foundry.yaml"
    path.write_text(
        "version: 1\nunits:\n  broken:\n    track: test\n    command: nope\n",
        encoding="utf-8",
    )
    with pytest.raises(FoundryConfigError, match="non-empty list"):
        load_config(path)


def test_config_fragments_merge_in_sorted_order(tmp_path):
    base = tmp_path / "foundry.yaml"
    base.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "units": {
                    "base": {"track": "test", "command": ["{python}", "-c", "pass"]}
                },
            }
        ),
        encoding="utf-8",
    )
    fragment_dir = tmp_path / "foundry.d"
    fragment_dir.mkdir()
    (fragment_dir / "20-second.yaml").write_text(
        yaml.safe_dump(
            {
                "units": {
                    "second": {"track": "test", "command": ["{python}", "-c", "pass"]}
                }
            }
        ),
        encoding="utf-8",
    )
    (fragment_dir / "10-first.yaml").write_text(
        yaml.safe_dump(
            {
                "units": {
                    "first": {"track": "test", "command": ["{python}", "-c", "pass"]}
                }
            }
        ),
        encoding="utf-8",
    )
    config = load_config(base)
    assert list(config.units) == ["base", "first", "second"]
    assert [path.name for path in config.sources] == [
        "foundry.yaml",
        "10-first.yaml",
        "20-second.yaml",
    ]


def test_duplicate_fragment_ids_fail_closed(tmp_path):
    base = tmp_path / "foundry.yaml"
    base.write_text(
        yaml.safe_dump(
            {
                "version": 1,
                "units": {
                    "same": {"track": "test", "command": ["{python}", "-c", "pass"]}
                },
            }
        ),
        encoding="utf-8",
    )
    fragment_dir = tmp_path / "foundry.d"
    fragment_dir.mkdir()
    (fragment_dir / "duplicate.yaml").write_text(
        yaml.safe_dump(
            {
                "units": {
                    "same": {"track": "test", "command": ["{python}", "-c", "pass"]}
                }
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(FoundryConfigError, match="duplicate units IDs"):
        load_config(base)
