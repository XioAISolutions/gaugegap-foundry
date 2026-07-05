"""Reality-forge dataset scenes for the complete Foundry Experience."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from gaugegap.compactification_forge import run_compactification_suite
from gaugegap.entanglement_forge import run_entanglement_forge
from gaugegap.fractal_topology_forge import run_menger_forge
from gaugegap.perception_forge import run_perception_forge
from gaugegap.quantum.uqt_forge import run_uqt_forge


def _spectra_model(
    model_id: str,
    eigenvalues: list[float],
    *,
    dimension: int,
    spectral_gap: float,
    hermitian: bool = True,
) -> dict[str, Any]:
    return {
        "id": model_id,
        "eigenvalues": eigenvalues,
        "audit": {
            "dimension": dimension,
            "spectral_gap": spectral_gap,
            "hermitian": hermitian,
        },
    }


def uqt_scene() -> dict[str, Any]:
    report = run_uqt_forge(task="all")
    models = []
    for task in report.tasks:
        models.append(
            _spectra_model(
                task.task_id,
                [0.0, task.row_permutation_fraction, task.accuracy],
                dimension=task.case_count,
                spectral_gap=task.accuracy - task.row_permutation_fraction,
                hermitian=True,
            )
        )
    return {
        "kind": "spectra",
        "id": "uqt-algebra",
        "label": "Quantum Algebra Interface",
        "description": "UQT-inspired finite algebra known-answer and reversibility controls",
        "equations": [
            "params = V*N_emb*4 + L*N*3",
            "U_layer = CNOT_ring * product_i SU(2)_i",
            "Z_11 add and Z_11* multiply are row-permutation controls",
            "Z_11 multiply with zero is the irreversible negative control",
        ],
        "models": models,
        "report": report.summary(),
        "claim_boundary": report.claim_boundary,
    }


def entanglement_scene() -> dict[str, Any]:
    report = run_entanglement_forge()
    summary = report.summary()
    correlations = [term.expectation for term in report.correlations]
    return {
        "kind": "spectra",
        "id": "entanglement-bell",
        "label": "Bell Entanglement Boundary",
        "description": "Finite CHSH violation with explicit no-signaling audit",
        "equations": [
            "|psi> = (|01> - |10>) / sqrt(2)",
            "S = |E00 + E01 + E10 - E11|",
            "classical bound = 2, Tsirelson bound = 2*sqrt(2)",
            "Bluetooth is analogy only; no-signaling residual gates the claim",
        ],
        "models": [
            _spectra_model(
                "singlet-chsh",
                correlations,
                dimension=4,
                spectral_gap=summary["violation_margin"],
                hermitian=True,
            ),
            _spectra_model(
                "no-signaling",
                [summary["no_signaling_residual"], summary["entanglement_gap_score"]],
                dimension=len(summary["joint_probabilities"]),
                spectral_gap=summary["entanglement_gap_score"],
                hermitian=True,
            ),
        ],
        "report": summary,
        "claim_boundary": report.claim_boundary,
    }


def compactification_scene() -> dict[str, Any]:
    reports = run_compactification_suite()
    models = []
    for report in reports:
        masses = [mode.mass for mode in report.modes[:14]]
        models.append(
            _spectra_model(
                report.geometry,
                masses,
                dimension=report.mode_count,
                spectral_gap=report.first_excited_mass,
                hermitian=True,
            )
        )
    return {
        "kind": "spectra",
        "id": "compactification",
        "label": "Compact Hidden Dimensions",
        "description": "Finite KK/winding spectra for circle and torus toy compactifications",
        "equations": [
            "m^2 = m0^2 + sum_i (n_i/R_i)^2 + sum_i (w_i R_i/alpha')^2",
            "small R pushes momentum modes above a detector cutoff",
            "low-energy observer sees only the zero mode when excitations are too heavy",
        ],
        "models": models,
        "reports": [report.summary() for report in reports],
        "claim_boundary": reports[0].claim_boundary,
    }


def menger_sponge_scene() -> dict[str, Any]:
    report = run_menger_forge(iterations=4)
    volumes = [stage.volume for stage in report.stages]
    surfaces = [stage.surface_area for stage in report.stages]
    return {
        "kind": "spectra",
        "id": "menger-sponge",
        "label": "Menger Sponge Topology Gap",
        "description": "Finite fractal stages showing volume collapse and surface growth",
        "equations": [
            "N_n = 20^n",
            "V_n = (20/27)^n",
            "A_n = 2*(20/9)^n + 4*(8/9)^n",
            "dim_H = log(20)/log(3); topological dimension label is boundary-only",
        ],
        "models": [
            _spectra_model(
                "volume-collapse",
                volumes,
                dimension=len(report.stages),
                spectral_gap=report.volume_collapse_score,
                hermitian=True,
            ),
            _spectra_model(
                "surface-growth",
                surfaces,
                dimension=len(report.stages),
                spectral_gap=report.surface_growth_score,
                hermitian=True,
            ),
        ],
        "report": report.summary(),
        "claim_boundary": report.claim_boundary,
    }


def perception_scene() -> dict[str, Any]:
    report = run_perception_forge(world_count=12)
    truth = [world.truth_payoff for world in report.worlds]
    interface = [world.interface_payoff for world in report.worlds]
    return {
        "kind": "spectra",
        "id": "perception-interface",
        "label": "Fitness Beats Truth Toy Game",
        "description": "Finite Hoffman-inspired perception game with explicit resource limits",
        "equations": [
            "truth percepts = equal-width bins over hidden state",
            "interface percepts = bins keyed to action payoff",
            "share_{t+1}(i) = share_t(i)*payoff_i / mean_payoff",
            "control: rich truth removes the finite percept bottleneck",
        ],
        "models": [
            _spectra_model(
                "truth-coded",
                truth,
                dimension=report.world_count,
                spectral_gap=min(interface) - max(truth),
                hermitian=True,
            ),
            _spectra_model(
                "fitness-interface",
                interface,
                dimension=report.world_count,
                spectral_gap=report.minimum_payoff_advantage,
                hermitian=True,
            ),
        ],
        "report": report.summary(),
        "claim_boundary": report.claim_boundary,
    }


def enhance_dataset(dataset: dict[str, Any]) -> dict[str, Any]:
    output = deepcopy(dataset)
    scenes = list(output.get("scenes", []))
    new_scenes = [
        entanglement_scene(),
        uqt_scene(),
        compactification_scene(),
        perception_scene(),
        menger_sponge_scene(),
    ]
    existing = {scene.get("id") for scene in scenes}
    insertion = next(
        (index + 1 for index, scene in enumerate(scenes) if scene.get("id") == "no-hiding"),
        len(scenes),
    )
    for scene in reversed(new_scenes):
        if scene["id"] not in existing:
            scenes.insert(insertion, scene)
    output["scenes"] = scenes
    output["schema"] = "gaugegap.foundry_experience.v6"
    return output
