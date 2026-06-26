from __future__ import annotations

import json
from pathlib import Path

import pytest

from gaugegap.experience import build_experience, build_manifest, scan_artifacts


def _seed_results(root: Path) -> None:
    run = root / "flowgap-0002-attractor-forge"
    run.mkdir(parents=True)
    (run / "summary.json").write_text(
        json.dumps(
            {
                "system": "rossler",
                "claim_boundary": "Finite-time numerical evidence only.",
                "lyapunov": [0.07, 0.0, -5.3],
            }
        ),
        encoding="utf-8",
    )
    (run / "projection_xy.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0L1 1"/></svg>',
        encoding="utf-8",
    )
    (run / "certificate.lean").write_text(
        "-- CLAIM BOUNDARY: algebraic divergence inequality only\nexample : 1 = 1 := by rfl\n",
        encoding="utf-8",
    )


def test_scan_artifacts_is_sorted_and_extracts_claims(tmp_path: Path) -> None:
    _seed_results(tmp_path)
    records = scan_artifacts(tmp_path)
    assert [record.path for record in records] == sorted(record.path for record in records)
    assert len(records) == 3
    summary = next(record for record in records if record.path.endswith("summary.json"))
    assert summary.claim_boundary == "Finite-time numerical evidence only."
    assert len(summary.sha256) == 64


def test_manifest_is_deterministic(tmp_path: Path) -> None:
    _seed_results(tmp_path)
    first = build_manifest(tmp_path)
    second = build_manifest(tmp_path)
    assert first == second
    assert first["schema"] == "gaugegap-foundry-experience/v1"
    assert first["artifact_count"] == 3
    assert len(first["manifest_sha256"]) == 64


def test_build_experience_contains_both_modes_and_no_external_runtime(tmp_path: Path) -> None:
    results = tmp_path / "results"
    _seed_results(results)
    output = tmp_path / "site" / "index.html"
    manifest = build_experience(results, output, title="Test Foundry", strict=True)
    html = output.read_text(encoding="utf-8")
    assert manifest["artifact_count"] == 3
    assert "EXPERIENCE" in html
    assert "EXPERIMENT" in html
    assert "Finite-time numerical evidence only." in html
    assert "projection_xy.svg" in html
    assert "https://" not in html
    assert "http://" not in html.replace('xmlns="http://www.w3.org/2000/svg"', "")
    assert output.with_suffix(".manifest.json").exists()


def test_repeat_build_is_byte_identical(tmp_path: Path) -> None:
    results = tmp_path / "results"
    _seed_results(results)
    output = tmp_path / "site" / "foundry-experience" / "index.html"
    first = build_experience(results, output, strict=True)
    first_html = output.read_bytes()
    first_manifest = output.with_suffix(".manifest.json").read_bytes()
    second = build_experience(results, output, strict=True)
    assert first == second
    assert output.read_bytes() == first_html
    assert output.with_suffix(".manifest.json").read_bytes() == first_manifest


def test_strict_mode_rejects_empty_results(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="no supported artifacts"):
        build_experience(tmp_path, tmp_path / "index.html", strict=True)


def test_unsafe_script_terminator_is_escaped(tmp_path: Path) -> None:
    run = tmp_path / "gaugegap-0001"
    run.mkdir()
    (run / "summary.json").write_text(
        json.dumps({"claim_boundary": "finite </script><script>alert(1)</script>"}),
        encoding="utf-8",
    )
    output = tmp_path / "index.html"
    build_experience(tmp_path, output)
    rendered = output.read_text(encoding="utf-8")
    assert "</script><script>alert(1)</script>" not in rendered
    assert "<\/script>" in rendered
