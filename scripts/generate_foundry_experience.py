#!/usr/bin/env python3
"""Generate GaugeGap Foundry's self-contained Experience / Experiment interface.

The interface uses one structural idea from Ryoji Ikeda's *supersymmetry*:
separate an immersive data ``experience`` from an exposed, manipulable
``experiment``.  The implementation, visual composition, code, and data are
original and come entirely from GaugeGap Foundry.

The output has no CDN, no server dependency, no remote assets, and no automatic
audio.  Audio is locally synthesized only after an explicit user action.

CLAIM BOUNDARY: finite computations and finite-time diagnostics only.  The output
is not a continuum Yang-Mills result, a Millennium Prize solution, or a formal
proof of chaos or a global strange attractor.
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
    "Finite computations and finite-time diagnostics only; no continuum "
    "Yang-Mills mass-gap claim, no Millennium Prize solution claim, and no "
    "formal proof of chaos or a global strange attractor."
)


def _r(value: float, digits: int = 8) -> float:
    return round(float(value), digits)


def _sample_rows(values: np.ndarray, maximum: int) -> np.ndarray:
    if len(values) <= maximum:
        return values
    stride = max(1, int(np.ceil(len(values) / maximum)))
    return values[::stride][:maximum]


def _equations(name: str) -> list[str]:
    if name == "rossler":
        return ["dx/dt = -y-z", "dy/dt = x+a y", "dz/dt = b+z(x-c)"]
    if name == "lorenz":
        return ["dx/dt = sigma(y-x)", "dy/dt = x(rho-z)-y", "dz/dt = xy-beta z"]
    if name == "thomas":
        return ["dx/dt = sin(y)-b x", "dy/dt = sin(z)-b y", "dz/dt = sin(x)-b z"]
    raise ValueError(name)


def build_attractor_dataset(
    name: str,
    *,
    steps: int,
    transient_steps: int,
    sample_every: int,
    maximum_points: int,
) -> dict[str, Any]:
    system = get_system(name)
    params = system.parameters()
    dt = 0.02 if name == "thomas" else 0.01
    times, states = integrate(
        system,
        params,
        system.default_state,
        dt=dt,
        steps=steps,
        sample_every=sample_every,
    )
    start = min(len(states) - 1, transient_steps // sample_every)
    combined = _sample_rows(
        np.column_stack((times[start:], states[start:])), maximum_points
    )
    points = combined[:, 1:]
    divergences = np.array(
        [system.divergence(point, params) for point in points], dtype=float
    )
    return {
        "id": name,
        "kind": "attractor",
        "label": name.title(),
        "description": system.description,
        "parameters": {key: _r(value) for key, value in params.items()},
        "default_state": [_r(value) for value in system.default_state],
        "dt": dt,
        "source_steps": steps,
        "transient_steps": transient_steps,
        "sample_every": sample_every,
        "time": [_r(value) for value in combined[:, 0]],
        "points": [[_r(value) for value in point] for point in points],
        "extents": [
            [_r(np.min(points[:, axis])), _r(np.max(points[:, axis]))]
            for axis in range(3)
        ],
        "mean_divergence": _r(np.mean(divergences)),
        "fraction_negative_divergence": _r(np.mean(divergences < 0.0)),
        "equations": _equations(name),
        "method": "deterministic fixed-step classical RK4",
        "claim_boundary": (
            "Finite-time ODE trajectory; its visual form is not a formal proof "
            "of chaos, ergodicity, or a global attractor."
        ),
    }


def build_z2_dataset(*, points: int) -> dict[str, Any]:
    if points < 3:
        raise ValueError("points must be at least 3")
    couplings = np.linspace(0.25, 2.0, points)
    fields = np.linspace(0.0, 1.5, points)
    records: list[dict[str, float]] = []
    for coupling in couplings:
        for field in fields:
            gap, e0, e1 = mass_gap(1, float(coupling), float(field))
            obs = ground_state_observables(1, float(coupling), float(field))
            records.append(
                {
                    "j": _r(coupling, 6),
                    "h": _r(field, 6),
                    "gap": _r(gap),
                    "e0": _r(e0),
                    "e1": _r(e1),
                    "plaquette_z": _r(obs["mean_plaquette_z"]),
                    "link_x": _r(obs["mean_link_x"]),
                }
            )
    return {
        "id": "z2",
        "kind": "spectrum",
        "label": "Z2 finite plaquette",
        "model": model_metadata(1, 1.0, 0.2),
        "couplings": [_r(value, 6) for value in couplings],
        "fields": [_r(value, 6) for value in fields],
        "records": records,
        "equations": ["H = -J product_l Z_l - h sum_l X_l", "gap = E1-E0"],
        "method": "exact dense diagonalization of a 4-qubit, 16-dimensional Hamiltonian",
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
                "centroid": [_r(value) for value in weight_centroid(weights)],
                "weyl_closed": bool(weyl_orbit_closed(weights)),
                "weights": [
                    {
                        "t3": _r(weight["t3"]),
                        "y": _r(weight["y"]),
                        "mult": int(weight["mult"]),
                    }
                    for weight in weights
                ],
            }
        )
    return {
        "id": "su3",
        "kind": "geometry",
        "label": "SU(3) representation geometry",
        "representations": representations,
        "method": "exact weight multiplicities from Freudenthal recursion",
        "claim_boundary": (
            "Exact finite representation geometry; not a completed SU(3) "
            "lattice Hamiltonian and not a continuum gauge-theory result."
        ),
    }


def build_payload(*, smoke: bool = False) -> dict[str, Any]:
    steps = 2200 if smoke else 12000
    transient = 300 if smoke else 2500
    channels = [
        build_attractor_dataset(
            name,
            steps=steps,
            transient_steps=transient,
            sample_every=4 if smoke else 5,
            maximum_points=450 if smoke else 1800,
        )
        for name in SYSTEMS
    ]
    channels.extend(
        [build_z2_dataset(points=5 if smoke else 13), build_su3_dataset()]
    )
    return {
        "schema": SCHEMA,
        "title": "GaugeGap Foundry — Experience / Experiment",
        "modes": {
            "experience": "immersive synchronized views of finite data",
            "experiment": "manipulable finite models with evidence exposed",
        },
        "channels": channels,
        "audio": {
            "default": "off",
            "source": "local Web Audio synthesis from the selected finite signal",
        },
        "claim_boundary": CLAIM_BOUNDARY,
        "provenance": {
            "generator": "scripts/generate_foundry_experience.py",
            "remote_assets": [],
            "external_runtime_dependencies": [],
        },
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_bundle(output_dir: Path, *, smoke: bool = False) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = build_payload(smoke=smoke)
    data_path = output_dir / "experience-data.json"
    html_path = output_dir / "index.html"
    data_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    compact = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    html_path.write_text(
        _HTML.replace("__FOUNDRY_DATA__", compact), encoding="utf-8"
    )
    manifest = {
        "schema": "gaugegap.foundry_experience_manifest.v1",
        "claim_boundary": CLAIM_BOUNDARY,
        "deterministic": True,
        "self_contained": True,
        "audio_opt_in": True,
        "files": {
            path.name: {"sha256": _sha256(path), "bytes": path.stat().st_size}
            for path in (html_path, data_path)
        },
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


_HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GaugeGap Foundry — Experience / Experiment</title>
<style>
:root{--b:#020202;--f:#f7f7f2;--m:#888;--l:#292929;--r:#ff3158;--c:#58d7ff}
*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;background:var(--b);color:var(--f);font:13px ui-monospace,SFMono-Regular,Menlo,monospace;overflow:hidden}
button,select,input{font:inherit}button,select{background:#050505;color:var(--f);border:1px solid #3b3b3b;padding:8px;text-transform:uppercase;letter-spacing:.08em}button{cursor:pointer}button:hover,button.active{background:var(--f);color:var(--b);border-color:var(--f)}
#app{height:100%;display:grid;grid-template-rows:54px 1fr 34px}.top{display:flex;align-items:center;gap:9px;padding:8px 12px;border-bottom:1px solid var(--l)}.brand{margin-right:auto;font-weight:700;letter-spacing:.13em}.brand span{color:var(--m);font-weight:400}.mode{min-width:118px}.stage{position:relative;min-height:0}.view{position:absolute;inset:0;display:none}.view.active{display:block}canvas{width:100%;height:100%;display:block}
#rail{position:absolute;left:13px;top:13px;display:flex;flex-direction:column;gap:5px}#rail button{text-align:left;min-width:150px;font-size:10px}#readout{position:absolute;right:13px;top:13px;width:min(340px,40vw);padding:12px;background:#070707e8;border:1px solid var(--l)}#readout h2{font-size:12px;letter-spacing:.12em;text-transform:uppercase;margin:0 0 10px}.metric{display:grid;grid-template-columns:1fr auto;border-top:1px solid #1d1d1d;padding:6px 0;font-size:10px}.metric span:first-child{color:var(--m)}
#experiment{height:100%;grid-template-columns:270px 1fr 330px}#experiment.active{display:grid}.panel{padding:13px;overflow:auto;background:#060606}.controls{border-right:1px solid var(--l)}.evidence{border-left:1px solid var(--l)}.panel h2{font-size:11px;letter-spacing:.13em;text-transform:uppercase}.field{margin:0 0 13px}.field label{display:flex;justify-content:space-between;color:var(--m);font-size:10px;margin-bottom:5px}.field input,.field select{width:100%}.field input{accent-color:var(--f)}.center{position:relative;min-width:0}.stats{position:absolute;left:10px;bottom:10px;display:grid;grid-template-columns:repeat(3,minmax(100px,1fr));gap:1px;background:var(--l);border:1px solid var(--l)}.stats div{padding:8px 10px;background:#050505}.stats b{display:block;font-size:16px}.stats small{color:var(--m);font-size:8px;text-transform:uppercase}.evidence section{border-top:1px solid var(--l);padding:10px 0}.evidence h3{font-size:9px;text-transform:uppercase;letter-spacing:.12em;color:var(--m)}.evidence p,.evidence li{font-size:10px;line-height:1.5}.evidence ul{padding-left:16px}.tag{display:inline-block;border:1px solid var(--c);color:var(--c);padding:3px 5px;font-size:8px;text-transform:uppercase}.tag.exact{border-color:var(--f);color:var(--f)}.tag.boundary{border-color:var(--r);color:var(--r)}
.footer{display:flex;align-items:center;padding:0 12px;border-top:1px solid var(--l);font-size:9px;color:var(--m);white-space:nowrap;overflow:hidden}.footer strong{color:var(--r);margin-right:6px}.keys{margin-left:auto}
@media(max-width:900px){#experiment.active{grid-template-columns:220px 1fr}.evidence{display:none}.brand span{display:none}}
@media(max-width:640px){.brand{font-size:10px}.mode{min-width:auto}#rail{left:6px;top:6px}#rail button{min-width:95px;font-size:8px;padding:6px}#readout{right:6px;top:6px;width:55vw;padding:7px}.controls{position:absolute;z-index:4;width:205px;height:100%;background:#050505ef}.stats{left:215px;right:7px;grid-template-columns:1fr}.stats div:not(:first-child){display:none}.keys{display:none}}
</style></head><body>
<div id="app"><header class="top"><div class="brand">GAUGEGAP FOUNDRY <span>/ finite data instrument</span></div><button class="mode active" data-mode="experience">experience</button><button class="mode" data-mode="experiment">experiment</button><button id="sound">sound off</button></header>
<main class="stage"><section id="experience" class="view active"><canvas id="experienceCanvas"></canvas><nav id="rail"></nav><aside id="readout"></aside></section>
<section id="experiment" class="view"><aside class="panel controls"><h2>finite model controls</h2><div class="field"><label>model</label><select id="model"></select></div><div id="fields"></div><button id="reset">reset</button></aside><div class="center"><canvas id="experimentCanvas"></canvas><div class="stats" id="stats"></div></div><aside class="panel evidence" id="evidence"></aside></section></main>
<footer class="footer"><strong>BOUNDARY</strong><span id="boundary"></span><span class="keys">E experience · X experiment · space pause · M sound</span></footer></div>
<script>'use strict';
const DATA=__FOUNDRY_DATA__,channels=DATA.channels,byId=Object.fromEntries(channels.map(x=>[x.id,x]));
const S={mode:'experience',channel:'rossler',model:'rossler',phase:0,paused:false,sound:false,audio:null,osc:null,gain:null,params:{},trajectory:[]};
const $=id=>document.getElementById(id),clamp=(v,a,b)=>Math.max(a,Math.min(b,v)),fmt=(v,d=5)=>Number.isFinite(v)?Number(v).toFixed(d):'—';
$('boundary').textContent=DATA.claim_boundary;
function fit(c){const r=c.getBoundingClientRect(),d=Math.min(devicePixelRatio||1,2),w=Math.max(1,Math.floor(r.width*d)),h=Math.max(1,Math.floor(r.height*d));if(c.width!==w||c.height!==h){c.width=w;c.height=h}return{w,h,d}}
function grid(g,w,h,d){g.strokeStyle='rgba(255,255,255,.045)';g.lineWidth=d;g.beginPath();for(let x=0;x<w;x+=48*d){g.moveTo(x,0);g.lineTo(x,h)}for(let y=0;y<h;y+=48*d){g.moveTo(0,y);g.lineTo(w,y)}g.stroke()}
function project(p,w,h,a,scale=.33){const ca=Math.cos(a),sa=Math.sin(a),cp=Math.cos(.45),sp=Math.sin(.45),x=p[0]*ca-p[2]*sa,z=p[0]*sa+p[2]*ca,y=p[1],yy=y*cp-z*sp;return[w*.5+x*scale*Math.min(w,h),h*.5-yy*scale*Math.min(w,h)]}
function setMode(mode){S.mode=mode;document.querySelectorAll('.mode').forEach(b=>b.classList.toggle('active',b.dataset.mode===mode));document.querySelectorAll('.view').forEach(v=>v.classList.toggle('active',v.id===mode));if(mode==='experiment')setupExperiment()}
document.querySelectorAll('.mode').forEach(b=>b.onclick=()=>setMode(b.dataset.mode));
function buildRail(){channels.forEach(ch=>{const b=document.createElement('button');b.textContent=ch.label;b.dataset.id=ch.id;b.classList.toggle('active',ch.id===S.channel);b.onclick=()=>{S.channel=ch.id;[...$('rail').children].forEach(x=>x.classList.toggle('active',x.dataset.id===ch.id));readout()};$('rail').appendChild(b)})}
function readout(){const ch=byId[S.channel];let rows;if(ch.kind==='attractor')rows=[['method','RK4'],['samples',ch.points.length],['mean divergence',fmt(ch.mean_divergence)],['negative divergence',fmt(ch.fraction_negative_divergence*100,1)+'%'],['dt',ch.dt]];else if(ch.kind==='spectrum')rows=[['method','exact diagonalization'],['Hilbert space','4 qubits / 16'],['grid records',ch.records.length],['observable','E1-E0']];else rows=[['method','Freudenthal recursion'],['representations',ch.representations.length],['Weyl closed',String(ch.representations.every(r=>r.weyl_closed))],['centroid','origin']];$('readout').innerHTML='<h2>'+ch.label+'</h2>'+rows.map(r=>'<div class="metric"><span>'+r[0]+'</span><span>'+r[1]+'</span></div>').join('')+'<div class="metric"><span>boundary</span><span>'+ch.claim_boundary+'</span></div>'}
function drawExperience(){const c=$('experienceCanvas'),g=c.getContext('2d'),{w,h,d}=fit(c),ch=byId[S.channel];g.fillStyle='#020202';g.fillRect(0,0,w,h);grid(g,w,h,d);if(ch.kind==='attractor')drawAttractor(g,w,h,d,ch);else if(ch.kind==='spectrum')drawSpectrum(g,w,h,d,ch);else drawGeometry(g,w,h,d,ch)}
function drawAttractor(g,w,h,d,ch){const max=ch.extents.map(v=>Math.max(Math.abs(v[0]),Math.abs(v[1]))||1),pts=ch.points.map(p=>p.map((v,i)=>v/max[i]));g.strokeStyle='rgba(255,255,255,.86)';g.lineWidth=.75*d;g.beginPath();pts.forEach((p,i)=>{const q=project(p,w,h,S.phase*.06);i?g.lineTo(...q):g.moveTo(...q)});g.stroke();for(const side of[-1,1])for(let b=0;b<11;b++){const z=b/10,x0=w*.5+side*(w*.13+z*w*.36),hh=h*(.08+z*.32),start=Math.floor((S.phase*8+b*131)%pts.length);g.strokeStyle=b%4===0?'rgba(255,49,88,.72)':'rgba(255,255,255,'+(.13+.45*z)+')';g.beginPath();for(let k=0;k<44;k++){const p=pts[(start+k*3)%pts.length],x=x0+side*(k/43)*w*.04,y=h*.5+p[(b+1)%3]*hh*.55;k?g.lineTo(x,y):g.moveTo(x,y)}g.stroke()}}
function drawSpectrum(g,w,h,d,ch){const rows=ch.fields.length,cols=ch.couplings.length,cw=w/(cols+4),rh=h/(rows+4),max=Math.max(...ch.records.map(r=>r.gap));ch.records.forEach((r,i)=>{const x=(Math.floor(i/rows)+2)*cw,y=((i%rows)+2)*rh,a=clamp(r.gap/max,0.03,.95)*(.75+.25*Math.sin(S.phase+i*.17));g.fillStyle='rgba(255,255,255,'+a+')';g.fillRect(x,y,cw*.72,rh*.5);if(r.plaquette_z<0){g.fillStyle='rgba(255,49,88,.7)';g.fillRect(x,y,cw*.1,rh*.5)}});g.strokeStyle='rgba(88,215,255,.7)';g.beginPath();for(let x=0;x<w;x+=3*d){const y=h*.5+Math.sin(x*.02/d+S.phase)*h*.07;x?g.lineTo(x,y):g.moveTo(x,y)}g.stroke()}
function drawGeometry(g,w,h,d,ch){ch.representations.forEach((rep,i)=>{const cx=w*(i ? .68 : .32),cy=h*.5,sc=Math.min(w,h)*.22,a=S.phase*.03*(i?1:-1);g.strokeStyle='rgba(255,255,255,.18)';g.beginPath();rep.weights.forEach((p,j)=>{const x=p.t3*Math.cos(a)-p.y*Math.sin(a),y=p.t3*Math.sin(a)+p.y*Math.cos(a);j?g.lineTo(cx+x*sc,cy-y*sc):g.moveTo(cx+x*sc,cy-y*sc)});g.closePath();g.stroke();rep.weights.forEach((p,j)=>{const x=p.t3*Math.cos(a)-p.y*Math.sin(a),y=p.t3*Math.sin(a)+p.y*Math.cos(a);g.fillStyle=j%3?'#f7f7f2':'#ff3158';g.beginPath();g.arc(cx+x*sc,cy-y*sc,(2.5+p.mult*1.8)*d,0,Math.PI*2);g.fill()})})}
const defaults={rossler:{a:.2,b:.2,c:5.7,dt:.01},lorenz:{sigma:10,rho:28,beta:2.666667,dt:.008},thomas:{b:.208186,dt:.02},z2:{j:1,h:.25}},ranges={a:[.05,.5,.01],b:[.05,.5,.01],c:[2,12,.1],sigma:[1,20,.5],rho:[1,50,.5],beta:[.5,5,.1],dt:[.002,.03,.001],j:[.25,2,.01],h:[0,1.5,.01]};
function setupExperiment(){if(!$('model').children.length){channels.filter(c=>c.kind!=='geometry').forEach(ch=>{const o=document.createElement('option');o.value=ch.id;o.textContent=ch.label;$('model').appendChild(o)});$('model').onchange=()=>{S.model=$('model').value;reset()};$('reset').onclick=reset}if(!Object.keys(S.params).length)reset();else controls()}
function reset(){S.params={...defaults[S.model]};$('model').value=S.model;controls();recompute()}
function controls(){$('fields').innerHTML='';Object.entries(S.params).forEach(([k,v])=>{const[min,max,step]=ranges[k],box=document.createElement('div');box.className='field';box.innerHTML='<label><span>'+k+'</span><output>'+fmt(v,4)+'</output></label><input type="range" min="'+min+'" max="'+max+'" step="'+step+'" value="'+v+'">';const input=box.querySelector('input'),out=box.querySelector('output');input.oninput=()=>{S.params[k]=+input.value;out.textContent=fmt(S.params[k],4);recompute()};$('fields').appendChild(box)})}
function deriv(m,p,s){const[x,y,z]=s;if(m==='rossler')return[-y-z,x+p.a*y,p.b+z*(x-p.c)];if(m==='lorenz')return[p.sigma*(y-x),x*(p.rho-z)-y,x*y-p.beta*z];return[Math.sin(y)-p.b*x,Math.sin(z)-p.b*y,Math.sin(x)-p.b*z]}
function rk4(m,p,s,dt){const add=(a,b,k)=>a.map((v,i)=>v+k*b[i]),k1=deriv(m,p,s),k2=deriv(m,p,add(s,k1,dt/2)),k3=deriv(m,p,add(s,k2,dt/2)),k4=deriv(m,p,add(s,k3,dt));return s.map((v,i)=>v+dt*(k1[i]+2*k2[i]+2*k3[i]+k4[i])/6)}
function trajectory(){let s=S.model==='lorenz'?[1,1,1]:S.model==='thomas'?[.1,0,0]:[0,1,0],out=[];for(let i=0;i<6200;i++){s=rk4(S.model,S.params,s,S.params.dt);if(i>1200&&i%3===0&&s.every(Number.isFinite))out.push([...s]);if(!s.every(Number.isFinite)||s.some(v=>Math.abs(v)>1e7))break}return out}
function nearestZ2(){let best=null,dist=Infinity;for(const r of byId.z2.records){const q=Math.abs(r.j-S.params.j)+Math.abs(r.h-S.params.h);if(q<dist){best=r;dist=q}}return best}
function recompute(){S.trajectory=S.model==='z2'?[]:trajectory();evidence();drawExperiment()}
function evidence(){const ch=byId[S.model];let stats,body;if(ch.kind==='spectrum'){const r=nearestZ2();stats=[['gap',r.gap],['E0',r.e0],['E1',r.e1]];body='<section><h3>exact lookup</h3><p>Controls select the nearest point in a grid generated by the repository\'s exact 16×16 Hamiltonian diagonalization.</p></section><section><h3>observables</h3><p>mean plaquette Z = '+fmt(r.plaquette_z)+'<br>mean link X = '+fmt(r.link_x)+'</p></section>'}else{const amp=S.trajectory.length?Math.max(...S.trajectory.slice(-250).map(p=>Math.hypot(...p))):NaN;stats=[['samples',S.trajectory.length],['state norm',amp],['dt',S.params.dt]];body='<section><h3>live integration</h3><p>Fixed-step RK4 recomputes a finite browser trajectory after every parameter change.</p></section><section><h3>equations</h3><ul>'+ch.equations.map(e=>'<li>'+e+'</li>').join('')+'</ul></section>'}$('stats').innerHTML=stats.map(r=>'<div><b>'+fmt(+r[1],5)+'</b><small>'+r[0]+'</small></div>').join('');$('evidence').innerHTML='<h2>evidence chain</h2><section><span class="tag '+(ch.kind==='spectrum'?'exact':'')+'">'+(ch.kind==='spectrum'?'exact finite':'finite numerical')+'</span></section>'+body+'<section><h3>method</h3><p>'+ch.method+'</p></section><section><h3>claim boundary</h3><p class="tag boundary">'+ch.claim_boundary+'</p></section>'}
function drawExperiment(){const c=$('experimentCanvas'),g=c.getContext('2d'),{w,h,d}=fit(c);g.fillStyle='#020202';g.fillRect(0,0,w,h);grid(g,w,h,d);if(S.model==='z2'){const ch=byId.z2,r=nearestZ2(),rows=ch.fields.length,cols=ch.couplings.length,cw=w/cols,rh=h/rows,max=Math.max(...ch.records.map(x=>x.gap));ch.records.forEach((q,i)=>{const x=Math.floor(i/rows)*cw,y=(i%rows)*rh;g.fillStyle='rgba(255,255,255,'+clamp(q.gap/max,.03,.95)+')';g.fillRect(x+1,y+1,cw-2,rh-2);if(q===r){g.strokeStyle='#ff3158';g.lineWidth=3*d;g.strokeRect(x+2,y+2,cw-4,rh-4)}})}else if(S.trajectory.length){const max=[0,0,0];S.trajectory.forEach(p=>p.forEach((v,i)=>max[i]=Math.max(max[i],Math.abs(v))));g.strokeStyle='#f7f7f2';g.lineWidth=.8*d;g.beginPath();S.trajectory.forEach((p,i)=>{const q=project(p.map((v,j)=>v/(max[j]||1)),w,h,S.phase*.02,.38);i?g.lineTo(...q):g.moveTo(...q)});g.stroke()}}
async function sound(){S.sound=!S.sound;$('sound').textContent=S.sound?'sound on':'sound off';$('sound').classList.toggle('active',S.sound);if(S.sound){if(!S.audio){S.audio=new(window.AudioContext||window.webkitAudioContext)();S.osc=S.audio.createOscillator();S.gain=S.audio.createGain();S.gain.gain.value=.012;S.osc.connect(S.gain).connect(S.audio.destination);S.osc.start()}await S.audio.resume()}else if(S.audio)S.gain.gain.setTargetAtTime(0,S.audio.currentTime,.03)}
$('sound').onclick=sound;
function updateSound(){if(!S.sound||!S.osc)return;const ch=byId[S.mode==='experience'?S.channel:S.model];let v=.5;if(ch.kind==='attractor'){const pts=S.mode==='experiment'?S.trajectory:ch.points;if(pts.length){const p=pts[Math.floor(S.phase*7)%pts.length];v=.5+.5*Math.tanh((p[0]+p[1])*.15)}}else if(ch.kind==='spectrum'){const r=S.mode==='experiment'?nearestZ2():ch.records[Math.floor(S.phase*3)%ch.records.length];v=clamp(r.gap/4,0,1)}else v=.5+.3*Math.sin(S.phase*.2);S.osc.frequency.setTargetAtTime(90+v*760,S.audio.currentTime,.05);S.gain.gain.setTargetAtTime(.008+v*.018,S.audio.currentTime,.08)}
let last=performance.now();function frame(now){const dt=Math.min(.05,(now-last)/1000);last=now;if(!S.paused)S.phase+=dt;drawExperience();if(S.mode==='experiment')drawExperiment();updateSound();requestAnimationFrame(frame)}
window.onresize=()=>{drawExperience();drawExperiment()};window.onkeydown=e=>{if(e.key.toLowerCase()==='e')setMode('experience');if(e.key.toLowerCase()==='x')setMode('experiment');if(e.key===' '){e.preventDefault();S.paused=!S.paused}if(e.key.toLowerCase()==='m')sound()};
buildRail();readout();setupExperiment();requestAnimationFrame(frame);
</script></body></html>'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "site" / "foundry-experience",
    )
    parser.add_argument("--smoke", action="store_true")
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
