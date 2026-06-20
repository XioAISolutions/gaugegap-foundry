#!/usr/bin/env python3
"""Self-contained interactive 'flatten the higher-dimensional form' explorer.

Emits a single dependency-free HTML file (vanilla JS + <canvas>, no CDN, no Python
runtime deps) that lets you drag-rotate an exact 3D structure and pull a "flatten"
slider that collapses it to its exact 2D shadow:

  * su(3) octet / decuplet weights — they lie on a plane in the sum-zero R^3
    embedding (rank 2), so flattening to the (T3, Y) plane is exact;
  * the Calabi-Yau (Fermat) cross-section — its R^4->R^3 projection flattened to a
    2D shadow.

CLAIM BOUNDARY: faithful projections of exact objects (su(3) representation theory;
the Fermat surface). Decorative only beyond that; not a physics claim. Output is
byte-deterministic (rounded coordinates).
"""
from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

warnings.filterwarnings("ignore")

from gaugegap.visualization.weight_diagrams import su3_weights, su3_dimension
from gaugegap.visualization.cy_projection import fermat_patches
from gaugegap.visualization.lattice_projection import cubic_lattice, wilson_loop

_PREC = 4


def _round(x):
    return round(float(x), _PREC)


def _weight_dataset(p: int, q: int, label: str) -> dict:
    ws = su3_weights(p, q)
    pts = []
    for w in ws:
        a, b, c = w["r3"]
        # 3D coords = the sum-zero embedding (a plane); flatten target = (T3, Y, 0).
        pts.append({
            "x3": _round(a), "y3": _round(b), "z3": _round(c),
            "xf": _round(w["t3"]), "yf": _round(w["y"]),
            "mult": w["mult"],
        })
    return {"kind": "weights", "label": f"{label} (dim {su3_dimension(p, q)})",
            "points": pts, "edges": []}


def _cy_dataset(n: int, n_grid: int) -> dict:
    patches = fermat_patches(n=n, n_grid=n_grid)
    pts = []
    segs = []
    idx = 0
    for patch in patches:
        g = patch.grid3d
        gi, gj, _ = g.shape
        base = idx
        for i in range(gi):
            for j in range(gj):
                x, y, z = g[i, j]
                pts.append({"x3": _round(x), "y3": _round(y), "z3": _round(z),
                            "xf": _round(x), "yf": _round(y), "mult": 1})
                if j > 0:
                    segs.append([base + i * gj + (j - 1), base + i * gj + j])
                if i > 0:
                    segs.append([base + (i - 1) * gj + j, base + i * gj + j])
        idx += gi * gj
    return {"kind": "cy", "label": f"Calabi-Yau Fermat z1^{n}+z2^{n}=1",
            "points": pts, "edges": segs}


def _lattice_dataset() -> dict:
    lat = cubic_lattice(3, 3, 3)
    loop = wilson_loop(lat, (0, 0, 0), R=2, T=2, plane="xy")
    ctr = lat.sites.mean(axis=0)
    pts = []
    for s in lat.sites:
        x, y, z = (s - ctr)
        pts.append({"x3": _round(x), "y3": _round(y), "z3": _round(z),
                    "xf": _round(x), "yf": _round(y), "mult": 1})
    loop_edges = {tuple(sorted((loop[i], loop[i + 1]))) for i in range(len(loop) - 1)}
    edges = []
    for (a, b) in lat.links:
        hl = 1 if tuple(sorted((a, b))) in loop_edges else 0
        edges.append([a, b, hl])
    return {"kind": "lattice", "label": "Lattice + Wilson loop", "points": pts,
            "edges": edges}


