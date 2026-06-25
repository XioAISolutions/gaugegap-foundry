#!/usr/bin/env python3
"""Run Attractor Forge: finite Rössler/Lorenz/Thomas dynamics diagnostics.

Produces deterministic trajectory and section data, three phase projections, a
return map, Lyapunov spectrum, short-horizon convergence evidence, sensitivity,
finite recurrence/correlation estimates, an optional bifurcation-style sweep, a
self-contained rotating HTML explorer, and hole-free Lean/Coq divergence bounds.

CLAIM BOUNDARY: these are finite-time numerical ODE diagnostics.  They are not
formal proofs of chaos, global attraction, fractal dimension, or ergodicity.  The
formal certificates prove only their stated algebraic divergence inequalities.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys
from typing import Iterable, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.flowgap_attractors import (  # noqa: E402
    SYSTEMS,
    analyze_attractor,
    get_system,
    parameter_sweep,
)
from gaugegap.ledger import git_state, object_hash, utc_run_id, write_jsonl  # noqa: E402
from gaugegap.visualization.svg import SVGCanvas  # noqa: E402


AXES = ("x", "y", "z")


def _parse_mapping(text: str) -> dict[str, float]:
    if not text.strip():
        return {}
    result: dict[str, float] = {}
    for item in text.split(","):
        if "=" not in item:
            raise argparse.ArgumentTypeError(f"expected key=value, got {item!r}")
        key, value = item.split("=", 1)
        try:
            result[key.strip()] = float(value)
        except ValueError as exc:
            raise argparse.ArgumentTypeError(f"invalid numeric value in {item!r}") from exc
    return result


def _parse_state(text: str) -> tuple[float, float, float]:
    try:
        values = tuple(float(value) for value in text.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("initial state must be x,y,z") from exc
    if len(values) != 3:
        raise argparse.ArgumentTypeError("initial state must contain exactly x,y,z")
    return values  # type: ignore[return-value]


def _downsample(values: np.ndarray, maximum: int) -> np.ndarray:
    if len(values) <= maximum:
        return values
    stride = max(1, int(np.ceil(len(values) / maximum)))
    return values[::stride][:maximum]


def _transform(points: np.ndarray, width: int, height: int, padding: int = 48):
    low = np.min(points, axis=0)
    high = np.max(points, axis=0)
    span = high - low
    span[span == 0.0] = 1.0

    def apply(point: Sequence[float]) -> tuple[float, float]:
        x = padding + (float(point[0]) - low[0]) / span[0] * (width - 2 * padding)
        y = height - padding - (float(point[1]) - low[1]) / span[1] * (height - 2 * padding)
        return x, y

    return apply


def _projection_svg(path: Path, states: np.ndarray, i: int, j: int, title: str) -> None:
    points = _downsample(states[:, [i, j]], 3500)
    canvas = SVGCanvas(720, 620)
    transform = _transform(points, canvas.width, canvas.height)
    canvas.polyline([transform(point) for point in points], stroke="#58a6ff", stroke_width=0.8, opacity=0.88)
    canvas.text(canvas.width / 2, 26, title, size=15)
    canvas.text(canvas.width / 2, canvas.height - 15, f"{AXES[i]} / {AXES[j]} finite trajectory projection", size=11, fill="#8b949e")
    canvas.write(path)


def _scatter_svg(
    path: Path,
    points: Iterable[tuple[float, float]],
    *,
    title: str,
    x_label: str,
    y_label: str,
    maximum: int = 5000,
) -> None:
    data = np.asarray(list(points), dtype=float).reshape((-1, 2))
    canvas = SVGCanvas(720, 620)
    if len(data) == 0:
        canvas.text(canvas.width / 2, canvas.height / 2, "No points for configured finite run", size=14)
    else:
        data = _downsample(data, maximum)
        transform = _transform(data, canvas.width, canvas.height)
        for point in data:
            canvas.circle(*transform(point), 1.7, fill="#f0c674", opacity=0.78)
    canvas.text(canvas.width / 2, 26, title, size=15)
    canvas.text(canvas.width / 2, canvas.height - 15, f"{x_label} → {y_label}", size=11, fill="#8b949e")
    canvas.write(path)


def _lyapunov_svg(path: Path, exponents: Sequence[float], system: str) -> None:
    values = np.asarray(exponents, dtype=float)
    canvas = SVGCanvas(640, 420)
    mid = 210
    canvas.line(55, mid, 600, mid, stroke="#8b949e")
    scale = 130.0 / max(1e-12, float(np.max(np.abs(values))))
    for index, value in enumerate(values):
        x = 135 + index * 175
        y = mid - float(value) * scale
        color = "#7ee787" if value >= 0.0 else "#ff7b72"
        canvas.line(x, mid, x, y, stroke=color, stroke_width=28)
        canvas.text(x, y - 14 if value >= 0.0 else y + 22, f"λ{index + 1}={value:.5g}", size=12)
    canvas.text(canvas.width / 2, 25, f"{system.title()} finite-time Lyapunov spectrum", size=15)
    canvas.text(canvas.width / 2, canvas.height - 18, "numerical estimate — not a proof of chaos", size=11, fill="#8b949e")
    canvas.write(path)


def _write_csv(path: Path, times: np.ndarray, states: np.ndarray) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("t", "x", "y", "z"))
        for time, state in zip(times, states):
            writer.writerow((f"{time:.17g}", *(f"{value:.17g}" for value in state)))


def _write_section_csv(path: Path, states: np.ndarray) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("x", "y", "z"))
        for state in states:
            writer.writerow(tuple(f"{value:.17g}" for value in state))


def _html_explorer(path: Path, states: np.ndarray, system: str, parameters: dict[str, float]) -> None:
    points = _downsample(states, 2600)
    payload = json.dumps([[round(float(v), 8) for v in row] for row in points], separators=(",", ":"))
    params = json.dumps(parameters, sort_keys=True)
    html = f"""<!doctype html>
