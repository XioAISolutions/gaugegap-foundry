from __future__ import annotations

import json
from math import log, sqrt
from pathlib import Path
import subprocess
import sys

import pytest

from gaugegap.cli import load_config
from gaugegap.compactification_forge import compact_spectrum, run_compactification_suite
from gaugegap.entanglement_forge import run_entanglement_forge
from gaugegap.fractal_topology_forge import (
    is_retained_voxel,
    menger_stage,
    retained_voxel_coordinates,
    run_menger_forge,
)
from gaugegap.perception_forge import audit_world, run_perception_forge
from gaugegap.quantum_gap import compute_quantum_gap
from gaugegap.quantum.uqt_forge import build_circuit_skeleton, evaluate_task, run_uqt_forge
from gaugegap.reality_forge_scene import enhance_dataset

ROOT = Path(__file__).resolve().parents[1]


def test_uqt_algebra_known_answers_and_negative_control():
    add = evaluate_task("mod11-add")
    zero_mul = evaluate_task("mod11-mul")
    star_mul = evaluate_task("mod11-star-mul")
    s4 = evaluate_task("s4-cayley")

    assert add.passed
    assert star_mul.passed
    assert s4.passed
    assert zero_mul.passed
    assert zero_mul.negative_control
    assert not zero_mul.reversible_by_rows
    assert zero_mul.row_permutation_fraction < 1.0
    assert s4.case_count == 24 * 24


def test_uqt_circuit_parameter_count_matches_paper_style_formula():
    circuit = build_circuit_skeleton(vocab_size=11, n_qubits=5, embedding_qubits=4, layers=25)
    assert circuit.parameter_count == (11 * 4 * 4) + (25 * 5 * 3)
    assert circuit.dimension == 32
    assert circuit.unitarity_residual < 1e-12

    s4_circuit = build_circuit_skeleton(vocab_size=24, n_qubits=5, embedding_qubits=5, layers=14)
    assert s4_circuit.parameter_count == (24 * 5 * 4) + (14 * 5 * 3)


def test_uqt_runner_emits_evidence_bundle(tmp_path: Path):
    output = tmp_path / "uqt"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_uqt_forge.py"),
            "--task",
            "all",
            "--output-dir",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert summary["passed"]
    assert (output / "cases.csv").exists()
    assert (output / "ledger.jsonl").exists()
    assert (output / "uqt_forge.svg").exists()


def test_compactification_small_circle_hides_excited_modes_below_cutoff():
    report = compact_spectrum(geometry="S1 circle", radii=(0.08,), cutoff=8.0, max_mode=3)
    assert report.passed
    assert report.visible_mode_count == 1
    assert report.effective_dimension_label == "4D-only below cutoff"
    assert report.first_excited_mass > report.cutoff

    larger = compact_spectrum(geometry="S1 circle", radii=(1.0,), cutoff=8.0, max_mode=3)
    assert larger.visible_mode_count > report.visible_mode_count


def test_compactification_runner_emits_modes(tmp_path: Path):
    output = tmp_path / "compact"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_compactification_forge.py"),
            "--geometry",
            "suite",
            "--output-dir",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert summary["passed"]
    assert len(summary["reports"]) == 2
    assert (output / "modes.csv").exists()
    assert (output / "compactification_forge.svg").exists()


def test_perception_interface_outcompetes_truth_under_same_budget():
    world = audit_world(payoff_period=3, phase=0)
    assert world.interface_dominates
    assert world.truth_extinct
    assert world.interface_payoff > world.truth_payoff

    report = run_perception_forge(world_count=6)
    assert report.passed
    assert report.truth_extinction_fraction == pytest.approx(1.0)
    assert report.controls["rich_truth_control_payoff"] == pytest.approx(
        report.controls["rich_interface_control_payoff"]
    )


def test_perception_runner_emits_evidence_bundle(tmp_path: Path):
    output = tmp_path / "perception"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_perception_forge.py"),
            "--world-count",
            "4",
            "--output-dir",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert summary["passed"]
    assert summary["truth_extinction_fraction"] == pytest.approx(1.0)
    assert (output / "worlds.csv").exists()
    assert (output / "strategy_ledger.jsonl").exists()
    assert (output / "perception_forge.svg").exists()


def test_menger_sponge_finite_stage_formulas_and_runner(tmp_path: Path):
    stage = menger_stage(2)
    assert stage.retained_cubes == 400
    assert stage.removed_cubes == (27**2) - (20**2)
    assert stage.volume == pytest.approx((20 / 27) ** 2)
    assert stage.surface_area == pytest.approx(2 * (20 / 9) ** 2 + 4 * (8 / 9) ** 2)
    assert stage.porosity == pytest.approx(1 - stage.volume)
    assert stage.retained_fraction == pytest.approx((20 / 27) ** 2)
    assert stage.hausdorff_dimension_estimate == pytest.approx(log(20) / log(3))
    assert is_retained_voxel(0, 0, 0, 2)
    assert not is_retained_voxel(1, 1, 0, 2)
    assert len(retained_voxel_coordinates(1)) == 20

    report = run_menger_forge(iterations=4)
    assert report.passed
    assert report.volume_collapse_score > 0.0
    assert report.surface_growth_score > 0.0
    assert report.voxel_sample
    assert report.voxel_sample_truncated
    assert report.summary()["limit_trends"]["volume_limit"] == 0.0

    output = tmp_path / "menger"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_menger_sponge_forge.py"),
            "--iterations",
            "3",
            "--output-dir",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert (output / "summary.json").exists()
    assert (output / "stages.csv").exists()
    assert (output / "voxels.csv").exists()
    assert (output / "menger_sponge_forge.svg").exists()


