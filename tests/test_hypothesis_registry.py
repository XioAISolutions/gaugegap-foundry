from __future__ import annotations

from pathlib import Path

import pytest

from gaugegap.hypothesis_registry import (
    HypothesisError,
    get_hypothesis,
    list_hypotheses,
    load_registry,
)


ROOT = Path(__file__).resolve().parents[1]
HYPOTHESES = ROOT / "hypotheses"


def test_repository_registry_loads_every_file():
    registry = load_registry(HYPOTHESES)
    # One record per registry file (YAML + the historical JSON), keyed by id.
    on_disk = [
        p for p in HYPOTHESES.iterdir() if p.suffix in {".yaml", ".yml", ".json"}
    ]
    assert len(registry) == len(on_disk)
    assert {"curverank-0001", "flowgap-0001", "gaugegap-0005"} <= set(registry)


def test_legacy_json_id_field_is_accepted():
    # gaugegap-search-0001 is JSON and uses ``hypothesis_id`` rather than ``id``.
    record = get_hypothesis("gaugegap-search-0001", load_registry(HYPOTHESES))
    assert record.track == "GaugeGap"
    assert record.id == "gaugegap-search-0001"


def test_list_is_sorted_and_carries_metadata():
    items = list_hypotheses(load_registry(HYPOTHESES))
    assert items == sorted(items, key=lambda h: (h.track, h.id))
    assert all(h.track and h.id for h in items)


def test_unknown_id_fails_closed():
    with pytest.raises(HypothesisError, match="unknown hypothesis"):
        get_hypothesis("does-not-exist", load_registry(HYPOTHESES))


def test_filename_must_match_id(tmp_path):
    (tmp_path / "mismatch.yaml").write_text(
        "id: something-else\ntrack: GaugeGap\n", encoding="utf-8"
    )
    with pytest.raises(HypothesisError, match="does not match filename"):
        load_registry(tmp_path)


def test_missing_track_fails_closed(tmp_path):
    (tmp_path / "x-0001.yaml").write_text("id: x-0001\n", encoding="utf-8")
    with pytest.raises(HypothesisError, match="missing a non-empty track"):
        load_registry(tmp_path)


def test_empty_directory_fails_closed(tmp_path):
    with pytest.raises(HypothesisError, match="no hypothesis files"):
        load_registry(tmp_path)
