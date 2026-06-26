#!/usr/bin/env python3
"""Generate the self-contained GaugeGap Foundry Experience / Experiment interface.

The interface is an original, dependency-free audiovisual instrument built from
GaugeGap Foundry's own finite data.  It borrows one structural idea from Ryoji
Ikeda's *supersymmetry*: separate an immersive data *experience* from an exposed,
manipulable *experiment*.  It does not copy that artwork's images, software,
composition, or installation design.

Experience mode presents deterministic attractor trajectories, finite Z2 spectra,
and exact SU(3) weight geometry as synchronized high-contrast data fields.
Experiment mode exposes parameters, finite integration, exact-diagonalization
lookups, observables, methods, and claim boundaries.  Audio is generated locally
with the Web Audio API and is off until the visitor explicitly enables it.

CLAIM BOUNDARY: the output visualizes finite computations.  It is not evidence of
continuum Yang-Mills, a Millennium Prize solution, or a formal proof of chaos.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.flowgap_attractors import SYSTEMS, get_system, integrate  # noqa: E402
from gaugegap.models.z2_plaquette import (  # noqa: E402
    CLAIM_BOUNDARY as Z2_CLAIM_BOUNDARY,
    ground_state_observables,
    mass_gap,
    model_metadata,
)
from gaugegap.visualization.weight_diagrams import (  # noqa: E402
    su3_dimension,
    su3_weights,
    weight_centroid,
    weyl_orbit_closed,
)

SCHEMA = "gaugegap.foundry_experience.v1"
CLAIM_BOUNDARY = (
    "Finite computations and finite-time visual diagnostics only; no continuum "
    "Yang-Mills mass-gap claim, no Millennium Prize solution claim, and no formal "
    "proof of chaos or a global strange attractor."
)


def _rounded(value: float, digits: int = 8) -> float:
    return round(float(value), digits)


def _downsample_rows(values: np.ndarray, maximum: int) -> np.ndarray:
    if len(values) <= maximum:
        return values
    stride = max(1, int(np.ceil(len(values) / maximum)))
    return values[::stride][:maximum]


def build_attractor_dataset(
    name: str,
    *,
    steps: int,
    transient_steps: int,
    sample_every: int,
    maximum_points: int = 1800,
) -> dict[str, Any]:
    """Build a deterministic finite trajectory for one registered ODE system."""
    system = get_system(name)
    params = system.parameters()
    times, states = integrate(
        system,
        params,
        system.default_state,
        dt=0.01 if name != "thomas" else 0.02,
        steps=steps,
        sample_every=sample_every,
    )
    start = min(len(states) - 1, transient_steps // sample_every)
    retained = states[start:]
    retained_times = times[start:]
    combined = _downsample_rows(np.column_stack((retained_times, retained)), maximum_points)
    states_out = combined[:, 1:]
    divergences = [system.divergence(state, params) for state in states_out]
    extents = {
        axis: [_rounded(np.min(states_out[:, i])), _rounded(np.max(states_out[:, i]))]
        for i, axis in enumerate(("x", "y", "z"))
    }
    return {
        "kind": "attractor",
        "id": name,
        "label": name.title(),
        "description": system.description,
        "parameters": {key: _rounded(value) for key, value in params.items()},
        "default_state": [_rounded(value) for value in system.default_state],
        "dt": 0.01 if name != "thomas" else 0.02,
        "source_steps": int(steps),
        "transient_steps": int(transient_steps),
        "sample_every": int(sample_every),
        "points": [[_rounded(value) for value in row] for row in states_out],
        "time": [_rounded(value) for value in combined[:, 0]],
        "extents": extents,
        "mean_divergence": _rounded(np.mean(divergences)),
        "fraction_negative_divergence": _rounded(np.mean(np.asarray(divergences) < 0.0)),
        "equations": _equations(name),
        "method": "deterministic fixed-step classical RK4",
        "claim_boundary": (
            "Finite-time numerical ODE trajectory; visual structure and sensitivity "
            "are not a formal proof of chaos, ergodicity, or a global attractor."
        ),
    }


def _equations(name: str) -> list[str]:
    if name == "rossler":
        return ["dx/dt = -y - z", "dy/dt = x + a y", "dz/dt = b + z(x-c)"]
    if name == "lorenz":
        return [
            "dx/dt = sigma(y-x)",
            "dy/dt = x(rho-z)-y",
            "dz/dt = xy-beta z",
        ]
    if name == "thomas":
        return ["dx/dt = sin(y)-b x", "dy/dt = sin(z)-b y", "dz/dt = sin(x)-b z"]
    raise ValueError(name)


def build_z2_dataset(*, points: int) -> dict[str, Any]:
    """Precompute an exact one-plaquette grid for browser-side inspection."""
    if points < 3:
        raise ValueError("points must be at least 3")
    couplings = np.linspace(0.25, 2.0, points)
    fields = np.linspace(0.0, 1.5, points)
    records: list[dict[str, Any]] = []
    for coupling in couplings:
        for field in fields:
            gap, e0, e1 = mass_gap(1, float(coupling), float(field))
            observables = ground_state_observables(1, float(coupling), float(field))
            records.append(
                {
                    "j": _rounded(coupling, 6),
                    "h": _rounded(field, 6),
                    "gap": _rounded(gap),
                    "e0": _rounded(e0),
                    "e1": _rounded(e1),
                    "mean_plaquette_z": _rounded(observables["mean_plaquette_z"]),
                    "mean_link_x": _rounded(observables["mean_link_x"]),
                }
            )
    return {
        "kind": "spectrum",
        "id": "z2",
        "label": "Z2 finite plaquette",
        "model": model_metadata(1, 1.0, 0.2),
        "couplings": [_rounded(value, 6) for value in couplings],
        "fields": [_rounded(value, 6) for value in fields],
        "records": records,
        "equations": ["H = -J product_l Z_l - h sum_l X_l", "gap = E1 - E0"],
        "method": "exact dense diagonalization of a 4-qubit / 16-dimensional Hamiltonian",
        "claim_boundary": Z2_CLAIM_BOUNDARY,
    }


def build_su3_dataset() -> dict[str, Any]:
    representations = []
    for p, q, label in ((1, 1, "adjoint / octet"), (3, 0, "decuplet")):
        weights = su3_weights(p, q)
        representations.append(
            {
                "label": label,
                "p": p,
                "q": q,
                "dimension": su3_dimension(p, q),
                "weights": [
                    {
                        "t3": _rounded(weight["t3"]),
                        "y": _rounded(weight["y"]),
                        "mult": int(weight["mult"]),
                    }
                    for weight in weights
                ],
                "centroid": [_rounded(value) for value in weight_centroid(weights)],
                "weyl_closed": bool(weyl_orbit_closed(weights)),
            }
        )
    return {
        "kind": "geometry",
        "id": "su3",
        "label": "SU(3) representation geometry",
        "representations": representations,
        "method": "exact weight multiplicities from Freudenthal recursion",
        "claim_boundary": (
            "Exact finite representation geometry; this is not a completed SU(3) "
            "lattice-gauge Hamiltonian or a continuum gauge-theory result."
        ),
    }


def build_payload(*, smoke: bool = False) -> dict[str, Any]:
    steps = 2200 if smoke else 12000
    transient = 300 if smoke else 2500
    sample_every = 4 if smoke else 5
    z2_points = 5 if smoke else 13
    channels = [
        build_attractor_dataset(
            name,
            steps=steps,
            transient_steps=transient,
            sample_every=sample_every,
            maximum_points=500 if smoke else 1800,
        )
        for name in SYSTEMS
    ]
    channels.extend([build_z2_dataset(points=z2_points), build_su3_dataset()])
    return {
        "schema": SCHEMA,
        "title": "GaugeGap Foundry — Experience / Experiment",
        "modes": {
            "experience": "immersive synchronized views of finite verified data",
            "experiment": "manipulable finite models with methods and evidence exposed",
        },
        "channels": channels,
        "audio": {
            "default": "off",
            "source": "local Web Audio synthesis derived from the selected finite signal",
        },
        "claim_boundary": CLAIM_BOUNDARY,
        "provenance": {
            "generator": "scripts/generate_foundry_experience.py",
            "external_runtime_dependencies": [],
            "remote_assets": [],
        },
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_bundle(output_dir: Path, *, smoke: bool = False) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = build_payload(smoke=smoke)
    data_json = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    compact = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    data_path = output_dir / "experience-data.json"
    html_path = output_dir / "index.html"
    data_path.write_text(data_json, encoding="utf-8")
    html_path.write_text(_HTML.replace("__FOUNDRY_DATA__", compact), encoding="utf-8")
    manifest = {
        "schema": "gaugegap.foundry_experience_manifest.v1",
        "claim_boundary": CLAIM_BOUNDARY,
        "files": {
            "index.html": {"sha256": _sha256(html_path), "bytes": html_path.stat().st_size},
            "experience-data.json": {
                "sha256": _sha256(data_path),
                "bytes": data_path.stat().st_size,
            },
        },
        "deterministic": True,
        "self_contained": True,
        "audio_opt_in": True,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


_HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>GaugeGap Foundry — Experience / Experiment</title>
<style>
:root{--bg:#020202;--fg:#f7f7f2;--muted:#828282;--line:#282828;--hot:#ff3158;--cold:#58d7ff;--panel:#080808e8}
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;background:var(--bg);color:var(--fg);font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;overflow:hidden}
button,select,input{font:inherit}button{color:var(--fg);background:#050505;border:1px solid #3a3a3a;padding:.62rem .85rem;letter-spacing:.08em;text-transform:uppercase;cursor:pointer}button:hover,button.active{border-color:var(--fg);background:var(--fg);color:var(--bg)}
#app{height:100%;display:grid;grid-template-rows:54px 1fr 34px}.top{display:flex;align-items:center;gap:10px;padding:8px 12px;border-bottom:1px solid var(--line);z-index:5;background:#020202e8}.brand{font-weight:700;letter-spacing:.13em;margin-right:auto}.brand small{color:var(--muted);font-weight:400}.mode{min-width:118px}.sound{min-width:94px}.stage{position:relative;min-height:0}.view{position:absolute;inset:0;display:none}.view.active{display:block}
#experienceCanvas{width:100%;height:100%;display:block}.channel-rail{position:absolute;left:14px;top:14px;display:flex;flex-direction:column;gap:6px;z-index:3}.channel-rail button{font-size:11px;text-align:left;min-width:148px}.readout{position:absolute;right:14px;top:14px;width:min(330px,38vw);padding:13px;border:1px solid var(--line);background:var(--panel);backdrop-filter:blur(8px)}.readout h2{font-size:13px;letter-spacing:.12em;text-transform:uppercase;margin:0 0 12px}.metric{display:grid;grid-template-columns:1fr auto;border-top:1px solid #1b1b1b;padding:7px 0;font-size:11px}.metric span:first-child{color:var(--muted)}.ticker{position:absolute;left:0;right:0;bottom:0;height:28px;border-top:1px solid var(--line);background:#020202d8;white-space:nowrap;overflow:hidden;font-size:10px;letter-spacing:.1em;line-height:28px}.ticker span{display:inline-block;padding-left:100%;animation:scroll 24s linear infinite}@keyframes scroll{to{transform:translateX(-100%)}}
#experiment{display:grid;grid-template-columns:280px minmax(0,1fr) 330px;height:100%}.controls,.evidence{padding:14px;overflow:auto;background:#060606;border-color:var(--line);border-style:solid}.controls{border-width:0 1px 0 0}.evidence{border-width:0 0 0 1px}.controls h2,.evidence h2{font-size:12px;text-transform:uppercase;letter-spacing:.14em;margin:2px 0 14px}.field{margin:0 0 14px}.field label{display:flex;justify-content:space-between;font-size:11px;color:var(--muted);margin-bottom:6px}.field input[type=range]{width:100%;accent-color:var(--fg)}.field select{width:100%;background:#050505;color:var(--fg);border:1px solid #3a3a3a;padding:8px}.experiment-center{position:relative;min-width:0}#experimentCanvas{display:block;width:100%;height:100%}.experiment-metrics{position:absolute;left:12px;bottom:12px;display:grid;grid-template-columns:repeat(3,minmax(105px,1fr));gap:1px;background:var(--line);border:1px solid var(--line)}.experiment-metrics div{background:#050505;padding:9px 12px}.experiment-metrics b{display:block;font-size:16px}.experiment-metrics small{color:var(--muted);font-size:9px;text-transform:uppercase;letter-spacing:.1em}.evidence section{border-top:1px solid var(--line);padding:12px 0}.evidence h3{font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:0 0 8px}.evidence p,.evidence li{font-size:11px;line-height:1.55}.evidence ul{padding-left:16px}.status{display:inline-block;padding:3px 6px;border:1px solid #444;font-size:9px;text-transform:uppercase}.status.finite{border-color:var(--cold);color:var(--cold)}.status.exact{border-color:#fff;color:#fff}.status.boundary{border-color:var(--hot);color:var(--hot)}
.footer{display:flex;align-items:center;padding:0 12px;border-top:1px solid var(--line);font-size:9px;color:var(--muted);letter-spacing:.04em;white-space:nowrap;overflow:hidden}.footer strong{color:var(--hot);margin-right:6px}.help{margin-left:auto;color:#aaa}
@media(max-width:900px){#experiment{grid-template-columns:220px 1fr}.evidence{display:none}.readout{width:48vw}.channel-rail button{min-width:112px}.brand small{display:none}}
@media(max-width:640px){.brand{font-size:11px}.mode{min-width:auto}.top button{padding:.55rem}.channel-rail{left:7px;top:7px}.channel-rail button{min-width:92px;padding:.45rem;font-size:9px}.readout{right:7px;top:7px;width:55vw;padding:8px}.readout .metric:nth-of-type(n+5){display:none}#experiment{grid-template-columns:1fr}.controls{position:absolute;left:0;top:0;z-index:4;width:210px;max-height:100%;background:#050505ef}.experiment-metrics{left:220px;right:8px;grid-template-columns:1fr}.experiment-metrics div:nth-child(n+2){display:none}.help{display:none}}
</style>
</head>
<body>
<div id="app">
<header class="top">
  <div class="brand">GAUGEGAP FOUNDRY <small>/ finite data instrument</small></div>
  <button class="mode active" data-mode="experience">experience</button>
  <button class="mode" data-mode="experiment">experiment</button>
  <button class="sound" id="sound">sound off</button>
</header>
<main class="stage">
<section class="view active" id="experience">
  <canvas id="experienceCanvas"></canvas>
  <nav class="channel-rail" id="channelRail"></nav>
  <aside class="readout" id="readout"></aside>
  <div class="ticker"><span id="tickerText"></span></div>
</section>
<section class="view" id="experiment">
  <aside class="controls">
    <h2>finite model controls</h2>
    <div class="field"><label for="model">model</label><select id="model"></select></div>
    <div id="parameterFields"></div>
    <button id="reset">reset model</button>
  </aside>
  <div class="experiment-center">
    <canvas id="experimentCanvas"></canvas>
    <div class="experiment-metrics" id="experimentMetrics"></div>
  </div>
  <aside class="evidence" id="evidence"></aside>
</section>
</main>
<footer class="footer"><strong>BOUNDARY</strong><span id="boundary"></span><span class="help">E experience · X experiment · space pause · M sound</span></footer>
</div>
<script>
'use strict';
const DATA=__FOUNDRY_DATA__;
const channels=DATA.channels;
const byId=Object.fromEntries(channels.map(x=>[x.id,x]));
const state={mode:'experience',channel:'rossler',paused:false,sound:false,audio:null,osc:null,gain:null,phase:0,model:'rossler',trajectory:null,params:{}};
const $=id=>document.getElementById(id);
$('boundary').textContent=DATA.claim_boundary;

function fitCanvas(canvas){const r=canvas.getBoundingClientRect(),d=Math.min(devicePixelRatio||1,2);const w=Math.max(1,Math.floor(r.width*d)),h=Math.max(1,Math.floor(r.height*d));if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}return {w,h,d};}
function clamp(v,a,b){return Math.max(a,Math.min(b,v));}
function norm(v,a,b){return b===a?.5:(v-a)/(b-a);}
function finite(v){return Number.isFinite(v)?v:0;}
function fmt(v,d=5){return Number.isFinite(v)?Number(v).toFixed(d):'—';}

function setMode(mode){state.mode=mode;document.querySelectorAll('.mode').forEach(b=>b.classList.toggle('active',b.dataset.mode===mode));document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v.id===mode));if(mode==='experiment')setupExperiment();}
document.querySelectorAll('.mode').forEach(b=>b.onclick=()=>setMode(b.dataset.mode));

function buildRail(){const rail=$('channelRail');channels.forEach(ch=>{const b=document.createElement('button');b.textContent=ch.label;b.dataset.id=ch.id;b.classList.toggle('active',ch.id===state.channel);b.onclick=()=>{state.channel=ch.id;[...rail.children].forEach(x=>x.classList.toggle('active',x.dataset.id===ch.id));updateReadout();};rail.appendChild(b);});}
function updateReadout(){const ch=byId[state.channel];let metrics=[];if(ch.kind==='attractor'){metrics=[['method',ch.method],['samples',ch.points.length],['mean divergence',fmt(ch.mean_divergence)],['negative divergence',fmt(100*ch.fraction_negative_divergence,1)+'%'],['dt',ch.dt]];}else if(ch.kind==='spectrum'){const r=ch.records[Math.floor(ch.records.length/2)];metrics=[['method','exact diagonalization'],['Hilbert dimension',ch.model.n_qubits+' qubits / '+(2**ch.model.n_qubits)],['grid points',ch.records.length],['sample gap',fmt(r.gap)],['observable','E1 - E0']];}else{metrics=[['method','Freudenthal recursion'],['representations',ch.representations.length],['octet dimension',ch.representations[0].dimension],['Weyl closed',String(ch.representations.every(r=>r.weyl_closed))],['centroid','origin']];}
$('readout').innerHTML='<h2>'+ch.label+'</h2>'+metrics.map(m=>'<div class="metric"><span>'+m[0]+'</span><span>'+m[1]+'</span></div>').join('')+'<div class="metric"><span>status</span><span class="status '+(ch.kind==='spectrum'||ch.kind==='geometry'?'exact':'finite')+'">'+(ch.kind==='spectrum'||ch.kind==='geometry'?'exact finite':'finite numerical')+'</span></div>';
$('tickerText').textContent=ch.claim_boundary+'  //  '+(ch.equations?ch.equations.join('  ·  '):'exact finite representation geometry')+'  //  data generated locally by GaugeGap Foundry';}

function drawExperience(){const c=$('experienceCanvas'),ctx=c.getContext('2d'),{w,h,d}=fitCanvas(c);ctx.setTransform(1,0,0,1,0,0);ctx.fillStyle='#020202';ctx.fillRect(0,0,w,h);const ch=byId[state.channel];const t=state.phase;if(ch.kind==='attractor')drawAttractorExperience(ctx,w,h,ch,t,d);else if(ch.kind==='spectrum')drawSpectrumExperience(ctx,w,h,ch,t,d);else drawGeometryExperience(ctx,w,h,ch,t,d);drawGrid(ctx,w,h,d);}
function drawGrid(ctx,w,h,d){ctx.strokeStyle='rgba(255,255,255,.045)';ctx.lineWidth=d;const step=48*d;ctx.beginPath();for(let x=0;x<w;x+=step){ctx.moveTo(x,0);ctx.lineTo(x,h)}for(let y=0;y<h;y+=step){ctx.moveTo(0,y);ctx.lineTo(w,y)}ctx.stroke();}
function projectPoint(p,w,h,rot,scale=.31){const cy=Math.cos(rot),sy=Math.sin(rot),cp=Math.cos(.45),sp=Math.sin(.45);let x=p[0]*cy-p[2]*sy,z=p[0]*sy+p[2]*cy,y=p[1];let yy=y*cp-z*sp;return [w*.5+x*scale*Math.min(w,h),h*.5-yy*scale*Math.min(w,h)];}
function drawAttractorExperience(ctx,w,h,ch,t,d){const ex=ch.extents;const sx=Math.max(Math.abs(ex.x[0]),Math.abs(ex.x[1]))||1,sy=Math.max(Math.abs(ex.y[0]),Math.abs(ex.y[1]))||1,sz=Math.max(Math.abs(ex.z[0]),Math.abs(ex.z[1]))||1;const pts=ch.points.map(p=>[p[0]/sx,p[1]/sy,p[2]/sz]);ctx.strokeStyle='rgba(255,255,255,.82)';ctx.lineWidth=.7*d;ctx.beginPath();pts.forEach((p,i)=>{const q=projectPoint(p,w,h,t*.07);i?ctx.lineTo(q[0],q[1]):ctx.moveTo(q[0],q[1]);});ctx.stroke();
const bands=12;for(let side of [-1,1])for(let band=0;band<bands;band++){const depth=band/(bands-1),baseX=w*.5+side*(w*.12+depth*w*.37),halfH=h*(.08+depth*.34),idx=Math.floor((t*6+band*137)%pts.length);ctx.strokeStyle=band%4===0?'rgba(255,49,88,.75)':'rgba(255,255,255,'+(.15+.45*depth)+')';ctx.lineWidth=(.5+depth)*d;ctx.beginPath();for(let k=0;k<50;k++){const p=pts[(idx+k*3)%pts.length],yy=h*.5+(p[(band+1)%3]) * halfH*.55;const xx=baseX+side*(k/49)*w*.045*(.3+depth);k?ctx.lineTo(xx,yy):ctx.moveTo(xx,yy);}ctx.stroke();}}
function drawSpectrumExperience(ctx,w,h,ch,t,d){const n=ch.couplings.length,m=ch.fields.length;const cellW=w/(n+6),cellH=h/(m+5);ch.records.forEach((r,i)=>{const ix=Math.floor(i/m),iy=i%m;const intensity=clamp(r.gap/3,0,1);const pulse=.72+.28*Math.sin(t*.8+i*.19);ctx.fillStyle='rgba(255,255,255,'+(intensity*pulse*.85)+')';ctx.fillRect((ix+3)*cellW,(iy+2)*cellH,Math.max(1,cellW*.72),Math.max(1,cellH*.5));if(r.mean_plaquette_z<0){ctx.fillStyle='rgba(255,49,88,.65)';ctx.fillRect((ix+3)*cellW,(iy+2)*cellH,Math.max(1,cellW*.12),Math.max(1,cellH*.5));}});ctx.strokeStyle='rgba(88,215,255,.7)';ctx.lineWidth=d;ctx.beginPath();for(let x=0;x<w;x+=3*d){const y=h*.5+Math.sin(x*.025/d+t)*h*.08+Math.sin(x*.007/d-t*.4)*h*.04;x?ctx.lineTo(x,y):ctx.moveTo(x,y);}ctx.stroke();}
function drawGeometryExperience(ctx,w,h,ch,t,d){const reps=ch.representations;reps.forEach((rep,ri)=>{const cx=w*(ri?.68:.32),cy=h*.5,scale=Math.min(w,h)*.22;ctx.strokeStyle='rgba(255,255,255,.15)';ctx.beginPath();rep.weights.forEach((p,i)=>{const angle=t*.04*(ri?1:-1),x=p.t3*Math.cos(angle)-p.y*Math.sin(angle),y=p.t3*Math.sin(angle)+p.y*Math.cos(angle);const xx=cx+x*scale,yy=cy-y*scale;i?ctx.lineTo(xx,yy):ctx.moveTo(xx,yy);});ctx.closePath();ctx.stroke();rep.weights.forEach((p,i)=>{const angle=t*.04*(ri?1:-1),x=p.t3*Math.cos(angle)-p.y*Math.sin(angle),y=p.t3*Math.sin(angle)+p.y*Math.cos(angle);ctx.fillStyle=i%3===0?'#ff3158':'#f7f7f2';ctx.beginPath();ctx.arc(cx+x*scale,cy-y*scale,(2.5+2*p.mult)*d,0,Math.PI*2);ctx.fill();});ctx.fillStyle='#888';ctx.font=11*d+'px monospace';ctx.fillText(rep.label,cx-scale,cy+scale+28*d);});}

const modelDefaults={
 rossler:{a:.2,b:.2,c:5.7,dt:.01},lorenz:{sigma:10,rho:28,beta:2.666667,dt:.008},thomas:{b:.208186,dt:.02},z2:{j:1,h:.25}
};
const ranges={a:[.05,.5,.01],b:[.05,.5,.01],c:[2,12,.1],sigma:[1,20,.5],rho:[1,50,.5],beta:[.5,5,.1],dt:[.002,.03,.001],j:[.25,2,.145833],h:[0,1.5,.125]};
function setupExperiment(){const model=$('model');if(!model.children.length){channels.filter(c=>['attractor','spectrum'].includes(c.kind)).forEach(ch=>{const o=document.createElement('option');o.value=ch.id;o.textContent=ch.label;model.appendChild(o)});model.onchange=()=>{state.model=model.value;resetExperiment();};$('reset').onclick=resetExperiment;}model.value=state.model;if(!Object.keys(state.params).length)resetExperiment();else renderControls();}
function resetExperiment(){state.params={...modelDefaults[state.model]};renderControls();recomputeExperiment();}
function renderControls(){const holder=$('parameterFields');holder.innerHTML='';Object.entries(state.params).forEach(([key,value])=>{const [min,max,step]=ranges[key];const wrap=document.createElement('div');wrap.className='field';wrap.innerHTML='<label><span>'+key+'</span><output id="out_'+key+'">'+fmt(value,4)+'</output></label><input type="range" min="'+min+'" max="'+max+'" step="'+step+'" value="'+value+'" data-key="'+key+'">';const input=wrap.querySelector('input');input.oninput=()=>{state.params[key]=+input.value;$('out_'+key).textContent=fmt(state.params[key],4);recomputeExperiment();};holder.appendChild(wrap);});}
function deriv(model,p,s){const [x,y,z]=s;if(model==='rossler')return[-y-z,x+p.a*y,p.b+z*(x-p.c)];if(model==='lorenz')return[p.sigma*(y-x),x*(p.rho-z)-y,x*y-p.beta*z];return[Math.sin(y)-p.b*x,Math.sin(z)-p.b*y,Math.sin(x)-p.b*z];}
function rk4js(model,p,s,dt){const add=(a,b,k)=>a.map((v,i)=>v+k*b[i]);const k1=deriv(model,p,s),k2=deriv(model,p,add(s,k1,dt/2)),k3=deriv(model,p,add(s,k2,dt/2)),k4=deriv(model,p,add(s,k3,dt));return s.map((v,i)=>v+dt*(k1[i]+2*k2[i]+2*k3[i]+k4[i])/6);}
function computeTrajectory(){const p=state.params,model=state.model;let s=model==='lorenz'?[1,1,1]:model==='thomas'?[.1,0,0]:[0,1,0],out=[];for(let i=0;i<6200;i++){s=rk4js(model,p,s,p.dt);if(i>1200&&i%3===0&&s.every(Number.isFinite))out.push(s.slice());if(!s.every(Number.isFinite)||s.some(v=>Math.abs(v)>1e7))break;}return out;}
function nearestZ2(){const ch=byId.z2;let best=null,dist=Infinity;for(const r of ch.records){const d=Math.abs(r.j-state.params.j)+Math.abs(r.h-state.params.h);if(d<dist){dist=d;best=r}}return best;}
function recomputeExperiment(){if(state.model==='z2')state.trajectory=null;else state.trajectory=computeTrajectory();updateEvidence();drawExperiment();}
function updateEvidence(){const ch=byId[state.model];let metrics,detail;if(ch.kind==='spectrum'){const r=nearestZ2();metrics=[['gap',r.gap],['E0',r.e0],['E1',r.e1]];detail='<section><h3>exact lookup</h3><p>Controls snap to a precomputed grid generated by the repository\'s 16×16 exact Hamiltonian diagonalization.</p></section><section><h3>observables</h3><p>mean plaquette Z = '+fmt(r.mean_plaquette_z)+'<br>mean link X = '+fmt(r.mean_link_x)+'</p></section>';}else{const pts=state.trajectory||[];const amp=pts.length?Math.max(...pts.slice(-300).map(p=>Math.hypot(...p))):NaN;metrics=[['samples',pts.length],['state norm',amp],['dt',state.params.dt]];detail='<section><h3>live browser integration</h3><p>Fixed-step RK4 recomputes a finite trajectory locally after every parameter change.</p></section><section><h3>equations</h3><ul>'+ch.equations.map(e=>'<li>'+e+'</li>').join('')+'</ul></section>';}
$('experimentMetrics').innerHTML=metrics.map(m=>'<div><b>'+fmt(+m[1],typeof m[1]==='number'&&Math.abs(m[1])<100?5:0)+'</b><small>'+m[0]+'</small></div>').join('');$('evidence').innerHTML='<h2>evidence chain</h2><section><span class="status '+(ch.kind==='spectrum'?'exact':'finite')+'">'+(ch.kind==='spectrum'?'exact finite':'finite numerical')+'</span></section>'+detail+'<section><h3>method</h3><p>'+ch.method+'</p></section><section><h3>claim boundary</h3><p class="status boundary">'+ch.claim_boundary+'</p></section>';}
function drawExperiment(){const c=$('experimentCanvas'),ctx=c.getContext('2d'),{w,h,d}=fitCanvas(c);ctx.fillStyle='#020202';ctx.fillRect(0,0,w,h);drawGrid(ctx,w,h,d);if(state.model==='z2'){const ch=byId.z2,r=nearestZ2(),maxGap=Math.max(...ch.records.map(x=>x.gap));const rows=ch.fields.length,cols=ch.couplings.length,cw=w/cols,chh=h/rows;ch.records.forEach((q,i)=>{const x=Math.floor(i/rows)*cw,y=(i%rows)*chh;ctx.fillStyle='rgba(255,255,255,'+clamp(q.gap/maxGap,0.03,.95)+')';ctx.fillRect(x+1,y+1,cw-2,chh-2);if(q===r){ctx.strokeStyle='#ff3158';ctx.lineWidth=3*d;ctx.strokeRect(x+2,y+2,cw-4,chh-4);}});}else{const pts=state.trajectory||[];if(!pts.length)return;const max=[0,0,0];pts.forEach(p=>p.forEach((v,i)=>max[i]=Math.max(max[i],Math.abs(v))));ctx.strokeStyle='#f7f7f2';ctx.lineWidth=.8*d;ctx.beginPath();pts.forEach((p,i)=>{const q=projectPoint([p[0]/(max[0]||1),p[1]/(max[1]||1),p[2]/(max[2]||1)],w,h,state.phase*.02,.38);i?ctx.lineTo(q[0],q[1]):ctx.moveTo(q[0],q[1]);});ctx.stroke();}}

async function toggleSound(){state.sound=!state.sound;$('sound').textContent=state.sound?'sound on':'sound off';$('sound').classList.toggle('active',state.sound);if(state.sound){if(!state.audio){state.audio=new (window.AudioContext||window.webkitAudioContext)();state.osc=state.audio.createOscillator();state.gain=state.audio.createGain();state.osc.type='sine';state.gain.gain.value=.018;state.osc.connect(state.gain).connect(state.audio.destination);state.osc.start();}await state.audio.resume();}else if(state.audio){state.gain.gain.setTargetAtTime(0,state.audio.currentTime,.03);setTimeout(()=>{if(state.sound)state.gain.gain.setTargetAtTime(.018,state.audio.currentTime,.03)},80);}}
$('sound').onclick=toggleSound;
function updateSound(){if(!state.sound||!state.osc)return;const ch=byId[state.mode==='experience'?state.channel:state.model];let v=.5;if(ch.kind==='attractor'){const pts=state.mode==='experiment'?(state.trajectory||[]):ch.points;if(pts.length){const p=pts[Math.floor(state.phase*7)%pts.length];v=.5+.5*Math.tanh((p[0]+p[1])*.15);}}else if(ch.kind==='spectrum'){const r=state.mode==='experiment'?nearestZ2():ch.records[Math.floor(state.phase*3)%ch.records.length];v=clamp(r.gap/4,0,1);}else v=.4+.3*Math.sin(state.phase*.2);state.osc.frequency.setTargetAtTime(90+v*760,state.audio.currentTime,.05);state.gain.gain.setTargetAtTime(.008+v*.018,state.audio.currentTime,.08);}

let last=performance.now();function frame(now){const dt=Math.min(.05,(now-last)/1000);last=now;if(!state.paused)state.phase+=dt;drawExperience();if(state.mode==='experiment')drawExperiment();updateSound();requestAnimationFrame(frame);}window.addEventListener('resize',()=>{drawExperience();drawExperiment()});window.addEventListener('keydown',e=>{if(e.key==='e'||e.key==='E')setMode('experience');if(e.key==='x'||e.key==='X')setMode('experiment');if(e.key===' '){e.preventDefault();state.paused=!state.paused}if(e.key==='m'||e.key==='M')toggleSound();});
buildRail();updateReadout();setupExperiment();requestAnimationFrame(frame);
</script>
</body></html>
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "site" / "foundry-experience",
    )
    parser.add_argument("--smoke", action="store_true", help="Generate a smaller CI bundle")
    args = parser.parse_args()
    manifest = write_bundle(args.output_dir, smoke=args.smoke)
    print(
        json.dumps(
            {
                "status": "pass",
                "output_dir": str(args.output_dir),
                "files": sorted(manifest["files"]),
                "self_contained": manifest["self_contained"],
                "audio_opt_in": manifest["audio_opt_in"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