def test_entanglement_bell_chsh_and_no_signaling_runner(tmp_path: Path):
    report = run_entanglement_forge()
    assert report.passed
    assert report.chsh_value == pytest.approx(2 * sqrt(2))
    assert report.classical_control_chsh == pytest.approx(2.0)
    assert report.no_signaling_residual < 1e-12
    assert report.local_marginal_min == pytest.approx(0.5)
    assert report.local_marginal_max == pytest.approx(0.5)
    assert report.entanglement_gap_score == pytest.approx(1.0)
    assert any(item["name"] == "quantum teleportation" for item in report.summary()["technology_context"])

    output = tmp_path / "entanglement"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_entanglement_forge.py"),
            "--output-dir",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert (output / "summary.json").exists()
    assert (output / "correlations.csv").exists()
    assert (output / "joint_probabilities.csv").exists()
    assert (output / "entanglement_forge.svg").exists()


def test_quantum_gap_functional_fails_closed_and_passes_with_all_terms():
    dynamics = [
        {
            "dmd": {"reconstruction_error": 0.01},
            "validated_step": {"validated": True},
        }
    ]
    hamiltonians = [
        {
            "audit": {
                "spectral_gap": 0.5,
                "ground_energy": -1.0,
                "first_excited_energy": -0.5,
            }
        }
    ]
    uqt = run_uqt_forge(task="all").summary()
    compact = [report.summary() for report in run_compactification_suite()]
    perception = run_perception_forge(world_count=4).summary()
    menger = run_menger_forge(iterations=4).summary()
    entanglement = run_entanglement_forge().summary()

    report = compute_quantum_gap(
        dynamics=dynamics,
        hamiltonians=hamiltonians,
        uqt_summary=uqt,
        compact_summaries=compact,
        perception_summary=perception,
        validation_gate=True,
        menger_summary=menger,
        entanglement_summary=entanglement,
    )
    assert report.passed
    assert report.score > 0.0
    assert {term.name for term in report.terms} == {
        "normalized_hamiltonian_gap",
        "validated_dynamics_coherence",
        "uqt_reversibility_gap",
        "uqt_unitarity_confidence",
        "compactification_visibility_gap",
        "fitness_interface_gap",
        "fractal_topology_gap",
        "entanglement_nonlocality_gap",
    }

    failed = compute_quantum_gap(
        dynamics=dynamics,
        hamiltonians=hamiltonians,
        uqt_summary=uqt,
        compact_summaries=compact,
        perception_summary=perception,
        validation_gate=False,
        menger_summary=menger,
        entanglement_summary=entanglement,
    )
    assert not failed.passed
    assert failed.score == 0.0


def test_foundry_config_registers_quantum_reality_forges():
    config = load_config(ROOT / "config" / "foundry.yaml")
    assert "uqt-0001-algebra" in config.units
    assert "compact-0001-hidden-circle" in config.units
    assert "perception-0001-fitness-interface" in config.units
    assert "menger-0001-topology" in config.units
    assert "entangle-0001-bell" in config.units
    assert config.groups["quantum-reality-forges"] == (
        "uqt-smoke",
        "compactification-smoke",
        "perception-smoke",
    )
    assert config.groups["topology-entanglement-forges"] == (
        "menger-smoke",
        "entanglement-smoke",
    )
    assert config.groups["brainsnn-showcase"] == ("brainsnn-gaugegap-showcase",)


def test_brainsnn_showcase_exporter_emits_handoff_package(tmp_path: Path):
    output = tmp_path / "brainsnn"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "export_brainsnn_showcase.py"),
            "--output-dir",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads((output / "showcase.json").read_text(encoding="utf-8"))
    assert payload["schema"] == "gaugegap.brainsnn_showcase.v1"
    assert len(payload["cards"]) == 6
    assert any(card["title"] == "Menger Sponge Forge" for card in payload["cards"])
    assert any(card["title"] == "Entanglement Forge" for card in payload["cards"])
    assert (output / "showcase.md").exists()


def test_reality_forge_scenes_extend_complete_dataset():
    dataset = enhance_dataset({"schema": "base", "scenes": [{"id": "no-hiding"}]})
    ids = [scene["id"] for scene in dataset["scenes"]]
    assert dataset["schema"] == "gaugegap.foundry_experience.v6"
    assert ids == [
        "no-hiding",
        "entanglement-bell",
        "uqt-algebra",
        "compactification",
        "perception-interface",
        "menger-sponge",
    ]
    for scene_id in (
        "entanglement-bell",
        "uqt-algebra",
        "compactification",
        "perception-interface",
        "menger-sponge",
    ):
        scene = next(scene for scene in dataset["scenes"] if scene["id"] == scene_id)
        assert scene["kind"] == "spectra"
        assert scene["claim_boundary"]
