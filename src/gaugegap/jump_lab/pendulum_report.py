"""Standalone report for one blinded pendulum holdout run."""

from __future__ import annotations

from html import escape
import json
from typing import Any


def _json(value: Any) -> str:
    return escape(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def render_pendulum_html(artifact: dict[str, Any]) -> str:
    metrics = artifact.get("metrics", {})
    blind = artifact.get("blind_protocol", {})
    winner = max(
        artifact.get("hypotheses", []),
        key=lambda item: float(item.get("score", 0.0)),
    )
    trajectories = artifact.get("trajectories", [])
    rows = "".join(
        "<tr>"
        f"<td>{escape(str(item.get('evidence_ref')))}</td>"
        f"<td>{escape(str(item.get('intervention', {}).get('action_type')))}</td>"
        f"<td>{escape(str(item.get('observed_signature')))}</td>"
        f"<td>{escape(str(item.get('local_match')))}</td>"
        f"<td>{escape(str(item.get('scope_boundary')))}</td>"
        "</tr>"
        for item in trajectories
    )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>GaugeGap Blind Pendulum Holdout</title><style>body{{font:16px/1.5 system-ui;margin:0;background:#07111f;color:#eef5ff}}main{{width:min(1220px,94vw);margin:36px auto}}section{{background:#101d31;border:1px solid #29415f;border-radius:16px;padding:20px;margin:16px 0}}.stats{{display:flex;gap:10px;flex-wrap:wrap}}.stat{{padding:8px 12px;border:1px solid #29415f;border-radius:999px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:9px;border-bottom:1px solid #29415f;text-align:left}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#07111f;padding:14px;border-radius:10px}}strong{{color:#87e9b4}}</style></head><body><main><h1>GaugeGap Jump Lab v0.4 · Blinded pendulum holdout</h1><div class="stats"><span class="stat">Winner <strong>{escape(str(winner.get('id')))}</strong></span><span class="stat">Correct <strong>{escape(str(metrics.get('blind_selection_correct')))}</strong></span><span class="stat">Complete <strong>{escape(str(metrics.get('discovery_complete')))}</strong></span><span class="stat">Leakage hits <strong>{escape(str(len(blind.get('leakage_hits', []))))}</strong></span></div><section><h2>Anonymous model deck</h2><p>Semantic statements were withheld during selection and revealed only in this post-run report.</p><pre>{_json(artifact.get('hypotheses', []))}</pre></section><section><h2>Evidence sequence</h2><table><thead><tr><th>Evidence</th><th>Intervention</th><th>Observed signature</th><th>Pair match</th><th>Scope boundary</th></tr></thead><tbody>{rows}</tbody></table></section><section><h2>Candidate axiom and verifier</h2><pre>{_json({'candidate_axiom': artifact.get('candidate_axiom'), 'verification': artifact.get('verification')})}</pre></section><section><h2>Blind protocol</h2><pre>{_json(blind)}</pre></section><p><strong>Claim boundary:</strong> This is blinded selection among pre-registered models in an ideal deterministic pendulum toy world. It is not open-ended hypothesis invention or real-world experimental validation.</p><p>Artifact hash: {escape(str(artifact.get('provenance', {}).get('artifact_hash', 'missing')))}</p></main></body></html>"""
