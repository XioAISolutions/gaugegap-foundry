"""Anomaly Forge dataset and browser-interface extension."""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
from typing import Any

from gaugegap.anomaly_audit import Hypercharges, payload
from gaugegap.hypercharge_solver import solve


def anomaly_scene() -> dict[str, Any]:
    solution = solve()
    assignment = solution.assignment
    perturbed = Hypercharges(
        colors=3,
        generations=3,
        y_q=assignment.y_q,
        y_u=Fraction(7, 10),
        y_d=assignment.y_d,
        y_l=assignment.y_l,
        y_e=assignment.y_e,
    )
    return {
        "kind": "anomaly",
        "id": "standard-model-anomalies",
        "label": "Anomaly Forge",
        "description": "Drag the hypercharges and watch quantum consistency appear or break",
        "equations": [
            "A[SU(3)^2 U(1)] = N_g (2Y_Q - Y_u - Y_d)",
            "A[SU(2)^2 U(1)] = N_g (N_c Y_Q + Y_L)",
            "A[U(1)^3] = N_g (2N_cY_Q^3 - N_cY_u^3 - N_cY_d^3 + 2Y_L^3 - Y_e^3)",
            "A[grav^2 U(1)] = N_g (2N_cY_Q - N_cY_u - N_cY_d + 2Y_L - Y_e)",
        ],
        "parameters": {
            "colors": 3.0,
            "generations": 3.0,
            "y_q": float(assignment.y_q),
            "y_u": float(assignment.y_u),
            "y_d": float(assignment.y_d),
            "y_l": float(assignment.y_l),
            "y_e": float(assignment.y_e),
        },
        "controls": {
            "colors": [1.0, 7.0, 1.0],
            "generations": [1.0, 5.0, 1.0],
            "y_q": [-0.5, 0.5, 1 / 60],
            "y_u": [-1.0, 1.0, 1 / 30],
            "y_d": [-1.0, 1.0, 1 / 30],
            "y_l": [-1.0, 0.5, 1 / 30],
            "y_e": [-1.5, 0.5, 1 / 30],
        },
        "exact": payload(assignment),
        "solver": solution.summary(),
        "failure_example": payload(perturbed),
        "views": {
            "xy": "anomaly balance",
            "xz": "triangle channels",
            "yz": "fractional charges",
            "3d": "constraint surface",
        },
        "claim_boundary": (
            "Under the declared field content, chirality, Yukawa assumptions and normalization, "
            "the displayed assignment cancels the registered local and global anomalies. "
            "Anomaly cancellation alone does not uniquely fix charges in every possible theory."
        ),
    }


def enhance_dataset(dataset: dict[str, Any]) -> dict[str, Any]:
    output = deepcopy(dataset)
    scenes = list(output.get("scenes", []))
    if not any(scene.get("id") == "standard-model-anomalies" for scene in scenes):
        insertion = next(
            (i + 1 for i, scene in enumerate(scenes) if scene.get("id") == "standard-model"),
            len(scenes),
        )
        scenes.insert(insertion, anomaly_scene())
    output["scenes"] = scenes
    return output


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(
            f"Anomaly Forge patch marker {label!r} expected once, found {text.count(old)}"
        )
    return text.replace(old, new, 1)


