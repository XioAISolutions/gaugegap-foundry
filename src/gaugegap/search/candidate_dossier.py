from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from gaugegap.models.z2_plaquette import CLAIM_BOUNDARY


def candidate_to_json(candidate: dict[str, object]) -> str:
    return json.dumps(candidate, indent=2, sort_keys=True, default=str) + "\n"


def candidate_to_markdown(candidate: dict[str, object]) -> str:
    candidate_id = str(candidate.get("candidate_id", "unknown-candidate"))
    score = float(candidate.get("score", 0.0))
    status = str(candidate.get("status", "unknown"))
    components = candidate.get("score_components", {})
    records = candidate.get("records", [])
    if not isinstance(components, dict):
        components = {}
    if not isinstance(records, list):
        records = []

    lines = [
        f"# {candidate_id}",
        "",
        "## Boundary",
        "",
        f"> {candidate.get('claim_boundary', CLAIM_BOUNDARY)}",
        "",
        "This dossier is finite-system exploration only. It is not a Yang-Mills proof and does not make a continuum mass-gap claim.",
        "",
        "## Rank Summary",
        "",
        f"- Hypothesis: `{candidate.get('hypothesis_id', 'gaugegap-search-0001')}`",
        f"- Model: `{candidate.get('model', 'unknown')}`",
        f"- Status: `{status}`",
        f"- Score: `{score:.12g}`",
        f"- Plaquette coupling J: `{candidate.get('plaquette_coupling', 'mixed')}`",
        f"- Finite sizes: `{candidate.get('n_plaquettes', [])}`",
        f"- Transverse fields h: `{candidate.get('transverse_fields', [])}`",
        "",
        "## Score Components",
        "",
    ]
    for key in sorted(components):
        try:
            value = float(components[key])
            lines.append(f"- `{key}`: `{value:.12g}`")
        except (TypeError, ValueError):
            lines.append(f"- `{key}`: `{components[key]}`")

    lines.extend([
        "",
        "## Gap Profile",
        "",
        "| n_plaquettes | h | gap | residual | Pauli replica |",
        "|---:|---:|---:|---:|---|",
    ])
    for record in records:
        if not isinstance(record, dict):
            continue
        params = record.get("params", {})
        replica = record.get("pauli_replica", {})
        if not isinstance(params, dict):
            params = {}
        if not isinstance(replica, dict):
            replica = {}
        lines.append(
            "| {n} | {h:.8g} | {gap:.12g} | {residual:.4g} | {replica_status} |".format(
                n=params.get("n_plaquettes", "?"),
                h=float(params.get("transverse_field", 0.0)),
                gap=float(record.get("value", 0.0)),
                residual=float(record.get("residual_norm", 0.0)),
                replica_status=replica.get("status", "unknown"),
            )
        )

    lines.extend([
        "",
        "## Why This Candidate Is Interesting",
        "",
        str(candidate.get("summary", "Candidate ranked by finite spectral-gap search.")),
        "",
        "A useful candidate has a clean exact-diagonalization baseline, low residuals, Pauli-replica agreement, and a gap profile that does not immediately collapse under the finite-size and perturbation checks used here.",
        "",
        "## Why This Is Not a Yang-Mills Proof",
        "",
        "This is a finite Z2 toy lattice system. The continuum Yang-Mills mass-gap problem requires a rigorous construction of four-dimensional quantum Yang-Mills theory and proof of a positive mass gap. This dossier only ranks finite benchmark behavior.",
        "",
        "## Next Validation Step",
        "",
        "Run the top candidate through noiseless statevector simulation, shot-based Aer simulation, noisy Aer, and only then consider a tiny hardware execution path.",
        "",
    ])
    return "\n".join(lines)


def write_candidate_dossiers(output_dir: Path, candidates: Iterable[dict[str, object]], *, limit: int = 5) -> list[Path]:
    dossier_dir = output_dir / "dossiers"
    dossier_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for index, candidate in enumerate(list(candidates)[:limit], start=1):
        candidate_id = _safe_name(str(candidate.get("candidate_id", f"candidate-{index}")))
        json_path = dossier_dir / f"{index:02d}-{candidate_id}.json"
        md_path = dossier_dir / f"{index:02d}-{candidate_id}.md"
        json_path.write_text(candidate_to_json(candidate), encoding="utf-8")
        md_path.write_text(candidate_to_markdown(candidate), encoding="utf-8")
        written.extend([json_path, md_path])
    return written


def write_markdown_summary(path: Path, candidates: list[dict[str, object]]) -> None:
    lines = [
        "# gaugegap-search-0001 Candidate Ranking",
        "",
        f"> {CLAIM_BOUNDARY}",
        "",
        "This is finite-system candidate mining. It is not a Yang-Mills proof.",
        "",
        "| rank | candidate_id | score | status | mean_gap | min_gap |",
        "|---:|---|---:|---|---:|---:|",
    ]
    for rank, candidate in enumerate(candidates, start=1):
        components = candidate.get("score_components", {})
        if not isinstance(components, dict):
            components = {}
        lines.append(
            "| {rank} | `{candidate_id}` | {score:.12g} | `{status}` | {mean_gap:.12g} | {min_gap:.12g} |".format(
                rank=rank,
                candidate_id=candidate.get("candidate_id", "unknown"),
                score=float(candidate.get("score", 0.0)),
                status=candidate.get("status", "unknown"),
                mean_gap=float(components.get("mean_gap", 0.0)),
                min_gap=float(components.get("min_gap", 0.0)),
            )
        )
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in value)[:120]
