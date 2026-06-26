"""Lagrangian Forge dataset and browser-interface extension."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from gaugegap.interaction_graph import build_interaction_graph
from gaugegap.lagrangian_audit import audit_standard_model
from gaugegap.standard_model_catalog import standard_model_catalog, tree_level_observables


def standard_model_scene() -> dict[str, Any]:
    catalog = standard_model_catalog()
    graph = build_interaction_graph(catalog)
    audit = audit_standard_model(catalog)
    observables = tree_level_observables()
    return {
        "kind": "lagrangian",
        "id": "standard-model",
        "label": "Lagrangian Forge",
        "description": "From gauge symmetry to fields, vertices, symmetry breaking, and tree-level masses",
        "equations": [
            "L_SM = -1/4 G^a_mn G^{a mn} - 1/4 W^i_mn W^{i mn} - 1/4 B_mn B^{mn}",
            "+ sum_f fbar i gamma^mu D_mu f + (D_mu Phi)^dagger(D^mu Phi) - V(Phi)",
            "- (Qbar_L Y_d Phi d_R + Qbar_L Y_u Phi_tilde u_R + Lbar_L Y_e Phi e_R + h.c.)",
            "+ L_gauge-fixing + L_ghost",
        ],
        "gauge_group": list(catalog.gauge_group),
        "gauge_convention": catalog.gauge_convention,
        "sectors": [sector.summary() for sector in catalog.sectors],
        "fields": [field.summary() for field in catalog.fields],
        "interactions": [interaction.summary() for interaction in catalog.interactions],
        "graph": graph,
        "parameters": dict(catalog.default_parameters),
        "controls": {key: list(value) for key, value in catalog.control_ranges.items()},
        "observables": observables,
        "audit": audit.summary(),
        "source_note": catalog.source_note,
        "views": {
            "xy": "interaction graph",
            "xz": "equation wall",
            "yz": "symmetry breaking",
            "3d": "vertex atlas",
        },
        "claim_boundary": catalog.claim_boundary,
    }


def enhance_dataset(dataset: dict[str, Any]) -> dict[str, Any]:
    """Append the canonical scene once, preserving every existing scene."""
    output = deepcopy(dataset)
    scenes = list(output.get("scenes", []))
    if not any(scene.get("id") == "standard-model" for scene in scenes):
        insertion = next((index for index, scene in enumerate(scenes) if scene.get("id") == "spectra"), len(scenes))
        scenes.insert(insertion, standard_model_scene())
    output["scenes"] = scenes
    output["schema"] = "gaugegap.foundry_experience.v2"
    return output


def _replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(f"Lagrangian Forge patch marker {label!r} expected once, found {text.count(old)}")
    return text.replace(old, new, 1)


def enhance_html(html: str) -> str:
    """Extend the existing self-contained interface without removing any prior mode."""
    html = _replace_once(
        html,
        "const attractorParams={};",
        "const attractorParams={};const lagrangianParams={};",
        "parameter stores",
    )
    html = _replace_once(
        html,
        "function liveDiagnostics(sc,P){if(sc.kind!=='attractor')return metric('scene type',sc.kind)+metric('samples',P.length);",
        "function liveDiagnostics(sc,P){if(sc.kind==='lagrangian'){const o=smObservables(sc);return metric('fields',sc.audit.field_count)+metric('vertices',sc.audit.interaction_count)+metric('structural audit',sc.audit.passed?'PASS':'FAIL')+metric('M_W',round(o.m_w,3)+' GeV')+metric('M_Z',round(o.m_z,3)+' GeV')+metric('M_H',round(o.m_h,3)+' GeV')+metric('photon m^2 residual',o.photon_mass_squared_residual.toExponential(2))}if(sc.kind!=='attractor')return metric('scene type',sc.kind)+metric('samples',P.length);",
        "live diagnostics",
    )
    html = _replace_once(
        html,
        "function buildParams(sc){paramsEl.innerHTML='';if(sc.kind!=='attractor'){paramsEl.innerHTML='<div class=\"tiny\">This scene uses a fixed finite dataset.</div>';return}",
        "function buildParams(sc){paramsEl.innerHTML='';if(sc.kind==='lagrangian'){lagrangianParams[sc.id]=lagrangianParams[sc.id]||{...sc.parameters};for(const [key,value] of Object.entries(sc.parameters)){const control=sc.controls[key]||[value,value,1],wrap=document.createElement('div');wrap.className='param';wrap.innerHTML=`<div class=\"paramTop\"><span>${key}</span><span id=\"pv-${key}\">${round(lagrangianParams[sc.id][key],4)}</span></div><input data-key=\"${key}\" type=\"range\" min=\"${control[0]}\" max=\"${control[1]}\" step=\"${control[2]}\" value=\"${lagrangianParams[sc.id][key]}\">`;paramsEl.appendChild(wrap);wrap.querySelector('input').oninput=e=>{lagrangianParams[sc.id][key]=+e.target.value;document.getElementById('pv-'+key).textContent=round(+e.target.value,4);updatePanels();frame=0}}return}if(sc.kind!=='attractor'){paramsEl.innerHTML='<div class=\"tiny\">This scene uses a fixed finite dataset.</div>';return}",
        "parameter controls",
    )
    html = _replace_once(
        html,
        "else if(sc.kind==='spectra'){for(const m of sc.models)evidence+=metric(m.id+' dim',m.audit.dimension)+metric(m.id+' gap',round(m.audit.spectral_gap,6))+metric('Hermitian',m.audit.hermitian?'PASS':'FAIL')}else evidence+=metric('dataset','finite / embedded');",
        "else if(sc.kind==='spectra'){for(const m of sc.models)evidence+=metric(m.id+' dim',m.audit.dimension)+metric(m.id+' gap',round(m.audit.spectral_gap,6))+metric('Hermitian',m.audit.hermitian?'PASS':'FAIL')}else if(sc.kind==='lagrangian'){const o=smObservables(sc);evidence+=metric('gauge group',sc.gauge_group.join(' x '))+metric('audit',sc.audit.passed?'PASS':'FAIL')+metric('sin^2 theta_W',round(o.sin2_theta_w,6))+metric('electric coupling e',round(o.electric_charge_coupling,6))+metric('top mass',round(o.m_top,3)+' GeV');evidence+=`<pre>${JSON.stringify({checks:sc.audit.checks,graph:sc.graph.summary,source_note:sc.source_note},null,2)}</pre>`}else evidence+=metric('dataset','finite / embedded');",
        "evidence panel",
    )
    helpers = r'''
function smObservables(sc){const p=lagrangianParams[sc.id]||sc.parameters,g=+p.g,gp=+p.g_prime,v=+p.v,lam=+p.lambda_h,n=Math.hypot(g,gp),s=gp/n,c=g/n;const m2=v*v/4;const a=m2*g*g,b=-m2*g*gp,d=m2*gp*gp,tr=a+d,disc=Math.sqrt(Math.max(0,(a-d)*(a-d)+4*b*b));return{sin_theta_w:s,cos_theta_w:c,sin2_theta_w:s*s,electric_charge_coupling:g*s,m_w:g*v/2,m_z:n*v/2,m_h:Math.sqrt(Math.max(0,2*lam))*v,m_top:+p.y_t*v/Math.sqrt(2),m_bottom:+p.y_b*v/Math.sqrt(2),m_tau:+p.y_tau*v/Math.sqrt(2),photon_mass_squared_residual:Math.abs((tr-disc)/2)}}
function drawLagrangian(sc){const view=projection.value,w=canvas.width,h=canvas.height,ox=w/2,oy=h/2;ctx.textAlign='center';if(view==='xy'){const nodes=sc.graph.nodes,edgeMap=new Map(sc.graph.hyperedges.map((e,i)=>[i,e]));ctx.globalAlpha=.12;for(const [ei,ni] of sc.graph.segments){const e=edgeMap.get(ei),n=nodes[ni],cx=ox+e.centroid[0]*w*.3,cy=oy+e.centroid[1]*h*.3,x=ox+n.x*w*.3,y=oy+n.y*h*.3;ctx.strokeStyle='#fff';ctx.beginPath();ctx.moveTo(cx,cy);ctx.lineTo(x,y);ctx.stroke()}ctx.globalAlpha=1;for(const n of nodes){const x=ox+n.x*w*.3,y=oy+n.y*h*.3,r=(3+Math.sqrt(Math.max(1,n.degree)))*devicePixelRatio;ctx.fillStyle=n.kind==='gauge'?'#fff':n.kind==='scalar'?'#58d7ff':n.kind==='ghost'?'#ff7777':'#999';ctx.beginPath();ctx.arc(x,y,r,0,7);ctx.fill();ctx.fillStyle='#aaa';ctx.fillText(n.label,x,y+18*devicePixelRatio)}}else if(view==='xz'){const terms=sc.sectors.concat(sc.interactions);ctx.textAlign='left';ctx.font=`${11*devicePixelRatio}px ui-monospace,monospace`;for(let row=0;row<Math.min(terms.length,34);row++){const item=terms[(row+Math.floor(frame/16))%terms.length],x=w*.12+(row%2)*w*.42,y=h*.15+Math.floor(row/2)*h*.043;ctx.fillStyle=row%3?'#777':'#fff';ctx.fillText(item.compact_term||`${item.coupling} :: ${item.label}`,x,y)}}else if(view==='yz'){const o=smObservables(sc),cx=w/2;ctx.fillStyle='#fff';ctx.font=`${18*devicePixelRatio}px ui-monospace,monospace`;ctx.fillText('SU(2)L x U(1)Y  ->  U(1)EM',cx,h*.22);ctx.strokeStyle='#444';ctx.beginPath();ctx.moveTo(w*.22,h*.48);ctx.lineTo(w*.78,h*.48);ctx.stroke();for(const [label,value,x] of [['photon',0,w*.28],['W',o.m_w,w*.46],['Z',o.m_z,w*.62],['H',o.m_h,w*.76]]){const bar=Math.max(2,value/140*h*.27);ctx.fillStyle=label==='photon'?'#777':'#fff';ctx.fillRect(x-22*devicePixelRatio,h*.75-bar,44*devicePixelRatio,bar);ctx.fillText(`${label} ${round(value,2)}`,x,h*.79)}}else{const edges=sc.graph.hyperedges,cols=4,cellW=w*.72/cols,cellH=h*.62/Math.ceil(edges.length/cols),startX=w*.14,startY=h*.17;ctx.textAlign='left';for(let i=0;i<edges.length;i++){const e=edges[(i+Math.floor(frame/30))%edges.length],x=startX+(i%cols)*cellW,y=startY+Math.floor(i/cols)*cellH;ctx.strokeStyle='#292929';ctx.strokeRect(x,y,cellW*.9,cellH*.75);ctx.fillStyle='#fff';ctx.fillText(e.id,x+8,y+15);ctx.fillStyle='#777';ctx.fillText(e.coupling,x+8,y+30);ctx.fillText(e.fields.join(' · '),x+8,y+45)}}ctx.textAlign='left';ctx.fillStyle='#777';ctx.fillText(sc.views[view]||view,w*.08,h*.92)}
'''
    html = _replace_once(html, "function drawSpectra(sc)", helpers + "function drawSpectra(sc)", "Lagrangian draw helpers")
    html = _replace_once(
        html,
        "else if(sc.kind==='spectra')drawSpectra(sc);else drawLimits(sc);",
        "else if(sc.kind==='spectra')drawSpectra(sc);else if(sc.kind==='lagrangian')drawLagrangian(sc);else drawLimits(sc);",
        "draw dispatch",
    )
    html = _replace_once(
        html,
        "document.getElementById('run').onclick=()=>{const sc=current();if(sc.kind==='attractor'){points=integrateClient(sc);frame=0;updatePanels()}};",
        "document.getElementById('run').onclick=()=>{const sc=current();if(sc.kind==='attractor'){points=integrateClient(sc);frame=0;updatePanels()}else if(sc.kind==='lagrangian'){frame=0;updatePanels()}};",
        "run control",
    )
    return html
