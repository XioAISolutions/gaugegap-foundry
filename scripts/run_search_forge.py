#!/usr/bin/env python3
"""Generate Search Forge evidence, preview SVG, and an offline interactive page."""
from __future__ import annotations

import argparse
from dataclasses import asdict
from fractions import Fraction
import html
import json
from pathlib import Path

from gaugegap.scientific_search_spaces import (
    HyperchargeState,
    repair_hypercharge,
    research_maturity_graph,
)
from gaugegap.search_forge import astar, dijkstra, manhattan, rectangular_grid
from gaugegap.symbolic_search import evaluate, null_distance_test

WIDTH = 17
HEIGHT = 11
START = (1, 1)
GOAL = (15, 9)
BLOCKED = {
    (4, y) for y in range(1, 9)
} | {
    (9, y) for y in range(2, 10)
} | {
    (x, 5) for x in range(5, 9)
} | {
    (x, 2) for x in range(10, 15)
}
BLOCKED.remove((4, 7))
BLOCKED.remove((9, 8))
BLOCKED.remove((12, 2))


def _grid_payload() -> dict[str, object]:
    graph = rectangular_grid(WIDTH, HEIGHT, blocked=BLOCKED)
    baseline = dijkstra(graph, START, GOAL)
    guided = astar(
        graph,
        START,
        GOAL,
        manhattan(GOAL),
        heuristic_name="manhattan",
        admissible_declared=True,
    )
    return {
        "width": WIDTH,
        "height": HEIGHT,
        "start": START,
        "goal": GOAL,
        "blocked": sorted(BLOCKED),
        "dijkstra": baseline.certificate(),
        "astar": guided.certificate(),
    }


def _anomaly_payload() -> dict[str, object]:
    perturbed = HyperchargeState(
        Fraction(1, 6), Fraction(7, 10), Fraction(-1, 3), Fraction(-1, 2), Fraction(-1)
    )
    target = HyperchargeState(
        Fraction(1, 6), Fraction(2, 3), Fraction(-1, 3), Fraction(-1, 2), Fraction(-1)
    )
    exact = repair_hypercharge(perturbed, target, field="y_u", step=Fraction(1, 30))
    guided = repair_hypercharge(
        perturbed,
        target,
        field="y_u",
        step=Fraction(1, 30),
        use_astar=True,
    )
    roadmap = dijkstra(research_maturity_graph(), "idea", "reviewer-packet")
    return {
        "repair_dijkstra": exact.certificate(),
        "repair_astar": guided.certificate(),
        "research_path": roadmap.certificate(),
        "claim_boundary": (
            "Search is exact only over the declared finite candidate graph; it does not prove "
            "uniqueness across all quantum field theories or all possible research plans."
        ),
    }


def _symbolic_payload() -> dict[str, object]:
    chai = evaluate("חי", cipher_name="hebrew-standard")
    messiah = evaluate("משיח", cipher_name="hebrew-standard")
    serpent = evaluate("נחש", cipher_name="hebrew-standard")
    null = null_distance_test(
        "SEARCH FORGE",
        target=evaluate("SEARCH FORGE").value,
        trials=500,
        seed=72,
    )
    return {
        "examples": [asdict(chai), asdict(messiah), asdict(serpent)],
        "equal_value_example": {
            "texts": [messiah.text, serpent.text],
            "value": messiah.value,
            "equal": messiah.value == serpent.value,
        },
        "null_model": null.summary(),
        "claim_boundary": (
            "Equal cipher totals are symbolic associations. They are not evidence of causation, "
            "prediction, elite coordination, or a physical mechanism."
        ),
    }


def build_payload() -> dict[str, object]:
    return {
        "schema": "gaugegap.search_forge.v1",
        "grid": _grid_payload(),
        "scientific": _anomaly_payload(),
        "symbolic": _symbolic_payload(),
    }


