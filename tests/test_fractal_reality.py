from __future__ import annotations

import json

import numpy as np
import pytest

from gaugegap.fractal_reality import (
    ANALOGUE_LIBRARY,
    analyze_point,
    build_fractal_reality_manifest,
    compare_to_analogue,
    encode_brainsnn,
    julia_escape_grid,
    mandelbrot_orbit,
    sonification_events,
)


def test_known_bounded_and_escaping_points() -> None:
    bounded = analyze_point(0.0, 0.0, max_iterations=64)
    escaping = analyze_point(1.0, 1.0, max_iterations=64)
    assert not bounded.escaped
    assert bounded.features["boundedness"] == 1.0
    assert escaping.escaped
    assert escaping.escape_iteration < 5
    assert escaping.features["escape_speed"] > 0.9


def test_orbit_validation() -> None:
    with pytest.raises(ValueError):
        mandelbrot_orbit(0j, max_iterations=0)
    with pytest.raises(ValueError):
        mandelbrot_orbit(0j, escape_radius=1.0)


def test_julia_grid_is_finite_and_deterministic() -> None:
    first = julia_escape_grid(complex(-0.8, 0.156), width=24, height=18, max_iterations=32)
    second = julia_escape_grid(complex(-0.8, 0.156), width=24, height=18, max_iterations=32)
    assert first.shape == (18, 24)
    assert np.array_equal(first, second)
    assert int(first.min()) >= 1
    assert int(first.max()) <= 32


def test_sonification_is_bounded() -> None:
    report = analyze_point(-0.75, 0.1, max_iterations=80)
    events = sonification_events(report, sample_limit=20)
    assert 1 <= len(events) <= 20
    assert all(45.0 <= event["frequency"] <= 4000.0 for event in events)
    assert all(-1.0 <= event["pan"] <= 1.0 for event in events)
    assert all(0.0 < event["gain"] <= 0.22 for event in events)


def test_brainsnn_encoding_is_deterministic_and_bounded() -> None:
    report = analyze_point(-0.1011, 0.9563, max_iterations=96)
    first = encode_brainsnn(report, steps=48)
    second = encode_brainsnn(report, steps=48)
    assert first == second
    assert len(first["regions"]) == 7
    assert all(0.0 <= value <= 1.0 for value in first["activation"].values())
    assert "not a trained biological model" in first["claim_boundary"]


def test_comparisons_preserve_evidence_layer_and_gap() -> None:
    report = analyze_point(-0.743643887, 0.131825904, max_iterations=128)
    comparison = compare_to_analogue(report, "neuron_branching", user_prediction=0.8)
    assert comparison.evidence_layer == "structural_analogy"
    assert 0.0 <= comparison.measured_similarity <= 1.0
    assert comparison.gauge_gap == pytest.approx(abs(0.8 - comparison.measured_similarity))
    with pytest.raises(KeyError):
        compare_to_analogue(report, "not-real")


def test_manifest_is_hashed_json_and_covers_all_analogues() -> None:
    manifest = build_fractal_reality_manifest(max_iterations=32)
    assert manifest["schema"] == "gaugegap.fractal_reality.v1"
    assert len(manifest["experiments"]) == 4
    assert set(manifest["analogues"]) == set(ANALOGUE_LIBRARY)
    assert len(manifest["content_sha256"]) == 64
    json.dumps(manifest, sort_keys=True)
    assert "literal code" in " ".join(manifest["do_not_claim"])
