from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_foundry_experience_complete.py"


def _load_complete_generator():
    spec = importlib.util.spec_from_file_location("complete_experience_test", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_complete_dataset_preserves_old_scenes_and_adds_all_extensions():
    module = _load_complete_generator()
    dataset = module.build_dataset()
    ids = [scene["id"] for scene in dataset["scenes"]]
    assert dataset["schema"] == "gaugegap.foundry_experience.v4"
    assert len(ids) == 10
    assert ids == [
        "rossler",
        "lorenz",
        "thomas",
        "lattice",
        "su3",
        "standard-model",
        "standard-model-anomalies",
        "no-hiding",
        "spectra",
        "limits",
    ]
    lagrangian = next(scene for scene in dataset["scenes"] if scene["id"] == "standard-model")
    assert lagrangian["audit"]["passed"]
    assert lagrangian["graph"]["summary"]["interaction_hyperedges"] == len(lagrangian["interactions"])
    assert lagrangian["observables"]["photon_mass_squared_residual"] < 1e-9
    anomaly = next(scene for scene in dataset["scenes"] if scene["id"] == "standard-model-anomalies")
    assert anomaly["exact"]["anomalies"]["passes"]
    assert not anomaly["failure_example"]["anomalies"]["passes"]
    assert anomaly["exact"]["composites"] == {"proton": "1", "neutron": "0"}
    no_hiding = next(scene for scene in dataset["scenes"] if scene["id"] == "no-hiding")
    assert no_hiding["suite"]["passed"]
    assert no_hiding["selected"]["recovery_fidelity"] == 1.0


def test_complete_generator_writes_interactive_extension_scenes(tmp_path: Path):
    output = tmp_path / "site"
    preview = tmp_path / "preview.svg"
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--output-dir", str(output), "--preview", str(preview)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    data = json.loads((output / "data.json").read_text(encoding="utf-8"))
    html = (output / "index.html").read_text(encoding="utf-8")
    manifest = json.loads((output / "research_manifest.json").read_text(encoding="utf-8"))
    assert len(data["scenes"]) == 10
    assert any(scene["id"] == "standard-model" for scene in data["scenes"])
    assert any(scene["id"] == "standard-model-anomalies" for scene in data["scenes"])
    assert any(scene["id"] == "no-hiding" for scene in data["scenes"])
    assert "drawLagrangian" in html
    assert "drawAnomaly" in html
    assert "drawNoHiding" in html
    assert "interaction graph" in html
    assert "Lagrangian Forge" in html
    assert "Anomaly Forge" in html
    assert "Information Cannot Disappear" in html
    assert manifest["claims"][0]["parameters"]["scene_count"] == 10
    assert preview.exists()
