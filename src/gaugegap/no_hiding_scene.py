"""InfoGap no-hiding dataset and browser-interface extension."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from gaugegap.quantum_information.no_hiding import audit_no_hiding, run_no_hiding_suite


def no_hiding_scene() -> dict[str, Any]:
    selected = audit_no_hiding(1.1, 0.7, label="default")
    suite = run_no_hiding_suite(random_count=6, seed=1729)
    return {
        "kind": "no_hiding",
        "id": "no-hiding",
        "label": "Information Cannot Disappear",
        "description": "A finite three-qubit realization of the quantum no-hiding theorem",
        "equations": [
            "|psi>_S |00>_AB -> |Phi+>_SA |psi>_B",
            "rho_S(psi) = I/2",
            "F(rho_B, |psi><psi|) = 1",
            "U = CNOT(S,A) H(S) SWAP(S,B)",
        ],
        "parameters": {"theta": 1.1, "phi": 0.7},
        "controls": {
            "theta": [0.0, 3.141592653589793, 0.005],
            "phi": [-3.141592653589793, 3.141592653589793, 0.005],
        },
        "selected": selected.summary(),
        "suite": suite.summary(),
        "circuit": [
            {"gate": "SWAP", "qubits": ["S", "B"]},
            {"gate": "H", "qubits": ["S"]},
            {"gate": "CNOT", "qubits": ["S", "A"]},
        ],
        "subsystems": {
            "system": "S",
            "environment": ["A", "B"],
            "recovery": "B",
            "fixed_correlation": "Bell pair on S,A",
        },
        "views": {
            "xy": "information flow",
            "xz": "Bloch transfer",
            "yz": "entropy ledger",
            "3d": "unitary circuit",
        },
        "claim_boundary": selected.claim_boundary,
    }


def enhance_dataset(dataset: dict[str, Any]) -> dict[str, Any]:
    output = deepcopy(dataset)
    scenes = list(output.get("scenes", []))
    if not any(scene.get("id") == "no-hiding" for scene in scenes):
        insertion = next(
            (index + 1 for index, scene in enumerate(scenes) if scene.get("id") == "standard-model-anomalies"),
            len(scenes),
        )
        scenes.insert(insertion, no_hiding_scene())
    output["scenes"] = scenes
    output["schema"] = "gaugegap.foundry_experience.v4"
    return output


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(
            f"No-Hiding patch marker {label!r} expected once, found {text.count(old)}"
        )
    return text.replace(old, new, 1)


def enhance_html(html: str) -> str:
    html = _replace_once(
        html,
        "const attractorParams={};const lagrangianParams={};const anomalyParams={};",
        "const attractorParams={};const lagrangianParams={};const anomalyParams={};const noHidingParams={};",
        "parameter stores",
    )
    html = _replace_once(
        html,
        "function liveDiagnostics(sc,P){if(sc.kind==='anomaly')",
        "function liveDiagnostics(sc,P){if(sc.kind==='no_hiding'){const n=noHidingValues(sc);return metric('system dependence',n.systemDependence.toExponential(2))+metric('recovery fidelity',round(n.recoveryFidelity,12))+metric('system entropy',round(n.systemEntropy,6))+metric('S:E mutual information',round(n.mutualInformation,6))+metric('Bloch error',n.blochError.toExponential(2))}if(sc.kind==='anomaly')",
        "live diagnostics",
    )
    html = _replace_once(
        html,
        "function buildParams(sc){paramsEl.innerHTML='';if(sc.kind==='anomaly')",
        "function buildParams(sc){paramsEl.innerHTML='';if(sc.kind==='no_hiding'){noHidingParams[sc.id]=noHidingParams[sc.id]||{...sc.parameters};for(const [key,value] of Object.entries(sc.parameters)){const c=sc.controls[key],wrap=document.createElement('div');wrap.className='param';wrap.innerHTML=`<div class=\"paramTop\"><span>${key}</span><span id=\"nh-${key}\">${round(noHidingParams[sc.id][key],5)}</span></div><input data-key=\"${key}\" type=\"range\" min=\"${c[0]}\" max=\"${c[1]}\" step=\"${c[2]}\" value=\"${noHidingParams[sc.id][key]}\">`;paramsEl.appendChild(wrap);wrap.querySelector('input').oninput=e=>{noHidingParams[sc.id][key]=+e.target.value;document.getElementById('nh-'+key).textContent=round(+e.target.value,5);updatePanels();frame=0}}return}if(sc.kind==='anomaly')",
        "parameter controls",
    )
    html = _replace_once(
        html,
        "}else if(sc.kind==='anomaly'){const a=anomalyValues(sc);",
        "}else if(sc.kind==='no_hiding'){const n=noHidingValues(sc);evidence+=metric('canonical suite',sc.suite.passed?'PASS':'FAIL')+metric('states audited',sc.suite.case_count)+metric('minimum fidelity',round(sc.suite.minimum_recovery_fidelity,12))+metric('maximum system dependence',sc.suite.maximum_system_dependence.toExponential(2));evidence+=`<pre>${JSON.stringify({circuit:sc.circuit,subsystems:sc.subsystems,selected:sc.selected,claim_boundary:sc.claim_boundary},null,2)}</pre>`}else if(sc.kind==='anomaly'){const a=anomalyValues(sc);",
        "evidence panel",
    )
    helpers = r'''
function noHidingValues(sc){const p=noHidingParams[sc.id]||sc.parameters,t=+p.theta,ph=+p.phi,b=[Math.sin(t)*Math.cos(ph),Math.sin(t)*Math.sin(ph),Math.cos(t)];return{input:b,recovered:b.slice(),system:[0,0,0],systemDependence:0,recoveryFidelity:1,systemEntropy:1,recoveryEntropy:0,environmentEntropy:1,mutualInformation:2,systemRecoveryMutualInformation:0,blochError:0}}
function drawNoHiding(sc){const n=noHidingValues(sc),view=projection.value,w=canvas.width,h=canvas.height,cx=w/2,cy=h/2;ctx.textAlign='center';if(view==='xy'){const nodes=[['INPUT |psi>',w*.13,h*.5,'#58d7ff'],['UNITARY',w*.38,h*.5,'#fff'],['SYSTEM I/2',w*.68,h*.3,'#777'],['ENVIRONMENT |psi>',w*.78,h*.68,'#7ee787']];ctx.lineWidth=2*devicePixelRatio;ctx.strokeStyle='#555';ctx.beginPath();ctx.moveTo(w*.2,h*.5);ctx.lineTo(w*.3,h*.5);ctx.moveTo(w*.47,h*.5);ctx.lineTo(w*.61,h*.32);ctx.moveTo(w*.47,h*.5);ctx.lineTo(w*.71,h*.66);ctx.stroke();for(const [label,x,y,color] of nodes){ctx.strokeStyle=color;ctx.fillStyle='#080808';ctx.beginPath();ctx.arc(x,y,54*devicePixelRatio,0,7);ctx.fill();ctx.stroke();ctx.fillStyle=color;ctx.fillText(label,x,y+5*devicePixelRatio)}}else if(view==='xz'){const spheres=[[w*.2,'input',n.input,'#58d7ff'],[w*.5,'system',n.system,'#777'],[w*.8,'recovered',n.recovered,'#7ee787']];for(const [x,label,b,color] of spheres){const r=Math.min(w,h)*.11;ctx.strokeStyle=color;ctx.beginPath();ctx.arc(x,cy,r,0,7);ctx.stroke();ctx.beginPath();ctx.ellipse(x,cy,r,r*.28,0,0,7);ctx.stroke();ctx.beginPath();ctx.moveTo(x,cy);ctx.lineTo(x+b[0]*r,cy-b[2]*r);ctx.stroke();ctx.fillStyle=color;ctx.fillText(label,x,cy+r+28*devicePixelRatio)}}else if(view==='yz'){const bars=[['S entropy',n.systemEntropy],['B entropy',n.recoveryEntropy],['E entropy',n.environmentEntropy],['I(S:E)',n.mutualInformation]],max=2;for(let i=0;i<bars.length;i++){const x=w*(.18+i*.21),base=h*.76,height=bars[i][1]/max*h*.46;ctx.fillStyle=i===1?'#7ee787':i===0?'#777':'#fff';ctx.fillRect(x-32*devicePixelRatio,base-height,64*devicePixelRatio,height);ctx.fillStyle='#fff';ctx.fillText(bars[i][0],x,base+25*devicePixelRatio);ctx.fillText(round(bars[i][1],4),x,base-height-12*devicePixelRatio)}}else{const ys=[h*.28,h*.5,h*.72],labs=['S','A','B'];ctx.strokeStyle='#555';for(let i=0;i<3;i++){ctx.beginPath();ctx.moveTo(w*.12,ys[i]);ctx.lineTo(w*.88,ys[i]);ctx.stroke();ctx.fillStyle='#fff';ctx.fillText(labs[i],w*.08,ys[i]+5)}const gates=[['SWAP',w*.28,[0,2]],['H',w*.5,[0]],['CNOT',w*.72,[0,1]]];for(const [name,x,qs] of gates){ctx.strokeStyle='#fff';for(const q of qs){ctx.strokeRect(x-24*devicePixelRatio,ys[q]-18*devicePixelRatio,48*devicePixelRatio,36*devicePixelRatio)}ctx.fillStyle='#fff';ctx.fillText(name,x,ys[qs[0]]-28*devicePixelRatio)}}ctx.textAlign='left';ctx.fillStyle='#7ee787';ctx.fillText(sc.views[view]||view,w*.08,h*.94)}
'''
    html = _replace_once(
        html,
        "function anomalyValues(sc)",
        helpers + "function anomalyValues(sc)",
        "draw helpers",
    )
    html = _replace_once(
        html,
        "else if(sc.kind==='lagrangian')drawLagrangian(sc);else if(sc.kind==='anomaly')drawAnomaly(sc);else drawLimits(sc);",
        "else if(sc.kind==='lagrangian')drawLagrangian(sc);else if(sc.kind==='anomaly')drawAnomaly(sc);else if(sc.kind==='no_hiding')drawNoHiding(sc);else drawLimits(sc);",
        "draw dispatch",
    )
    html = _replace_once(
        html,
        "else if(sc.kind==='lagrangian'||sc.kind==='anomaly'){frame=0;updatePanels()}};",
        "else if(sc.kind==='lagrangian'||sc.kind==='anomaly'||sc.kind==='no_hiding'){frame=0;updatePanels()}};",
        "run control",
    )
    return html