_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>Geometry of GaugeGap — flatten explorer</title>
<style>
 body{margin:0;background:#0b0e14;color:#e6edf3;font-family:monospace}
 #wrap{display:flex;flex-direction:column;align-items:center;padding:12px}
 canvas{background:#0b0e14;border:1px solid #30363d;touch-action:none}
 .row{margin:8px;display:flex;gap:14px;align-items:center;flex-wrap:wrap}
 button{background:#161b22;color:#e6edf3;border:1px solid #30363d;padding:6px 10px;cursor:pointer;font-family:monospace}
 button.active{border-color:#58a6ff;color:#58a6ff}
 input[type=range]{width:240px}
 .note{color:#8b949e;font-size:12px;max-width:640px;text-align:center}
</style></head><body><div id="wrap">
<h3 id="title">Geometry of GaugeGap</h3>
<div class="row" id="picker"></div>
<canvas id="c" width="640" height="640"></canvas>
<div class="row">
  <label>flatten <input id="flat" type="range" min="0" max="100" value="0"></label>
  <button id="play">&#9654; play</button>
  <label><input id="sacred" type="checkbox"> golden overlay</label>
  <span class="note">drag to rotate &middot; slide (or play) to flatten to the exact 2D shadow</span>
</div>
<div class="note">Faithful projections of exact objects (su(3) weights via Freudenthal;
Fermat surface). Overlay is decorative only — not a mathematical claim.</div>
</div>
<script>
const DATA = __DATA__;
const c=document.getElementById('c'),ctx=c.getContext('2d');
let cur=0,yaw=0.6,pitch=0.5,drag=false,px=0,py=0;
const flat=document.getElementById('flat'),sacred=document.getElementById('sacred');
function rot(p){const cy=Math.cos(yaw),sy=Math.sin(yaw),cp=Math.cos(pitch),sp=Math.sin(pitch);
 let x=p[0]*cy+p[2]*sy, z=-p[0]*sy+p[2]*cy, y=p[1];
 let y2=y*cp-z*sp, z2=y*sp+z*cp; return [x,y2,z2];}
function draw(){const d=DATA.sets[cur];ctx.clearRect(0,0,640,640);
 const t=flat.value/100;
 // compute projected coords
 let P=[],minx=1e9,maxx=-1e9,miny=1e9,maxy=-1e9;
 for(const q of d.points){
   // interpolate 3D->flatten target
   const X=q.x3*(1-t)+q.xf*t, Y=q.y3*(1-t)+q.yf*t, Z=q.z3*(1-t);
   let r=rot([X,Y,Z]); P.push(r);
   minx=Math.min(minx,r[0]);maxx=Math.max(maxx,r[0]);
   miny=Math.min(miny,r[1]);maxy=Math.max(maxy,r[1]);}
 const span=Math.max(maxx-minx,maxy-miny)||1, sc=(640-120)/span;
 const cx=(minx+maxx)/2, cyy=(miny+maxy)/2;
 const tf=r=>[320+(r[0]-cx)*sc, 320-(r[1]-cyy)*sc];
 if(sacred.checked){const phi=(1+Math.sqrt(5))/2;let rr=260;ctx.strokeStyle='#d4a017';
   for(let k=0;k<6;k++){ctx.globalAlpha=.18;ctx.beginPath();ctx.arc(320,320,rr,0,7);ctx.stroke();rr/=phi;}ctx.globalAlpha=1;}
 // edges (e[2]==1 highlights the Wilson loop)
 for(const e of d.edges){const a=tf(P[e[0]]),b=tf(P[e[1]]);
   if(e[2]){ctx.strokeStyle='#f0c674';ctx.globalAlpha=.95;ctx.lineWidth=2.6;}
   else{ctx.strokeStyle='#3b6ea5';ctx.globalAlpha=.5;ctx.lineWidth=.8;}
   ctx.beginPath();ctx.moveTo(a[0],a[1]);ctx.lineTo(b[0],b[1]);ctx.stroke();}
 ctx.globalAlpha=1;
 // points
 for(let i=0;i<d.points.length;i++){const q=d.points[i],r=tf(P[i]);
   if(d.kind==='cy'){ctx.fillStyle='#58a6ff';ctx.beginPath();ctx.arc(r[0],r[1],1.4,0,7);ctx.fill();}
   else{for(let m=0;m<q.mult;m++){ctx.fillStyle='#f0c674';ctx.strokeStyle='#0b0e14';
     ctx.beginPath();ctx.arc(r[0],r[1],9-3*m,0,7);ctx.fill();ctx.stroke();}}}
 document.getElementById('title').textContent='Geometry of GaugeGap — '+d.label
   +(t>0.99?'  (flattened 2D shadow)':'');
}
function mk(){const pk=document.getElementById('picker');
 DATA.sets.forEach((d,i)=>{const b=document.createElement('button');b.textContent=d.label.split(' (')[0];
  b.onclick=()=>{cur=i;[...pk.children].forEach(x=>x.classList.remove('active'));b.classList.add('active');draw();};
  if(i===0)b.classList.add('active');pk.appendChild(b);});}
c.addEventListener('pointerdown',e=>{drag=true;px=e.clientX;py=e.clientY;});
addEventListener('pointerup',()=>drag=false);
addEventListener('pointermove',e=>{if(!drag)return;yaw+=(e.clientX-px)*.01;pitch+=(e.clientY-py)*.01;px=e.clientX;py=e.clientY;draw();});
flat.addEventListener('input',draw);sacred.addEventListener('change',draw);
// Auto-play: slowly rotate while easing flatten 0->100->0 (the "reel" loop).
let playing=false,phase=0,raf=0;
const play=document.getElementById('play');
function tick(){if(!playing)return;phase+=0.012;yaw+=0.006;
 flat.value=Math.round(50-50*Math.cos(phase));draw();raf=requestAnimationFrame(tick);}
play.onclick=()=>{playing=!playing;play.classList.toggle('active',playing);
 play.innerHTML=playing?'&#10073;&#10073; pause':'&#9654; play';
 if(playing)tick();else cancelAnimationFrame(raf);};
mk();draw();
</script></body></html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cy-n", type=int, default=5)
    ap.add_argument("--cy-grid", type=int, default=10)
    ap.add_argument("--output", type=Path,
                    default=ROOT / "figures" / "geometry" / "geometry_explorer.html")
    args = ap.parse_args()

    data = {"sets": [
        _weight_dataset(1, 1, "su(3) octet"),
        _weight_dataset(3, 0, "su(3) decuplet"),
        _lattice_dataset(),
        _cy_dataset(args.cy_n, args.cy_grid),
    ]}
    html = _HTML.replace("__DATA__", json.dumps(data, sort_keys=True))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    print(f"wrote interactive explorer -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