def _svg(payload: dict[str, object]) -> str:
    grid = payload["grid"]
    assert isinstance(grid, dict)
    dijkstra_cert = grid["dijkstra"]
    astar_cert = grid["astar"]
    assert isinstance(dijkstra_cert, dict) and isinstance(astar_cert, dict)
    cell = 25
    margin = 48
    panel_w = WIDTH * cell + 2 * margin
    panel_h = HEIGHT * cell + 125
    total_w = panel_w * 2

    def panel(offset: int, title: str, cert: dict[str, object], accent: str) -> str:
        expanded = {eval(item, {"__builtins__": {}}) for item in cert["expanded_order"]}
        path = {eval(item, {"__builtins__": {}}) for item in cert["path"]}
        bits = [f'<g transform="translate({offset},0)">']
        bits.append(f'<rect width="{panel_w}" height="{panel_h}" rx="22" fill="#0b0e14"/>')
        bits.append(f'<text x="{panel_w/2}" y="34" text-anchor="middle" fill="#f0f6fc" font-size="22" font-family="system-ui">{title}</text>')
        for y in range(HEIGHT):
            for x in range(WIDTH):
                px, py = margin + x * cell, 58 + y * cell
                node = (x, y)
                fill = "#161b22"
                if node in BLOCKED:
                    fill = "#30363d"
                elif node in expanded:
                    fill = "#173a52"
                if node in path:
                    fill = accent
                if node == START:
                    fill = "#3fb950"
                if node == GOAL:
                    fill = "#f85149"
                bits.append(f'<rect x="{px}" y="{py}" width="22" height="22" rx="3" fill="{fill}"/>')
        bits.append(f'<text x="{panel_w/2}" y="{panel_h-52}" text-anchor="middle" fill="#8b949e" font-size="14" font-family="monospace">cost {cert["path_cost"]} · expanded {cert["nodes_expanded"]}</text>')
        bits.append(f'<text x="{panel_w/2}" y="{panel_h-26}" text-anchor="middle" fill="#8b949e" font-size="12" font-family="monospace">same graph · same optimum · different search frontier</text>')
        bits.append('</g>')
        return "".join(bits)

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{panel_h}" viewBox="0 0 {total_w} {panel_h}">'
        '<rect width="100%" height="100%" fill="#010409"/>'
        + panel(0, "Dijkstra · exact baseline", dijkstra_cert, "#58a6ff")
        + panel(panel_w, "A* · admissible guidance", astar_cert, "#d2a8ff")
        + '</svg>'
    )