def enhance_html(html: str) -> str:
    html = _replace_once(
        html,
        "const attractorParams={};const lagrangianParams={};",
        "const attractorParams={};const lagrangianParams={};const anomalyParams={};",
        "parameter stores",
    )
    html = _replace_once(
        html,
        "function liveDiagnostics(sc,P){if(sc.kind==='lagrangian')",
        "function liveDiagnostics(sc,P){if(sc.kind==='anomaly'){const a=anomalyValues(sc),ok=a.pass?'PASS':'BROKEN';return metric('consistency',ok)+metric('SU(3)^2-U(1)',round(a.su3,6))+metric('SU(2)^2-U(1)',round(a.su2,6))+metric('U(1)^3',round(a.u13,6))+metric('gravity^2-U(1)',round(a.grav,6))+metric('weak doublets',a.doublets)}if(sc.kind==='lagrangian')",
        "live diagnostics",
    )
    html = _replace_once(
        html,
        "function buildParams(sc){paramsEl.innerHTML='';if(sc.kind==='lagrangian')",
        "function buildParams(sc){paramsEl.innerHTML='';if(sc.kind==='anomaly'){anomalyParams[sc.id]=anomalyParams[sc.id]||{...sc.parameters};for(const [key,value] of Object.entries(sc.parameters)){const c=sc.controls[key]||[value,value,1],wrap=document.createElement('div');wrap.className='param';wrap.innerHTML=`<div class=\"paramTop\"><span>${key}</span><span id=\"av-${key}\">${round(anomalyParams[sc.id][key],5)}</span></div><input data-key=\"${key}\" type=\"range\" min=\"${c[0]}\" max=\"${c[1]}\" step=\"${c[2]}\" value=\"${anomalyParams[sc.id][key]}\">`;paramsEl.appendChild(wrap);wrap.querySelector('input').oninput=e=>{anomalyParams[sc.id][key]=+e.target.value;document.getElementById('av-'+key).textContent=round(+e.target.value,5);updatePanels();frame=0}}return}if(sc.kind==='lagrangian')",
        "parameter controls",
    )
    html = _replace_once(
        html,
        "}else if(sc.kind==='lagrangian'){const o=smObservables(sc);",
        "}else if(sc.kind==='anomaly'){const a=anomalyValues(sc);evidence+=metric('exact default',sc.exact.anomalies.passes?'PASS':'FAIL')+metric('live assignment',a.pass?'ANOMALY FREE':'INCONSISTENT')+metric('proton charge',round(a.proton,6))+metric('neutron charge',round(a.neutron,6));evidence+=`<pre>${JSON.stringify({equations:sc.equations,solver:sc.solver,failure_example:sc.failure_example.anomalies.exact},null,2)}</pre>`}else if(sc.kind==='lagrangian'){const o=smObservables(sc);",
        "evidence panel",
    )
    helpers = r'''
function anomalyValues(sc){const p=anomalyParams[sc.id]||sc.parameters,n=Math.round(+p.colors),g=Math.round(+p.generations),yq=+p.y_q,yu=+p.y_u,yd=+p.y_d,yl=+p.y_l,ye=+p.y_e,su3=g*(2*yq-yu-yd),su2=g*(n*yq+yl),u13=g*(2*n*yq*yq*yq-n*yu*yu*yu-n*yd*yd*yd+2*yl*yl*yl-ye*ye*ye),grav=g*(2*n*yq-n*yu-n*yd+2*yl-ye),doublets=g*(n+1),eps=1e-7;return{su3,su2,u13,grav,doublets,up:yq+.5,down:yq-.5,proton:3*yq+.5,neutron:3*yq-.5,pass:Math.max(Math.abs(su3),Math.abs(su2),Math.abs(u13),Math.abs(grav))<eps&&doublets%2===0}}
function drawAnomaly(sc){const a=anomalyValues(sc),view=projection.value,w=canvas.width,h=canvas.height,cx=w/2,cy=h/2,accent=a.pass?'#7ee787':'#ff6b6b';ctx.textAlign='center';if(view==='xy'){const vals=[['SU3²U1',a.su3],['SU2²U1',a.su2],['U1³',a.u13],['grav²U1',a.grav]],R=Math.min(w,h)*.28;ctx.strokeStyle=accent;ctx.lineWidth=3*devicePixelRatio;ctx.beginPath();ctx.arc(cx,cy,R,0,7);ctx.stroke();ctx.fillStyle=accent;ctx.font=`${20*devicePixelRatio}px ui-monospace,monospace`;ctx.fillText(a.pass?'CONSISTENT':'ANOMALY',cx,cy);for(let i=0;i<vals.length;i++){const t=-Math.PI/2+i*Math.PI/2,x=cx+Math.cos(t)*R,y=cy+Math.sin(t)*R;ctx.fillStyle='#fff';ctx.fillText(vals[i][0],x,y-10);ctx.fillStyle=accent;ctx.fillText(round(vals[i][1],5),x,y+12)}}else if(view==='xz'){const labs=['SU(3)²-U(1)','SU(2)²-U(1)','U(1)³','grav²-U(1)'];for(let i=0;i<4;i++){const x=w*(.2+(i%2)*.6),y=h*(.28+Math.floor(i/2)*.42),r=70*devicePixelRatio;ctx.strokeStyle=accent;ctx.beginPath();ctx.moveTo(x,y-r);ctx.lineTo(x-r*.85,y+r*.55);ctx.lineTo(x+r*.85,y+r*.55);ctx.closePath();ctx.stroke();ctx.fillStyle='#fff';ctx.fillText(labs[i],x,y+r*.9)}}else if(view==='yz'){const cards=[['u',a.up],['d',a.down],['p=uud',a.proton],['n=udd',a.neutron]];for(let i=0;i<cards.length;i++){const x=w*(.2+(i%2)*.6),y=h*(.3+Math.floor(i/2)*.4);ctx.fillStyle=i<2?'#58d7ff':accent;ctx.font=`${42*devicePixelRatio}px ui-monospace,monospace`;ctx.fillText(cards[i][0],x,y);ctx.font=`${24*devicePixelRatio}px ui-monospace,monospace`;ctx.fillText(round(cards[i][1],6),x,y+42*devicePixelRatio)}}else{ctx.strokeStyle='#333';for(let i=0;i<11;i++){ctx.beginPath();ctx.moveTo(w*.15,h*(.15+i*.065));ctx.lineTo(w*.85,h*(.15+i*.065));ctx.stroke()}const x=w*(.5+a.su2*.18),y=h*(.5-a.su3*.18);ctx.fillStyle=accent;ctx.beginPath();ctx.arc(x,y,12*devicePixelRatio,0,7);ctx.fill();ctx.fillStyle='#fff';ctx.fillText('live charge assignment',x,y-22*devicePixelRatio);ctx.fillStyle='#777';ctx.fillText('origin = exact anomaly cancellation',cx,h*.88)}ctx.textAlign='left';ctx.fillStyle=accent;ctx.fillText(sc.views[view]||view,w*.08,h*.94)}
'''
    html = _replace_once(
        html,
        "function drawLagrangian(sc)",
        helpers + "function drawLagrangian(sc)",
        "draw helpers",
    )
    html = _replace_once(
        html,
        "else if(sc.kind==='spectra')drawSpectra(sc);else if(sc.kind==='lagrangian')drawLagrangian(sc);else drawLimits(sc);",
        "else if(sc.kind==='spectra')drawSpectra(sc);else if(sc.kind==='lagrangian')drawLagrangian(sc);else if(sc.kind==='anomaly')drawAnomaly(sc);else drawLimits(sc);",
        "draw dispatch",
    )
    html = _replace_once(
        html,
        "else if(sc.kind==='lagrangian'){frame=0;updatePanels()}};",
        "else if(sc.kind==='lagrangian'||sc.kind==='anomaly'){frame=0;updatePanels()}};",
        "run control",
    )
    return html
