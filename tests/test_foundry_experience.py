from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_foundry_experience.py"


def _module():
    spec = importlib.util.spec_from_file_location("foundry_experience_generator", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_smoke_payload_uses_real_registered_models():
    module = _module()
    payload = module.build_payload(smoke=True)
    channels = {item["id"]: item for item in payload["channels"]}

    assert payload["schema"] == "gaugegap.foundry_experience.v1"
    assert set(channels) == {"rossler", "lorenz", "thomas", "z2", "su3"}
    assert payload["audio"]["default"] == "off"
    assert payload["provenance"]["remote_assets"] == []

    for name in ("rossler", "lorenz", "thomas"):
        channel = channels[name]
        assert channel["kind"] == "attractor"
        assert len(channel["points"]) > 100
        assert all(len(point) == 3 for point in channel["points"])
        assert "not a formal proof" in channel["claim_boundary"]

    z2 = channels["z2"]
    assert z2["model"]["n_qubits"] == 4
    assert len(z2["records"]) == 25
    assert all(record["gap"] >= -1e-10 for record in z2["records"])
    assert "exact dense diagonalization" in z2["method"]

    su3 = channels["su3"]
    assert [item["dimension"] for item in su3["representations"]] == [8, 10]
    assert all(item["weyl_closed"] for item in su3["representations"])
    assert all(item["centroid"] == pytest.approx([0.0, 0.0]) for item in su3["representations"])


def test_bundle_is_self_contained_and_byte_deterministic(tmp_path):
    module = _module()
    first = tmp_path / "first"
    second = tmp_path / "second"
    module.write_bundle(first, smoke=True)
    module.write_bundle(second, smoke=True)

    for filename in ("index.html", "experience-data.json", "manifest.json"):
        assert (first / filename).read_bytes() == (second / filename).read_bytes()

    html = (first / "index.html").read_text(encoding="utf-8")
    assert "__FOUNDRY_DATA__" not in html
    assert "experience" in html
    assert "experiment" in html
    assert "sound off" in html
    assert "AudioContext" in html
    assert "<script src=" not in html
    assert "http://" not in html
    assert "https://" not in html
    assert "Millennium Prize solution" in html

    manifest = json.loads((first / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["deterministic"] is True
    assert manifest["self_contained"] is True
    assert manifest["audio_opt_in"] is True
    for filename, record in manifest["files"].items():
        assert record["sha256"] == _sha256(first / filename)
        assert record["bytes"] == (first / filename).stat().st_size


def test_cli_writes_bundle_outside_repository(tmp_path):
    output = tmp_path / "instrument"
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--smoke", "--output-dir", str(output)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    result = json.loads(completed.stdout)
    assert result["status"] == "pass"
    assert result["self_contained"] is True
    assert result["audio_opt_in"] is True
    assert {"index.html", "experience-data.json", "manifest.json"} <= {
        path.name for path in output.iterdir()
    }
