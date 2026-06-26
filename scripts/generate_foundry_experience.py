#!/usr/bin/env python3
"""Generate the self-contained GaugeGap Foundry Experience.

The interface has two deliberately separate modes:

* EXPERIENCE — an immersive audiovisual traversal of finite scientific data.
* EXPERIMENT — direct control over equations, parameters, projections, and the
  evidence/claim boundary attached to every rendered scene.

The design is inspired by the conceptual split between Ryoji Ikeda's
``supersymmetry [experience]`` and ``supersymmetry [experiment]``.  No artwork,
photography, audio, or source code from that installation is copied.

All generated scientific data remain finite numerical artifacts.  The page does
not claim a continuum theorem, global strange attractor, or Millennium solution.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.flowgap_attractors import (  # noqa: E402
    get_system,
    integrate,
    lyapunov_spectrum,
    poincare_section,
)
from gaugegap.hamiltonian_factory import build_and_audit  # noqa: E402
from gaugegap.koopman import dominant_modes, exact_dmd  # noqa: E402
from gaugegap.research_manifest import (  # noqa: E402
    ClaimLevel,
    EvidenceArtifact,
    ResearchClaim,
    write_manifest,
)
from gaugegap.validated_dynamics import (  # noqa: E402
    IntervalBox,
    picard_enclosure_step,
)
from gaugegap.visualization.lattice_projection import cubic_lattice, wilson_loop  # noqa: E402
from gaugegap.visualization.weight_diagrams import su3_weights  # noqa: E402


CLAIM_BOUNDARY = (
    "finite deterministic visualizations and browser-side numerical experiments only; "
    "no continuum theorem, formal chaos proof, or Millennium Prize solution claim"
)


def _round_rows(values: np.ndarray, digits: int = 7) -> list[list[float]]:
    return [[round(float(value), digits) for value in row] for row in values]


def _downsample(values: np.ndarray, maximum: int) -> np.ndarray:
    if len(values) <= maximum:
        return values
    indices = np.linspace(0, len(values) - 1, maximum, dtype=int)
    return values[indices]


def _git_commit() -> str | None:
    completed = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    return completed.stdout.strip() or None if completed.returncode == 0 else None


def _attractor_dataset(name: str) -> dict[str, Any]:
    system = get_system(name)
    params = system.parameters()
    dt = 0.01 if name != "thomas" else 0.02
    steps = 12000 if name != "thomas" else 18000
    transient = 2500 if name != "thomas" else 4000
    _, states = integrate(system, params, system.default_state, dt=dt, steps=steps)
    retained = states[transient:]
    display = _downsample(retained, 2200)
    dmd = exact_dmd(retained[::4], dt=dt * 4, rank=3)
    exponents = lyapunov_spectrum(
        system,
        params,
        system.default_state,
        dt=dt,
        steps=min(9000, steps),
        transient_steps=min(2000, transient),
        renormalize_every=10,
    )
    section = poincare_section(retained, axis=0, level=0.0, direction=1)
    enclosure = picard_enclosure_step(
        name,
        IntervalBox.from_point(system.default_state, radius=1e-15),
        params,
        dt=min(dt, 0.005),
    )
    formulas = {
        "rossler": ["x' = -y-z", "y' = x+a y", "z' = b+z(x-c)"],
        "lorenz": ["x' = σ(y-x)", "y' = x(ρ-z)-y", "z' = xy-βz"],
        "thomas": ["x' = sin(y)-b x", "y' = sin(z)-b y", "z' = sin(x)-b z"],
    }
    return {
        "kind": "attractor",
        "id": name,
        "label": name.title(),
        "description": system.description,
        "equations": formulas[name],
        "parameters": params,
        "defaults": list(system.default_state),
        "dt": dt,
        "points": _round_rows(display),
        "diagnostics": {
            "lyapunov": [round(float(value), 8) for value in exponents],
            "poincare_crossings": int(len(section)),
            "dmd": dmd.summary(),
            "dominant_modes": dominant_modes(dmd, count=3),
            "validated_step": enclosure.summary(),
        },
        "claim_boundary": (
            "finite-time ODE integration, finite-time Lyapunov and DMD evidence only; "
            "the interval item certifies one configured finite step"
        ),
    }


def _lattice_dataset() -> dict[str, Any]:
    lattice = cubic_lattice(4, 4, 4)
    loop = wilson_loop(lattice, (0, 0, 1), R=2, T=2, plane="xy")
    highlighted = {tuple(sorted((loop[index], loop[index + 1]))) for index in range(len(loop) - 1)}
    points = lattice.sites - lattice.sites.mean(axis=0)
    edges = [
        [int(left), int(right), int(tuple(sorted((left, right))) in highlighted)]
        for left, right in lattice.links
    ]
    return {
        "kind": "geometry",
        "id": "lattice",
        "label": "Gauge lattice",
        "description": "Finite cubic lattice with a highlighted Wilson-loop path",
        "points": _round_rows(points),
        "edges": edges,
        "claim_boundary": "finite lattice geometry and path visualization only",
    }


def _weights_dataset() -> dict[str, Any]:
    octet = su3_weights(1, 1)
    decuplet = su3_weights(3, 0)

    def rows(values: list[dict[str, Any]]) -> list[list[float]]:
        output: list[list[float]] = []
        for value in values:
            x, y, z = value["r3"]
            output.append([
                round(float(x), 7),
                round(float(y), 7),
                round(float(z), 7),
                int(value["mult"]),
            ])
        return output

    return {
        "kind": "geometry",
        "id": "su3",
        "label": "SU(3) weights",
        "description": "Exact finite representation-weight coordinates",
        "octet": rows(octet),
        "decuplet": rows(decuplet),
        "claim_boundary": "representation-theory geometry; not evidence for a continuum mass gap",
    }


def _spectra_dataset() -> dict[str, Any]:
    z2_artifact, z2_audit = build_and_audit(
        "z2-plaquette", n_plaquettes=1, plaquette_coupling=1.0, transverse_field=0.35
    )
    u1_artifact, u1_audit = build_and_audit(
        "u1-plaquette", n_links=2, g_electric=1.0, g_magnetic=0.5, truncation=1
    )
    return {
        "kind": "spectra",
        "id": "spectra",
        "label": "Finite spectra",
        "description": "Canonical factory spectra for finite Z2 and truncated U(1) models",
        "models": [
            {
                "id": z2_artifact.model_id,
                "eigenvalues": [round(float(value), 8) for value in np.linalg.eigvalsh(z2_artifact.matrix)],
                "audit": z2_audit.summary(),
            },
            {
                "id": u1_artifact.model_id,
                "eigenvalues": [round(float(value), 8) for value in np.linalg.eigvalsh(u1_artifact.matrix)],
                "audit": u1_audit.summary(),
            },
        ],
        "claim_boundary": "finite matrix spectra only; no continuum spectral-gap theorem",
    }


def _physical_limits_dataset() -> dict[str, Any]:
    log_mass = np.linspace(-6.0, 6.0, 360)
    mass = 10.0**log_mass
    schwarzschild = 2.0 * mass
    compton = 1.0 / mass
    return {
        "kind": "limits",
        "id": "limits",
        "label": "Mass-radius limits",
        "description": "Dimensionless Planck-unit Compton and Schwarzschild scaling curves",
        "log_mass": [round(float(value), 7) for value in log_mass],
        "log_schwarzschild": [round(float(value), 7) for value in np.log10(schwarzschild)],
        "log_compton": [round(float(value), 7) for value in np.log10(compton)],
        "claim_boundary": "dimensionless scaling visualization of established formulas",
    }


def build_dataset() -> dict[str, Any]:
    scenes = [
        _attractor_dataset("rossler"),
        _attractor_dataset("lorenz"),
        _attractor_dataset("thomas"),
        _lattice_dataset(),
        _weights_dataset(),
        _spectra_dataset(),
        _physical_limits_dataset(),
    ]
    return {
        "schema": "gaugegap.foundry_experience.v1",
        "title": "GaugeGap Foundry Experience",
        "git_commit": _git_commit(),
        "claim_boundary": CLAIM_BOUNDARY,
        "scenes": scenes,
    }


_HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>GaugeGap Foundry — Experience / Experiment</title>
<style>
:root{--bg:#030303;--fg:#f4f4f4;--muted:#777;--line:#242424;--hot:#ff2a2a;--cold:#a7d8ff}
*{box-sizing:border-box}html,body{width:100%;height:100%;margin:0;background:var(--bg);color:var(--fg);font:12px/1.35 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;overflow:hidden}
button,select,input{font:inherit;color:inherit;background:#080808;border:1px solid #333}
button{cursor:pointer;padding:8px 12px;letter-spacing:.12em;text-transform:uppercase}
button:hover,button.active{background:#fff;color:#000;border-color:#fff}
#stage{position:fixed;inset:0}canvas{position:absolute;inset:0;width:100%;height:100%}
#scan{pointer-events:none;position:absolute;inset:0;background:repeating-linear-gradient(0deg,transparent 0 3px,rgba(255,255,255,.025) 3px 4px);mix-blend-mode:screen}
#header{position:fixed;left:0;right:0;top:0;height:62px;border-bottom:1px solid var(--line);display:flex;align-items:center;padding:0 18px;z-index:5;background:linear-gradient(#030303f2,#030303c9)}
#brand{font-size:14px;letter-spacing:.26em;font-weight:700;white-space:nowrap}#mode{display:flex;gap:8px;margin-left:28px}
#status{margin-left:auto;color:var(--muted);text-align:right}.hot{color:var(--hot)}
#left{position:fixed;left:0;top:62px;bottom:0;width:286px;border-right:1px solid var(--line);padding:18px;z-index:4;background:#030303e8;overflow:auto;transition:transform .3s}
#right{position:fixed;right:0;top:62px;bottom:0;width:352px;border-left:1px solid var(--line);padding:18px;z-index:4;background:#030303e8;overflow:auto;transition:transform .3s}
.experience #left,.experience #right{transform:translateX(-105%)}.experience #right{transform:translateX(105%)}
.section{border-top:1px solid #252525;padding-top:12px;margin-top:16px}.section:first-child{border-top:0;margin-top:0;padding-top:0}
.label{color:#888;text-transform:uppercase;letter-spacing:.18em;font-size:10px;margin-bottom:7px}.value{font-size:13px;word-break:break-word}
select,input[type=range]{width:100%}select{padding:8px}input[type=range]{accent-color:#fff}
.param{margin:12px 0}.paramTop{display:flex;justify-content:space-between}.tiny{font-size:10px;color:#777}.monoBox{white-space:pre-wrap;border:1px solid #222;background:#060606;padding:10px;margin-top:7px}
.metric{display:grid;grid-template-columns:1fr auto;gap:8px;border-bottom:1px dotted #292929;padding:5px 0}.metric span:last-child{color:#fff}.warn{color:#ff8c8c}
#sceneTitle{position:fixed;left:50%;top:82px;transform:translateX(-50%);z-index:3;text-align:center;letter-spacing:.18em;text-transform:uppercase;font-size:13px}
#sceneSub{display:block;color:#777;font-size:10px;letter-spacing:.08em;margin-top:5px;text-transform:none}
#ticker{position:fixed;left:18px;right:18px;bottom:13px;z-index:3;color:#777;white-space:nowrap;overflow:hidden;border-top:1px solid #191919;padding-top:8px}
#tickerInner{display:inline-block;animation:ticker 28s linear infinite}@keyframes ticker{from{transform:translateX(100vw)}to{transform:translateX(-100%)}}
#bigIndex{position:fixed;left:22px;bottom:38px;font-size:80px;color:#ffffff0b;z-index:1;font-weight:800}
#sound{margin-left:8px}#run{width:100%;margin-top:12px}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:8px}
#evidence pre{font-size:10px;white-space:pre-wrap;color:#aaa}.pill{display:inline-block;border:1px solid #333;padding:3px 6px;margin:2px;color:#aaa}
@media(max-width:900px){#right{width:310px}#left{width:250px}.experiment #right{display:none}}
</style></head>
<body class="experience">
<div id="stage"><canvas id="c"></canvas><div id="scan"></div></div>
<header id="header"><div id="brand">GAUGEGAP // FOUNDRY</div><div id="mode"><button id="experience" class="active">Experience</button><button id="experiment">Experiment</button></div><button id="sound">Sound: off</button><div id="status"><span id="clock"></span><br><span class="hot">FINITE CLAIM MODE</span></div></header>
<div id="sceneTitle"></div><div id="bigIndex">00</div>
<aside id="left">
  <div class="section"><div class="label">Scene</div><select id="scene"></select></div>
  <div class="section"><div class="label">Projection</div><select id="projection"><option value="xy">x / y</option><option value="xz">x / z</option><option value="yz">y / z</option><option value="3d">rotating 3-D</option></select></div>
  <div class="section"><div class="label">Equation controls</div><div id="params"></div><button id="run">Re-integrate finite model</button></div>
  <div class="section"><div class="label">Display</div>
    <div class="param"><div class="paramTop"><span>density</span><span id="densityV"></span></div><input id="density" type="range" min="100" max="5000" value="2200"></div>
    <div class="param"><div class="paramTop"><span>speed</span><span id="speedV"></span></div><input id="speed" type="range" min="1" max="20" value="6"></div>
    <div class="param"><div class="paramTop"><span>persistence</span><span id="trailV"></span></div><input id="trail" type="range" min="1" max="100" value="83"></div>
  </div>
  <div class="section"><div class="label">Layer</div><div class="grid2"><button id="points">Points</button><button id="lines" class="active">Lines</button></div></div>
</aside>
<aside id="right">
  <div class="section"><div class="label">Equations</div><div id="equations" class="monoBox"></div></div>
  <div class="section"><div class="label">Live diagnostics</div><div id="metrics"></div></div>
  <div class="section"><div class="label">Evidence manifest</div><div id="evidence"></div></div>
  <div class="section"><div class="label">Claim boundary</div><div id="boundary" class="warn"></div></div>
</aside>
<div id="ticker"><div id="tickerInner"></div></div>
<script>
const DATA=__DATA__;
const canvas=document.getElementById('c'),ctx=canvas.getContext('2d');
const sceneSel=document.getElementById('scene'),projection=document.getElementById('projection');
const body=document.body,paramsEl=document.getElementById('params'),metricsEl=document.getElementById('metrics');
const evidenceEl=document.getElementById('evidence'),boundaryEl=document.getElementById('boundary'),equationsEl=document.getElementById('equations');
const density=document.getElementById('density'),speed=document.getElementById('speed'),trail=document.getElementById('trail');
let mode='experience',sceneIndex=0,points=[],frame=0,yaw=.5,pitch=.35,lastSwitch=performance.now(),drawLines=true;
let audio=null,oscA=null,oscB=null,gain=null,soundOn=false;
const attractorParams={};

function resize(){canvas.width=innerWidth*devicePixelRatio;canvas.height=innerHeight*devicePixelRatio}addEventListener('resize',resize);resize();
function current(){return DATA.scenes[sceneIndex]}
function metric(k,v){return `<div class="metric"><span>${k}</span><span>${v}</span></div>`}
function round(v,n=5){return Number(v).toFixed(n)}
function bounds(P){let lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];for(const p of P)for(let i=0;i<3;i++){lo[i]=Math.min(lo[i],p[i]||0);hi[i]=Math.max(hi[i],p[i]||0)}return[lo,hi]}
function projectPoint(p,b){let [x,y,z]=p;const pr=projection.value;if(pr==='xy')z=0;else if(pr==='xz'){y=z;z=0}else if(pr==='yz'){x=y;y=z;z=0}else{const cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch);const x1=cy*x-sy*z,z1=sy*x+cy*z;const y1=cp*y-sp*z1;x=x1;y=y1;z=sp*y+cp*z1}
 const lo=b[0],hi=b[1],sx=(canvas.width*.66)/Math.max(hi[0]-lo[0],1e-9),syy=(canvas.height*.72)/Math.max(hi[1]-lo[1],1e-9),s=Math.min(sx,syy);return[canvas.width/2+(x-(lo[0]+hi[0])/2)*s,canvas.height/2-(y-(lo[1]+hi[1])/2)*s,z]}
function rhs(name,s,p){const[x,y,z]=s;if(name==='rossler')return[-y-z,x+p.a*y,p.b+z*(x-p.c)];if(name==='lorenz')return[p.sigma*(y-x),x*(p.rho-z)-y,x*y-p.beta*z];return[Math.sin(y)-p.b*x,Math.sin(z)-p.b*y,Math.sin(x)-p.b*z]}
function rk4(name,s,dt,p){const k1=rhs(name,s,p),k2=rhs(name,s.map((v,i)=>v+dt*k1[i]/2),p),k3=rhs(name,s.map((v,i)=>v+dt*k2[i]/2),p),k4=rhs(name,s.map((v,i)=>v+dt*k3[i]),p);return s.map((v,i)=>v+dt*(k1[i]+2*k2[i]+2*k3[i]+k4[i])/6)}
function integrateClient(sc){const p=attractorParams[sc.id]||{...sc.parameters},dt=sc.dt,steps=sc.id==='thomas'?18000:12000,burn=sc.id==='thomas'?4000:2500;let s=[...sc.defaults],out=[];for(let i=0;i<steps;i++){s=rk4(sc.id,s,dt,p);if(i>=burn&&i%4===0&&s.every(Number.isFinite))out.push([...s]);if(!s.every(Number.isFinite)||Math.max(...s.map(Math.abs))>1e8)break}return out}
function liveDiagnostics(sc,P){if(sc.kind!=='attractor')return metric('scene type',sc.kind)+metric('samples',P.length);const p=attractorParams[sc.id]||sc.parameters;let div=0,cross=0;for(let i=1;i<P.length;i++){const q=P[i];if(sc.id==='rossler')div+=p.a+q[0]-p.c;else if(sc.id==='lorenz')div+=-(p.sigma+1+p.beta);else div+=-3*p.b;if(P[i-1][0]<=0&&q[0]>0)cross++}div/=Math.max(P.length,1);const b=bounds(P),span=Math.hypot(b[1][0]-b[0][0],b[1][1]-b[0][1],b[1][2]-b[0][2]);return metric('samples',P.length)+metric('mean divergence',round(div))+metric('x=0 crossings',cross)+metric('phase span',round(span))+metric('precomputed λ',sc.diagnostics.lyapunov.map(x=>round(x,4)).join(' / '))}
function setScene(index){sceneIndex=(index+DATA.scenes.length)%DATA.scenes.length;sceneSel.value=sceneIndex;const sc=current();points=sc.points?sc.points.map(p=>p.slice(0,3)):[];frame=0;lastSwitch=performance.now();document.getElementById('bigIndex').textContent=String(sceneIndex).padStart(2,'0');document.getElementById('sceneTitle').innerHTML=`${sc.label}<span id="sceneSub">${sc.description||''}</span>`;boundaryEl.textContent=sc.claim_boundary||DATA.claim_boundary;equationsEl.textContent=(sc.equations||['finite geometric/spectral dataset']).join('\n');buildParams(sc);updatePanels();}
function buildParams(sc){paramsEl.innerHTML='';if(sc.kind!=='attractor'){paramsEl.innerHTML='<div class="tiny">This scene uses a fixed finite dataset.</div>';return}attractorParams[sc.id]=attractorParams[sc.id]||{...sc.parameters};for(const [key,value] of Object.entries(sc.parameters)){const wrap=document.createElement('div');wrap.className='param';const span=Math.max(Math.abs(value)*.8,.5),min=value-span,max=value+span;wrap.innerHTML=`<div class="paramTop"><span>${key}</span><span id="pv-${key}">${round(attractorParams[sc.id][key],4)}</span></div><input data-key="${key}" type="range" min="${min}" max="${max}" step="${span/300}" value="${attractorParams[sc.id][key]}">`;paramsEl.appendChild(wrap);wrap.querySelector('input').oninput=e=>{attractorParams[sc.id][key]=+e.target.value;document.getElementById('pv-'+key).textContent=round(+e.target.value,4)}}}
function updatePanels(){const sc=current();metricsEl.innerHTML=liveDiagnostics(sc,points);let evidence='';if(sc.kind==='attractor'){const d=sc.diagnostics;evidence+=metric('DMD rank',d.dmd.rank)+metric('DMD residual',round(d.dmd.reconstruction_error,6))+metric('validated step',d.validated_step.validated?'PASS':'FAIL')+metric('interval width',round(d.validated_step.maximum_endpoint_width,8));evidence+=`<pre>${JSON.stringify({dominant_modes:d.dominant_modes,validated_reason:d.validated_step.reason},null,2)}</pre>`}else if(sc.kind==='spectra'){for(const m of sc.models)evidence+=metric(m.id+' dim',m.audit.dimension)+metric(m.id+' gap',round(m.audit.spectral_gap,6))+metric('Hermitian',m.audit.hermitian?'PASS':'FAIL')}else evidence+=metric('dataset','finite / embedded');evidenceEl.innerHTML=evidence;document.getElementById('tickerInner').textContent=`${DATA.schema} // ${sc.id} // ${sc.claim_boundary||DATA.claim_boundary} // git ${DATA.git_commit||'unavailable'} // `}
function drawAttractor(sc){const max=Math.min(+density.value,points.length),P=points.slice(0,max);if(!P.length)return;const b=bounds(P);ctx.lineWidth=devicePixelRatio*(drawLines?.72:1);ctx.strokeStyle='#f2f2f2';ctx.fillStyle='#fff';ctx.globalAlpha=.86;ctx.beginPath();const reveal=mode==='experience'?Math.max(20,Math.floor((frame*+speed.value)%P.length)):P.length;for(let i=0;i<reveal;i++){const q=projectPoint(P[i],b);if(drawLines){if(i===0)ctx.moveTo(q[0],q[1]);else ctx.lineTo(q[0],q[1])}else{ctx.fillRect(q[0],q[1],1.2*devicePixelRatio,1.2*devicePixelRatio)}}if(drawLines)ctx.stroke();ctx.globalAlpha=1;const idx=Math.min(reveal-1,P.length-1);if(soundOn&&idx>=0)updateSound(P[idx],b)}
function drawLattice(sc){const P=sc.points,b=bounds(P);yaw+=.002*+speed.value;ctx.strokeStyle='#555';ctx.lineWidth=.55*devicePixelRatio;for(const e of sc.edges){const a=projectPoint(P[e[0]],b),d=projectPoint(P[e[1]],b);ctx.strokeStyle=e[2]?'#fff':'#343434';ctx.lineWidth=(e[2]?2:.55)*devicePixelRatio;ctx.beginPath();ctx.moveTo(a[0],a[1]);ctx.lineTo(d[0],d[1]);ctx.stroke()}ctx.fillStyle='#aaa';for(const p of P){const q=projectPoint(p,b);ctx.fillRect(q[0]-1,q[1]-1,2,2)}}
function drawWeights(sc){const rows=(Math.floor(frame/600)%2?sc.decuplet:sc.octet),P=rows.map(r=>r.slice(0,3)),b=bounds(P);yaw+=.002*+speed.value;ctx.fillStyle='#fff';for(let i=0;i<P.length;i++){const q=projectPoint(P[i],b),mult=rows[i][3];ctx.beginPath();ctx.arc(q[0],q[1],(4+mult*2)*devicePixelRatio,0,7);ctx.fill();ctx.strokeStyle='#333';for(let r=1;r<mult;r++){ctx.beginPath();ctx.arc(q[0],q[1],(4+mult*2-r*2)*devicePixelRatio,0,7);ctx.stroke()}}}
function drawSpectra(sc){const models=sc.models,gap=canvas.width/(models.length+1);models.forEach((m,mi)=>{const vals=m.eigenvalues,lo=Math.min(...vals),hi=Math.max(...vals),x=gap*(mi+1);ctx.fillStyle='#777';ctx.textAlign='center';ctx.fillText(m.id,x,canvas.height*.18);for(let i=0;i<vals.length;i++){const y=canvas.height*.78-(vals[i]-lo)/Math.max(hi-lo,1e-9)*canvas.height*.52;ctx.strokeStyle=i<2?'#fff':'#444';ctx.lineWidth=(i<2?2:1)*devicePixelRatio;ctx.beginPath();ctx.moveTo(x-80*devicePixelRatio,y);ctx.lineTo(x+80*devicePixelRatio,y);ctx.stroke();if(i<2){ctx.fillStyle='#aaa';ctx.fillText(round(vals[i],4),x+96*devicePixelRatio,y+3)}}})}
function drawLimits(sc){const n=sc.log_mass.length,x0=canvas.width*.18,x1=canvas.width*.82,y0=canvas.height*.78,y1=canvas.height*.22;const map=(x,y)=>[x0+(x+6)/12*(x1-x0),y0-(y+6.5)/13*(y0-y1)];for(const [arr,label,style] of [[sc.log_schwarzschild,'Schwarzschild','#fff'],[sc.log_compton,'Compton','#777']]){ctx.strokeStyle=style;ctx.lineWidth=1.3*devicePixelRatio;ctx.beginPath();for(let i=0;i<n;i++){const q=map(sc.log_mass[i],arr[i]);i?ctx.lineTo(...q):ctx.moveTo(...q)}ctx.stroke();ctx.fillStyle=style;ctx.fillText(label,x1-80*devicePixelRatio,label==='Compton'?y1+20:y0-20)}}
function draw(){const alpha=1-Math.min(+trail.value/100,.985);ctx.fillStyle=`rgba(3,3,3,${alpha})`;ctx.fillRect(0,0,canvas.width,canvas.height);ctx.font=`${11*devicePixelRatio}px ui-monospace,monospace`;const sc=current();if(sc.kind==='attractor')drawAttractor(sc);else if(sc.id==='lattice')drawLattice(sc);else if(sc.id==='su3')drawWeights(sc);else if(sc.kind==='spectra')drawSpectra(sc);else drawLimits(sc);frame++;if(mode==='experience'&&performance.now()-lastSwitch>12000)setScene(sceneIndex+1);requestAnimationFrame(draw)}
function setMode(next){mode=next;body.className=next;document.getElementById('experience').classList.toggle('active',next==='experience');document.getElementById('experiment').classList.toggle('active',next==='experiment');lastSwitch=performance.now()}
function startSound(){audio=audio||new AudioContext();oscA=audio.createOscillator();oscB=audio.createOscillator();gain=audio.createGain();const filter=audio.createBiquadFilter();oscA.type='sine';oscB.type='square';oscA.connect(filter);oscB.connect(filter);filter.connect(gain);gain.connect(audio.destination);gain.gain.value=.025;oscA.start();oscB.start();soundOn=true;document.getElementById('sound').textContent='Sound: on'}
function stopSound(){if(gain)gain.gain.setTargetAtTime(0,audio.currentTime,.03);setTimeout(()=>{try{oscA.stop();oscB.stop()}catch(e){}},100);soundOn=false;document.getElementById('sound').textContent='Sound: off'}
function updateSound(p,b){if(!audio||!soundOn)return;const norm=(v,i)=>(v-b[0][i])/Math.max(b[1][i]-b[0][i],1e-9);oscA.frequency.setTargetAtTime(45+norm(p[0],0)*900,audio.currentTime,.03);oscB.frequency.setTargetAtTime(24+norm(p[1],1)*220,audio.currentTime,.04);gain.gain.setTargetAtTime(.008+norm(p[2],2)*.035,audio.currentTime,.05)}
DATA.scenes.forEach((s,i)=>{const o=document.createElement('option');o.value=i;o.textContent=`${String(i).padStart(2,'0')} // ${s.label}`;sceneSel.appendChild(o)});
sceneSel.onchange=()=>setScene(+sceneSel.value);projection.onchange=()=>frame=0;document.getElementById('experience').onclick=()=>setMode('experience');document.getElementById('experiment').onclick=()=>setMode('experiment');
document.getElementById('sound').onclick=()=>soundOn?stopSound():startSound();document.getElementById('run').onclick=()=>{const sc=current();if(sc.kind==='attractor'){points=integrateClient(sc);frame=0;updatePanels()}};
document.getElementById('points').onclick=()=>{drawLines=false;document.getElementById('points').classList.add('active');document.getElementById('lines').classList.remove('active')};document.getElementById('lines').onclick=()=>{drawLines=true;document.getElementById('lines').classList.add('active');document.getElementById('points').classList.remove('active')};
for(const el of [density,speed,trail])el.oninput=()=>{document.getElementById(el.id+'V').textContent=el.value};density.oninput();speed.oninput();trail.oninput();
setInterval(()=>document.getElementById('clock').textContent=new Date().toISOString(),250);setScene(0);draw();
</script></body></html>'''


def _preview_svg(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
<rect width="1200" height="630" fill="#030303"/><g fill="none" stroke="#fff" stroke-width="1" opacity=".9">
<path d="M670 110 C850 75 1025 180 1005 330 C985 480 760 535 585 450 C410 365 425 185 570 145 C705 110 860 205 835 335 C810 465 625 470 535 370 C445 270 525 165 635 170 C745 175 800 265 760 345 C720 425 610 410 565 345 C520 280 570 220 635 225 C700 230 725 285 700 330"/>
</g><g fill="#fff" font-family="monospace"><text x="65" y="90" font-size="18" letter-spacing="5">GAUGEGAP // FOUNDRY</text><text x="65" y="155" font-size="54" font-weight="700">EXPERIENCE</text><text x="65" y="215" font-size="54" fill="#666">EXPERIMENT</text><text x="65" y="520" font-size="16" fill="#999">FINITE DATA · EQUATIONS · SONIFICATION · EVIDENCE · CLAIM BOUNDARIES</text><text x="65" y="566" font-size="12" fill="#ff5a5a">NO CONTINUUM OR MILLENNIUM CLAIM</text></g><path d="M65 470H1135" stroke="#222"/>
</svg>\n""",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "site" / "foundry-experience",
    )
    parser.add_argument(
        "--preview",
        type=Path,
        default=ROOT / "figures" / "foundry-experience" / "preview.svg",
    )
    args = parser.parse_args()

    dataset = build_dataset()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    data_path = args.output_dir / "data.json"
    html_path = args.output_dir / "index.html"
    data_path.write_text(json.dumps(dataset, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    html_path.write_text(
        _HTML.replace("__DATA__", json.dumps(dataset, sort_keys=True, separators=(",", ":"))),
        encoding="utf-8",
    )
    _preview_svg(args.preview)

    artifacts = (
        EvidenceArtifact.from_path(data_path, base=args.output_dir, kind="data"),
        EvidenceArtifact.from_path(html_path, base=args.output_dir, kind="interactive_view"),
    )
    claim = ResearchClaim(
        claim_id="foundry-experience-0001",
        title="GaugeGap Foundry Experience finite-data interface",
        statement=(
            "The generated static interface reproduces the embedded finite datasets and "
            "permits finite browser-side reintegration of the registered ODEs."
        ),
        level=ClaimLevel.REPRODUCIBLE_FINITE_RESULT,
        finite_scope="embedded finite trajectories, finite matrices, and finite geometry datasets",
        assumptions=("modern browser with Canvas and optional WebAudio support",),
        exclusions=(
            "no formal proof of chaos or a global strange attractor",
            "no continuum Yang-Mills or Navier-Stokes theorem",
            "no Millennium Prize problem solution claim",
        ),
        evidence=artifacts,
        methods=("RK4", "finite-time Lyapunov QR", "exact DMD", "interval Picard step", "exact diagonalization"),
        parameters={"scene_count": len(dataset["scenes"]), "schema": dataset["schema"]},
        git_commit=dataset["git_commit"] or "unavailable-local-checkout",
    )
    write_manifest(args.output_dir / "research_manifest.json", [claim])
    (args.output_dir / "README.md").write_text(
        "# GaugeGap Foundry Experience\n\nOpen `index.html` in a modern browser. "
        "The output is dependency-free and self-contained except for its adjacent "
        "machine-readable `data.json` and `research_manifest.json`.\n\n> "
        + CLAIM_BOUNDARY
        + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "status": "pass",
        "output": str(html_path),
        "scenes": len(dataset["scenes"]),
        "preview": str(args.preview),
        "claim_boundary": CLAIM_BOUNDARY,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