def _html(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Search Forge</title>
<style>
:root{{--bg:#010409;--panel:#0d1117;--line:#30363d;--text:#f0f6fc;--muted:#8b949e;--blue:#58a6ff;--violet:#d2a8ff;--green:#3fb950;--red:#f85149}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.45 system-ui,sans-serif}}
header{{padding:26px 32px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:24px;align-items:end}} h1{{margin:0;font-size:30px}} .sub{{color:var(--muted)}}
nav{{display:flex;gap:8px}} button{{background:#161b22;color:var(--text);border:1px solid var(--line);border-radius:8px;padding:9px 13px;cursor:pointer}} button.active{{border-color:var(--blue);color:var(--blue)}}
main{{padding:24px;max-width:1500px;margin:auto}} .view{{display:none}} .view.active{{display:block}} .grid2{{display:grid;grid-template-columns:1fr 1fr;gap:18px}} .card{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px}} canvas{{width:100%;height:auto;background:#05080d;border-radius:10px}}
.stats{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:12px}} .stat{{padding:10px;background:#161b22;border-radius:8px}} code,pre{{font-family:ui-monospace,monospace}} pre{{white-space:pre-wrap;color:#c9d1d9}} .boundary{{border-left:3px solid var(--violet);padding-left:12px;color:var(--muted)}}
@media(max-width:900px){{.grid2{{grid-template-columns:1fr}}header{{display:block}}nav{{margin-top:16px;flex-wrap:wrap}}}}
</style></head><body>
<header><div><h1>Search Forge</h1><div class="sub">Exact finite paths · heuristic acceleration · symbolic null controls</div></div>
<nav><button data-tab="maze" class="active">Dijkstra vs A*</button><button data-tab="science">Scientific paths</button><button data-tab="symbolic">Symbolic lab</button></nav></header>
<main>
<section id="maze" class="view active"><div class="grid2"><div class="card"><h2>Dijkstra</h2><canvas id="dcanvas" width="680" height="440"></canvas><div id="dstats" class="stats"></div></div><div class="card"><h2>A*</h2><canvas id="acanvas" width="680" height="440"></canvas><div id="astats" class="stats"></div></div></div><p class="boundary">Dijkstra certifies the minimum on the declared non-negative graph. A* carries that claim only under its declared heuristic contract.</p></section>
<section id="science" class="view"><div class="grid2"><div class="card"><h2>Anomaly repair</h2><pre id="repair"></pre></div><div class="card"><h2>Research maturity route</h2><pre id="research"></pre></div></div><p class="boundary">These are finite declared search spaces, not a proof that the chosen model or roadmap is unique in nature.</p></section>
<section id="symbolic" class="view"><div class="grid2"><div class="card"><h2>Historical examples</h2><pre id="examples"></pre></div><div class="card"><h2>Null-model control</h2><pre id="nullmodel"></pre></div></div><p class="boundary">Equal values are symbolic associations only. The null control exists to expose how easily target matches can be manufactured after the fact.</p></section>
</main>
<script>
const DATA={encoded};
const parseNode=s=>JSON.parse(s.replaceAll("(","[").replaceAll(")","]"));
function draw(canvasId,cert,accent){{const c=document.getElementById(canvasId),x=c.getContext('2d');const g=DATA.grid, sx=c.width/g.width, sy=c.height/g.height;const expanded=cert.expanded_order.map(parseNode), path=cert.path.map(parseNode);let i=0;function frame(){{x.fillStyle='#05080d';x.fillRect(0,0,c.width,c.height);for(const [bx,by] of g.blocked){{x.fillStyle='#30363d';x.fillRect(bx*sx+1,by*sy+1,sx-2,sy-2)}}for(const [px,py] of expanded.slice(0,i)){{x.fillStyle='#173a52';x.fillRect(px*sx+2,py*sy+2,sx-4,sy-4)}}if(i>=expanded.length)for(const [px,py] of path){{x.fillStyle=accent;x.fillRect(px*sx+4,py*sy+4,sx-8,sy-8)}}for(const [node,color] of [[g.start,'#3fb950'],[g.goal,'#f85149']]){{x.fillStyle=color;x.fillRect(node[0]*sx+3,node[1]*sy+3,sx-6,sy-6)}}if(i<=expanded.length){{i+=2;requestAnimationFrame(frame)}}}}frame()}}
function stats(id,cert){{document.getElementById(id).innerHTML=`<div class=stat><b>cost</b><br>${{cert.path_cost}}</div><div class=stat><b>expanded</b><br>${{cert.nodes_expanded}}</div><div class=stat><b>hash</b><br>${{cert.result_hash.slice(0,10)}}</div>`}}
draw('dcanvas',DATA.grid.dijkstra,'#58a6ff');draw('acanvas',DATA.grid.astar,'#d2a8ff');stats('dstats',DATA.grid.dijkstra);stats('astats',DATA.grid.astar);
document.getElementById('repair').textContent=JSON.stringify(DATA.scientific.repair_astar,null,2);document.getElementById('research').textContent=JSON.stringify(DATA.scientific.research_path,null,2);document.getElementById('examples').textContent=JSON.stringify(DATA.symbolic.examples.concat([DATA.symbolic.equal_value_example]),null,2);document.getElementById('nullmodel').textContent=JSON.stringify(DATA.symbolic.null_model,null,2);
for(const b of document.querySelectorAll('nav button'))b.onclick=()=>{{document.querySelectorAll('nav button,.view').forEach(e=>e.classList.remove('active'));b.classList.add('active');document.getElementById(b.dataset.tab).classList.add('active')}};
</script></body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="site/search-forge")
    parser.add_argument("--preview", default="figures/search-forge/search-forge.svg")
    args = parser.parse_args()

    payload = build_payload()
    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    Path(args.preview).parent.mkdir(parents=True, exist_ok=True)
    (output / "search-forge.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output / "index.html").write_text(_html(payload), encoding="utf-8")
    Path(args.preview).write_text(_svg(payload), encoding="utf-8")
    print(json.dumps({"output": str(output), "preview": args.preview, "schema": payload["schema"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
