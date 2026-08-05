"""Standalone HTML reports for Jump Lab artifacts and benchmarks."""

from __future__ import annotations

from html import escape
import json
from pathlib import Path
from typing import Any


def _json(value: Any) -> str:
    return escape(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def _winner(artifact: dict[str, Any]) -> dict[str, Any]:
    hypotheses = artifact.get("hypotheses", [])
    return max(hypotheses, key=lambda item: item.get("score", 0.0)) if hypotheses else {}


def _world_copy(artifact: dict[str, Any]) -> tuple[str, str, str, str]:
    world = str(artifact.get("experiment", {}).get("world", "unknown-world"))
    if world.startswith("force-mass-cart"):
        return (
            "The Force/Mass Cart",
            "1 · Synthetic force/mass cart world",
            (
                "Two black-box carts expose matching kinematics while force and "
                "mass remain hidden until an allowed intervention probes them."
            ),
            (
                "This is a frictionless constant-force Newtonian toy world. It "
                "demonstrates scoped latent-parameter abduction; it does not validate "
                "the candidate in real mechanical systems."
            ),
        )
    return (
        "The Elevator",
        "1 · Synthetic elevator world",
        (
            "Two black boxes expose the same local mechanical interface while their "
            "causal state remains hidden from the executive."
        ),
        (
            "This is a deterministic Newtonian toy-world benchmark. It demonstrates "
            "an auditable experience-to-hypothesis-to-scoped-axiom pipeline; it does "
            "not implement general relativity or establish unrestricted machine discovery."
        ),
    )


def render_discovery_html(artifact: dict[str, Any]) -> str:
    """Render the five-panel public demonstration as one portable HTML file."""
    winner = _winner(artifact)
    metrics = artifact.get("metrics", {})
    observations = artifact.get("experience", {}).get("initial_observations", [])
    trajectories = artifact.get("trajectories", [])
    axiom = artifact.get("candidate_axiom") or {
        "status": "not_compiled",
        "reason": "The configured evidence threshold was not reached.",
    }
    verification = artifact.get("verification", {})
    world_title, panel_title, world_description, claim_boundary = _world_copy(artifact)
    trajectory_rows = "".join(
        "<tr>"
        f"<td>{index + 1}</td>"
        f"<td>{escape(str(item.get('intervention', {}).get('action_type', 'unknown')))}</td>"
        f"<td>{escape(str(item.get('local_match')))}</td>"
        f"<td>{escape(str(item.get('external_difference', item.get('latent_difference'))))}</td>"
        f"<td>{escape(', '.join(item.get('discriminated_hypotheses', [])))}</td>"
        "</tr>"
        for index, item in enumerate(trajectories)
    )
    hypothesis_cards = "".join(
        "<article class='hypothesis'>"
        f"<h3>{escape(str(item.get('id')))} · {escape(str(item.get('class')))}</h3>"
        f"<p>{escape(str(item.get('statement')))}</p>"
        f"<strong>Score {float(item.get('score', 0.0)):.3f}</strong>"
        f"<small>{escape(str(item.get('status', 'active')))}</small>"
        "</article>"
        for item in sorted(
            artifact.get("hypotheses", []),
            key=lambda candidate: candidate.get("score", 0.0),
            reverse=True,
        )
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GaugeGap Jump Lab · {escape(str(artifact.get('experiment', {}).get('id', 'run')))}</title>
<style>
:root{{--bg:#07111f;--panel:#0e1b2f;--line:#263b59;--text:#e9f1ff;--muted:#9fb2ce;--accent:#7bdcff;--ok:#87efb1;}}
*{{box-sizing:border-box}} body{{margin:0;background:linear-gradient(145deg,#07111f,#0b1730);color:var(--text);font:16px/1.5 ui-sans-serif,system-ui,-apple-system,sans-serif}}
main{{width:min(1440px,96vw);margin:0 auto;padding:32px 0 60px}} header{{display:flex;justify-content:space-between;gap:24px;align-items:end;margin-bottom:22px}}
h1{{margin:0;font-size:clamp(2rem,5vw,4.5rem);line-height:.95}} .eyebrow{{color:var(--accent);text-transform:uppercase;letter-spacing:.16em;font-weight:800}}
.grid{{display:grid;grid-template-columns:repeat(12,1fr);gap:16px}} .panel{{background:rgba(14,27,47,.94);border:1px solid var(--line);border-radius:18px;padding:20px;box-shadow:0 20px 60px rgba(0,0,0,.22)}}
.panel h2{{margin-top:0}} .world{{grid-column:span 5}} .sensors{{grid-column:span 7}} .hypotheses{{grid-column:span 7}} .interventions{{grid-column:span 5}} .axiom{{grid-column:span 12}}
.statline{{display:flex;gap:14px;flex-wrap:wrap}} .stat{{padding:9px 12px;border:1px solid var(--line);border-radius:999px;color:var(--muted)}} .stat strong{{color:var(--text)}}
pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#07111f;border:1px solid var(--line);border-radius:12px;padding:14px;color:#dce9ff}}
table{{width:100%;border-collapse:collapse}} th,td{{text-align:left;padding:9px;border-bottom:1px solid var(--line);vertical-align:top}} th{{color:var(--muted)}}
.hypothesis-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}} .hypothesis{{border:1px solid var(--line);border-radius:12px;padding:13px}} .hypothesis h3{{margin:0 0 8px}} .hypothesis small{{display:block;color:var(--muted)}}
.verdict{{font-size:1.25rem;color:var(--ok);font-weight:800}} footer{{margin-top:18px;color:var(--muted)}}
@media(max-width:900px){{.world,.sensors,.hypotheses,.interventions,.axiom{{grid-column:span 12}} .hypothesis-grid{{grid-template-columns:1fr}} header{{align-items:start;flex-direction:column}}}}
</style>
</head>
<body><main>
<header><div><div class="eyebrow">GaugeGap Jump Lab v0.3</div><h1>{escape(world_title)}</h1></div><div class="statline">
<span class="stat">Policy <strong>{escape(str(metrics.get('policy', 'unknown')))}</strong></span>
<span class="stat">Experiments <strong>{escape(str(metrics.get('experiments_run', len(trajectories))))}</strong></span>
<span class="stat">Winner <strong>{escape(str(winner.get('id', 'none')))}</strong></span>
</div></header>
<section class="grid">
<article class="panel world"><h2>{escape(panel_title)}</h2><p>{escape(world_description)}</p><pre>{_json(artifact.get('experiment', {}))}</pre></article>
<article class="panel sensors"><h2>2 · Sensor experience</h2><p>The raw observations remain separate from the later interpretation.</p><pre>{_json(observations)}</pre></article>
<article class="panel hypotheses"><h2>3 · Competing hypotheses</h2><div class="hypothesis-grid">{hypothesis_cards}</div></article>
<article class="panel interventions"><h2>4 · Interventions</h2><table><thead><tr><th>#</th><th>Action</th><th>Local match</th><th>Boundary difference</th><th>Discriminates</th></tr></thead><tbody>{trajectory_rows}</tbody></table></article>
<article class="panel axiom"><h2>5 · Candidate axiom and deterministic verdict</h2><p class="verdict">{escape(str(verification.get('verdict', 'not_verified')))}</p><div class="grid"><div style="grid-column:span 7"><h3>Scoped candidate</h3><pre>{_json(axiom)}</pre></div><div style="grid-column:span 5"><h3>Verification</h3><pre>{_json(verification)}</pre></div></div></article>
</section>
<footer><strong>Claim boundary:</strong> {escape(claim_boundary)}<br>Artifact hash: {escape(str(artifact.get('provenance', {}).get('artifact_hash', 'missing')))}</footer>
</main></body></html>"""


def render_benchmark_html(report: dict[str, Any]) -> str:
    """Render a compact A/B benchmark report."""
    paired = report.get("paired_summary", {})
    rows = "".join(
        "<tr>"
        f"<td>{escape(str(item.get('seed')))}</td>"
        f"<td>{escape(str(item.get('salience', {}).get('experiments_run')))}</td>"
        f"<td>{escape(str(item.get('baseline', {}).get('experiments_run')))}</td>"
        f"<td>{escape(str(item.get('saved_experiments')))}</td>"
        f"<td>{escape(str(item.get('same_winner')))}</td>"
        "</tr>"
        for item in report.get("runs", [])
    )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Jump Lab Salience Benchmark</title><style>body{{font:16px/1.5 system-ui;margin:0;background:#08111f;color:#edf4ff}}main{{width:min(1100px,94vw);margin:40px auto}}section{{background:#101d31;border:1px solid #2b405f;border-radius:16px;padding:20px;margin:16px 0}}table{{width:100%;border-collapse:collapse}}th,td{{padding:10px;border-bottom:1px solid #2b405f;text-align:left}}pre{{white-space:pre-wrap;background:#08111f;padding:16px;border-radius:12px}}strong{{color:#80e6b0}}</style></head><body><main><h1>BrainSNN-style salience A/B benchmark</h1><section><h2>Paired result</h2><p>Mean experiments saved: <strong>{escape(str(paired.get('mean_experiments_saved', 0.0)))}</strong></p><p>Same-winner rate: <strong>{escape(str(paired.get('same_winner_rate', 0.0)))}</strong></p><p>Both-policy completion rate: <strong>{escape(str(paired.get('both_complete_rate', 0.0)))}</strong></p></section><section><h2>Runs</h2><table><thead><tr><th>Seed</th><th>Salience</th><th>Fixed baseline</th><th>Saved</th><th>Same winner</th></tr></thead><tbody>{rows}</tbody></table></section><section><h2>Raw benchmark</h2><pre>{_json(report)}</pre></section><p>This benchmark measures experiment ordering inside one deterministic toy world. It does not establish that spiking control is generally superior.</p></main></body></html>"""


def write_html(content: str, path: str | Path) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return destination