<meta charset="utf-8">
<title>Attractor Forge — {system}</title>
<style>
body{{margin:0;background:#090d14;color:#e6edf3;font:14px system-ui;overflow:hidden}}
#hud{{position:fixed;left:16px;top:14px;background:#111827dd;padding:12px 14px;border:1px solid #30363d;border-radius:10px;max-width:390px}}
canvas{{display:block;width:100vw;height:100vh}}
input{{width:180px}} .small{{color:#8b949e;font-size:12px}}
</style>
<canvas id="c"></canvas>
<div id="hud"><b>Attractor Forge — {system.title()}</b><br><span class="small">parameters {params}</span><br>
yaw <input id="yaw" type="range" min="-3.14" max="3.14" value="0.7" step="0.01"><br>
pitch <input id="pitch" type="range" min="-1.55" max="1.55" value="0.35" step="0.01"><br>
zoom <input id="zoom" type="range" min="0.45" max="2.5" value="1" step="0.01"><br>
<label><input id="spin" type="checkbox" checked> rotate</label><br>
<span class="small">Finite numerical trajectory. Visual structure is not a formal proof of chaos.</span></div>
<script>
const pts={payload}; const c=document.getElementById('c'),g=c.getContext('2d');
const yaw=document.getElementById('yaw'),pitch=document.getElementById('pitch'),zoom=document.getElementById('zoom'),spin=document.getElementById('spin');
let auto=+yaw.value; const lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];
for(const p of pts)for(let i=0;i<3;i++){{lo[i]=Math.min(lo[i],p[i]);hi[i]=Math.max(hi[i],p[i]);}}
const center=lo.map((v,i)=>(v+hi[i])/2), span=Math.max(...hi.map((v,i)=>v-lo[i]))||1;
function size(){{c.width=innerWidth*devicePixelRatio;c.height=innerHeight*devicePixelRatio;}} addEventListener('resize',size);size();
function frame(){{if(spin.checked){{auto+=0.003;yaw.value=((auto+3.14)%6.28-3.14).toFixed(3);}}else auto=+yaw.value;
const Y=+yaw.value,P=+pitch.value,Z=+zoom.value,cy=Math.cos(Y),sy=Math.sin(Y),cp=Math.cos(P),sp=Math.sin(P);
g.fillStyle='#090d14';g.fillRect(0,0,c.width,c.height);g.strokeStyle='#58a6ff';g.lineWidth=1.05*devicePixelRatio;g.beginPath();
let first=true;for(const p0 of pts){{let x=(p0[0]-center[0])/span,y=(p0[1]-center[1])/span,z=(p0[2]-center[2])/span;
let x1=cy*x-sy*z,z1=sy*x+cy*z,y1=cp*y-sp*z1;let s=Math.min(c.width,c.height)*0.78*Z;
let X=c.width/2+x1*s,Yp=c.height/2-y1*s;if(first){{g.moveTo(X,Yp);first=false}}else g.lineTo(X,Yp);}}g.stroke();requestAnimationFrame(frame)}}frame();
</script>
"""
    path.write_text(html, encoding="utf-8")


def _default_sweep(system: str) -> tuple[str, float, float]:
    if system == "rossler":
        return "c", 3.5, 8.0
    if system == "lorenz":
        return "rho", 0.5, 42.0
    return "b", 0.12, 0.26


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--system", choices=sorted(SYSTEMS), default="rossler")
    parser.add_argument("--params", type=_parse_mapping, default={}, help="comma-separated key=value overrides")
    parser.add_argument("--initial", type=_parse_state, default=None, help="x,y,z")
    parser.add_argument("--dt", type=float, default=0.01)
    parser.add_argument("--steps", type=int, default=30000)
    parser.add_argument("--transient", type=int, default=5000)
    parser.add_argument("--sample-every", type=int, default=2)
    parser.add_argument("--lyapunov-steps", type=int, default=30000)
    parser.add_argument("--section-axis", type=int, choices=(0, 1, 2), default=0)
    parser.add_argument("--section-level", type=float, default=0.0)
    parser.add_argument("--section-direction", type=int, choices=(-1, 0, 1), default=1)
    parser.add_argument("--bifurcation-points", type=int, default=0)
    parser.add_argument("--bifurcation-steps", type=int, default=6000)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "flowgap-0002-attractor-forge")
    parser.add_argument("--skip-audit", action="store_true")
    args = parser.parse_args()

    system = get_system(args.system)
    initial = args.initial or system.default_state
    analysis = analyze_attractor(
        args.system,
        parameter_overrides=args.params,
        initial_state=initial,
        dt=args.dt,
        steps=args.steps,
        transient_steps=args.transient,
        sample_every=args.sample_every,
        lyapunov_steps=args.lyapunov_steps,
        poincare_axis=args.section_axis,
        poincare_level=args.section_level,
        poincare_direction=args.section_direction,
    )

    out = args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    transient_index = min(len(analysis.trajectory) - 1, args.transient // args.sample_every)
    retained = analysis.trajectory[transient_index:]
    retained_times = analysis.times[transient_index:]
    trajectory_for_files = _downsample(np.column_stack((retained_times, retained)), 12000)
    _write_csv(out / "trajectory.csv", trajectory_for_files[:, 0], trajectory_for_files[:, 1:])
    _write_section_csv(out / "poincare.csv", analysis.poincare)

    _projection_svg(out / "projection_xy.svg", retained, 0, 1, f"{args.system.title()} attractor — x/y")
    _projection_svg(out / "projection_xz.svg", retained, 0, 2, f"{args.system.title()} attractor — x/z")
    _projection_svg(out / "projection_yz.svg", retained, 1, 2, f"{args.system.title()} attractor — y/z")

    section_coordinate = (args.section_axis + 2) % 3
    section_values = analysis.poincare[:, section_coordinate] if len(analysis.poincare) else np.empty(0)
    return_points = list(zip(section_values[:-1], section_values[1:]))
    _scatter_svg(
        out / "poincare_return_map.svg",
        return_points,
        title=f"{args.system.title()} Poincaré return map",
        x_label=f"{AXES[section_coordinate]}[n]",
        y_label=f"{AXES[section_coordinate]}[n+1]",
    )
    _lyapunov_svg(out / "lyapunov_spectrum.svg", analysis.lyapunov_exponents, args.system)
    _html_explorer(out / "attractor_explorer.html", retained, args.system, analysis.parameters)

    bifurcation: list[tuple[float, float]] = []
    if args.bifurcation_points > 1:
        parameter, start, stop = _default_sweep(args.system)
        values = np.linspace(start, stop, args.bifurcation_points)
        bifurcation = parameter_sweep(
            system,
            analysis.parameters,
            parameter,
            values,
            initial,
            dt=args.dt,
            steps=args.bifurcation_steps,
            transient_steps=min(args.bifurcation_steps - 1, args.bifurcation_steps // 2),
        )
        _scatter_svg(
            out / "bifurcation.svg",
            bifurcation,
            title=f"{args.system.title()} finite bifurcation-style maxima sweep",
            x_label=parameter,
            y_label="local maxima of x",
            maximum=9000,
        )

    summary = analysis.summary()
    summary.update(
        {
            "run_id": utc_run_id(),
            "git": git_state(ROOT),
            "output_files": sorted(path.name for path in out.iterdir()),
            "bifurcation_points": len(bifurcation),
        }
    )
    summary["object_hash"] = object_hash(summary)
    (out / "pipeline.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_jsonl(out / "ledger.jsonl", [summary])
    (out / f"{args.system}_divergence.lean").write_text(analysis.lean4, encoding="utf-8")
    (out / f"{args.system}_divergence.v").write_text(analysis.coq, encoding="utf-8")

    exponents = ", ".join(f"{value:.6g}" for value in analysis.lyapunov_exponents)
    markdown = f"""# Attractor Forge — {args.system.title()}

A deterministic finite-time analysis of the configured `{args.system}` ODE.

- parameters: `{json.dumps(analysis.parameters, sort_keys=True)}`
- RK4: `dt={analysis.dt}`, `steps={analysis.steps}`, transient steps `{analysis.transient_steps}`
- Poincaré crossings: **{len(analysis.poincare)}**
- finite-time Lyapunov spectrum: **[{exponents}]**
- Kaplan–Yorke estimate: **{analysis.kaplan_yorke_dimension:.6g}**
- mean sampled divergence: **{analysis.divergence['mean']:.6g}**
- step-halving observed order: **{analysis.convergence['observed_order']:.5g}**
- correlation-dimension fit: **{analysis.recurrence.get('correlation_dimension', float('nan')):.5g}** (R² **{analysis.recurrence.get('fit_r2', float('nan')):.5g}**)
- formal statement: `{analysis.certificate_statement}`
- certificate hole-free: **{summary['certificate_hole_free']}**

![xy](projection_xy.svg)

![xz](projection_xz.svg)

![Poincare](poincare_return_map.svg)

![Lyapunov](lyapunov_spectrum.svg)

Open [`attractor_explorer.html`](attractor_explorer.html) for the self-contained rotating 3-D view.

**Claim boundary:** finite-time deterministic numerical diagnostics only.  The
Lyapunov, Kaplan–Yorke, recurrence, correlation-dimension, Poincaré, frequency,
and bifurcation outputs are numerical evidence, not formal proofs of chaos,
global attraction, a fractal invariant, or ergodicity.  The Lean/Coq certificate
proves only the displayed algebraic divergence bound.
"""
    if bifurcation:
        markdown += "\n![bifurcation](bifurcation.svg)\n"
    (out / "REPORT.md").write_text(markdown, encoding="utf-8")

    print("=" * 72)
    print(f"Attractor Forge — {args.system}")
    print("=" * 72)
    print(f"parameters                 : {analysis.parameters}")
    print(f"trajectory samples         : {len(analysis.trajectory)}")
    print(f"Poincare crossings         : {len(analysis.poincare)}")
    print(f"Lyapunov spectrum          : {exponents}")
    print(f"Kaplan-Yorke estimate      : {analysis.kaplan_yorke_dimension:.6g}")
    print(f"mean divergence            : {analysis.divergence['mean']:.6g}")
    print(f"step-halving order         : {analysis.convergence['observed_order']:.5g}")
    print(f"certificate hole-free      : {summary['certificate_hole_free']}")
    print(f"report                     : {out / 'REPORT.md'}")

    if not args.skip_audit:
        try:
            include = (out / "REPORT.md").resolve().relative_to(ROOT)
        except ValueError:
            include = None
        if include is not None:
            completed = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "claim_boundary_audit.py"), "--include", str(include), "--strict"],
                cwd=ROOT,
                check=False,
            )
            if completed.returncode:
                return completed.returncode

    basics_ok = (
        bool(summary["certificate_hole_free"])
        and np.all(np.isfinite(analysis.lyapunov_exponents))
        and all(record["residual_norm"] < 1e-8 for record in analysis.fixed_points)
    )
    return 0 if basics_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
