"""Dependency-free interactive HTML renderer for verified SU(2) gap sweeps."""
from __future__ import annotations

import json
from typing import Any


def render_gap_forge_html(summary: dict[str, Any], rows: list[dict[str, object]]) -> str:
    payload = json.dumps({"summary": summary, "rows": rows}, sort_keys=True, separators=(",", ":"))
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gap Forge · Verified finite SU(2)</title>
<style>
:root{{--bg:#090c12;--panel:#111722;--line:#293241;--text:#e6edf3;--muted:#8b949e;--cyan:#58d7ff;--green:#7ee787;--violet:#d2a8ff;--red:#ff7b72}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 25% 0,#182238 0,var(--bg) 48%);color:var(--text);font-family:Inter,system-ui,sans-serif}}
header{{padding:28px 34px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:20px;align-items:flex-end}}h1{{margin:0;font-size:clamp(28px,5vw,56px);letter-spacing:-.04em}}.kicker{{font:12px ui-monospace,monospace;color:var(--cyan);letter-spacing:.16em}}.status{{border:1px solid var(--green);color:var(--green);padding:9px 13px;border-radius:999px;font:13px ui-monospace,monospace}}
main{{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(280px,.7fr);gap:18px;padding:20px;max-width:1440px;margin:auto}}.panel{{background:color-mix(in srgb,var(--panel) 92%,transparent);border:1px solid var(--line);border-radius:18px;padding:18px;box-shadow:0 16px 60px #0007}}canvas{{width:100%;height:480px;display:block}}label{{display:block;color:var(--muted);font:12px ui-monospace,monospace;margin:14px 0 6px}}select{{width:100%;background:#090d15;color:var(--text);border:1px solid var(--line);border-radius:10px;padding:10px}}.metric{{display:grid;grid-template-columns:1fr auto;gap:12px;padding:10px 0;border-bottom:1px solid #222b38;font:13px ui-monospace,monospace}}.metric b{{color:var(--green)}}pre{{white-space:pre-wrap;word-break:break-word;background:#090d15;border-radius:12px;padding:12px;color:#b7c4d5;font:11px ui-monospace,monospace;max-height:230px;overflow:auto}}.boundary{{color:var(--muted);font-size:12px;line-height:1.55;border-left:3px solid var(--violet);padding-left:12px}}@media(max-width:850px){{main{{grid-template-columns:1fr}}canvas{{height:360px}}}}
</style></head><body>
<header><div><div class="kicker">GAUGEGAP FOUNDRY · FINITE VERIFIED RESULT</div><h1>Gap Forge</h1><div style="color:var(--muted)">SU(2) one-plaquette class-function spectrum</div></div><div class="status" id="status">CERTIFIED POSITIVE</div></header>
<main><section class="panel"><canvas id="chart"></canvas></section><aside class="panel">
<label for="cutoff">representation cutoff j_max</label><select id="cutoff"></select>
<label for="electric">electric coupling</label><select id="electric"></select>
<div id="metrics"></div><label>evidence record</label><pre id="evidence"></pre><p class="boundary" id="boundary"></p>
</aside></main>
<script>
const data={payload};const rows=data.rows;const cutoff=document.getElementById('cutoff'),electric=document.getElementById('electric'),canvas=document.getElementById('chart'),ctx=canvas.getContext('2d');
const uniq=(xs)=>[...new Set(xs)];for(const v of uniq(rows.map(r=>r.max_two_j)).sort((a,b)=>a-b))cutoff.add(new Option(v+'/2',v));
function fillElectric(){{const prior=electric.value;electric.innerHTML='';for(const v of uniq(rows.filter(r=>String(r.max_two_j)===cutoff.value).map(r=>r.electric_float)).sort((a,b)=>a-b))electric.add(new Option(v,v));if([...electric.options].some(o=>o.value===prior))electric.value=prior}}
function selected(){{return rows.find(r=>String(r.max_two_j)===cutoff.value&&String(r.electric_float)===electric.value)||rows[0]}}
function resize(){{const d=devicePixelRatio||1;canvas.width=canvas.clientWidth*d;canvas.height=canvas.clientHeight*d;ctx.setTransform(d,0,0,d,0,0);draw()}}
function draw(){{const w=canvas.clientWidth,h=canvas.clientHeight,r=selected(),subset=rows.filter(x=>x.max_two_j===r.max_two_j).sort((a,b)=>a.electric_float-b.electric_float),max=Math.max(...rows.map(x=>x.gap_upper))*1.08,pad=58;ctx.clearRect(0,0,w,h);ctx.strokeStyle='#273244';ctx.fillStyle='#8b949e';ctx.font='12px ui-monospace,monospace';for(let i=0;i<6;i++){{const y=pad+(h-2*pad)*i/5;ctx.beginPath();ctx.moveTo(pad,y);ctx.lineTo(w-pad,y);ctx.stroke();ctx.fillText((max*(1-i/5)).toFixed(3),8,y+4)}}const minE=Math.min(...subset.map(x=>x.electric_float)),maxE=Math.max(...subset.map(x=>x.electric_float)),span=Math.max(maxE-minE,1e-9),X=x=>pad+(x-minE)/span*(w-2*pad),Y=y=>h-pad-y/max*(h-2*pad);ctx.strokeStyle='#58d7ff';ctx.lineWidth=2.5;ctx.beginPath();subset.forEach((x,i)=>{{const px=X(x.electric_float),py=Y(x.gap_lower);i?ctx.lineTo(px,py):ctx.moveTo(px,py)}});ctx.stroke();for(const x of subset){{const px=X(x.electric_float),yl=Y(x.gap_lower),yu=Y(x.gap_upper);ctx.strokeStyle=x===r?'#7ee787':'#d2a8ff';ctx.lineWidth=x===r?4:2;ctx.beginPath();ctx.moveTo(px,yu);ctx.lineTo(px,yl);ctx.stroke();ctx.fillStyle=ctx.strokeStyle;ctx.beginPath();ctx.arc(px,(yu+yl)/2,x===r?6:3,0,7);ctx.fill()}}ctx.fillStyle='#e6edf3';ctx.font='15px ui-monospace,monospace';ctx.fillText('certified gap interval vs electric coupling',pad,24);ctx.fillStyle='#8b949e';ctx.fillText('j_max = '+r.j_max,w-160,24);update(r)}}
function update(r){{document.getElementById('metrics').innerHTML=`<div class=metric><span>basis dimension</span><b>${{r.dimension}}</b></div><div class=metric><span>gap lower</span><b>${{r.gap_lower.toPrecision(10)}}</b></div><div class=metric><span>gap upper</span><b>${{r.gap_upper.toPrecision(10)}}</b></div><div class=metric><span>interval width</span><b>${{r.gap_width.toExponential(3)}}</b></div><div class=metric><span>status</span><b>${{r.strictly_positive?'POSITIVE':'FAILED'}}</b></div>`;document.getElementById('status').textContent=r.strictly_positive?'CERTIFIED POSITIVE':'NOT CERTIFIED';document.getElementById('status').style.borderColor=r.strictly_positive?'#7ee787':'#ff7b72';document.getElementById('evidence').textContent=JSON.stringify({{selected:r,canonical:data.summary}},null,2);document.getElementById('boundary').textContent=data.summary.claim_boundary}}
cutoff.onchange=()=>{{fillElectric();draw()}};electric.onchange=draw;fillElectric();addEventListener('resize',resize);resize();
</script></body></html>'''
