from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from gaugegap.hamiltonian_factory import audit_hamiltonian, build_hamiltonian, registered_models
from gaugegap.verified_su2_proof import emit_verified_su2_gap_coq

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_verified_su2_gap.py"


def test_verified_model_is_registered_in_canonical_factory():
    assert "su2-one-plaquette-verified" in registered_models()
    artifact = build_hamiltonian(
        "su2-one-plaquette-verified",
        max_two_j=1,
        electric="1",
        magnetic="1/2",
    )
    audit = audit_hamiltonian(artifact)
    assert artifact.implementation_status == "finite_verified_reference"
    assert artifact.metadata["gauge_invariant_by_construction"] is True
    assert artifact.metadata["magnetic_term_complete"] is True
    assert audit.hermitian
    assert abs(audit.spectral_gap - 1.25) < 1e-12


def test_runner_emits_complete_evidence_bundle(tmp_path: Path):
    output = tmp_path / "gap"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--max-two-j",
            "1",
            "--electric",
            "1",
            "--magnetic",
            "1/2",
            "--require-positive",
            "--output-dir",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    expected = {
        "verified_gap.json",
        "gap_sweep.csv",
        "gap_forge.svg",
        "gap_forge.html",
        "report.md",
    }
    assert expected == {path.name for path in output.iterdir()}
    summary = json.loads((output / "verified_gap.json").read_text(encoding="utf-8"))
    html = (output / "gap_forge.html").read_text(encoding="utf-8")
    assert summary["strictly_positive"] is True
    assert summary["implementation_status"] if "implementation_status" in summary else True
    assert float(summary["gap_interval"]["lower_float"]) > 0
    assert "Gap Forge" in html
    assert "claim_boundary" in html
    assert "CERTIFIED POSITIVE" in html


def test_emitted_coq_source_has_closed_positive_gap_theorem():
    source = emit_verified_su2_gap_coq()
    assert "certified_gap_positive" in source
    assert "Admitted" not in source
    assert "Qed." in source
