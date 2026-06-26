"""Build a deterministic, offline Experience/Experiment interface from Foundry results.

The interface is deliberately downstream of scientific execution.  It never invents
claims or recomputes scientific results: it scans reproducible artifacts, exposes their
hashes and claim boundaries, and renders two views over the same manifest.

* Experience mode: a full-screen, auto-sequenced presentation of verified artifacts.
* Experiment mode: a searchable workbench for inspecting evidence, metadata and files.

The visual language is high-contrast and data-led, but the implementation is original
and self-contained.  No external JavaScript, fonts, tracking or network access is used.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import html
import json
from pathlib import Path
from typing import Any, Iterable


TEXT_EXTENSIONS = {
    ".csv", ".json", ".jsonl", ".lean", ".md", ".svg", ".thy", ".txt", ".v", ".yaml", ".yml"
}
PREVIEW_LIMIT = 120_000
CLAIM_KEYS = (
    "claim_boundary",
    "claim",
    "scope",
    "maturity",
    "research_maturity",
    "limitations",
)


@dataclass(frozen=True)
class ArtifactRecord:
    path: str
    track: str
    kind: str
    title: str
    sha256: str
    bytes: int
    claim_boundary: str
    preview: str
    truncated: bool


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _kind(path: Path) -> str:
    name = path.name.lower()
    suffix = path.suffix.lower()
    if suffix == ".svg":
        return "visual"
    if suffix in {".lean", ".v", ".thy"}:
        return "formal"
    if suffix in {".json", ".jsonl", ".yaml", ".yml"}:
        return "data"
    if suffix == ".csv":
        return "table"
    if suffix == ".md":
        return "narrative"
    if "certificate" in name or "proof" in name:
        return "certificate"
    return "text"


def _track(relative: Path) -> str:
    if len(relative.parts) > 1:
        first = relative.parts[0]
        return first.split("-")[0].lower()
    return "foundry"


def _title(path: Path) -> str:
    return path.stem.replace("_", " ").replace("-", " ").strip().title()


def _read_preview(path: Path) -> tuple[str, bool]:
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return "", False
    raw = path.read_bytes()
    truncated = len(raw) > PREVIEW_LIMIT
    text = raw[:PREVIEW_LIMIT].decode("utf-8", errors="replace")
    return text, truncated


def _claim_from_json(value: Any) -> str:
    if isinstance(value, dict):
        for key in CLAIM_KEYS:
            item = value.get(key)
            if isinstance(item, str) and item.strip():
                return item.strip()
            if isinstance(item, (list, tuple)) and item:
                return "; ".join(str(part) for part in item)
        for child in value.values():
            found = _claim_from_json(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            found = _claim_from_json(child)
            if found:
                return found
    return ""


def _claim_boundary(path: Path, preview: str) -> str:
    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            found = _claim_from_json(json.loads(preview))
            if found:
                return found
        except (json.JSONDecodeError, TypeError):
            pass
    for line in preview.splitlines():
        normalized = line.strip().lstrip("#/*- ").strip()
        if normalized.lower().startswith(("claim boundary", "claim_boundary", "limitations")):
            _, _, remainder = normalized.partition(":")
            if remainder.strip():
                return remainder.strip()
    return "Finite artifact only. Inspect its source record before making a broader scientific claim."


def scan_artifacts(results_root: Path | str) -> list[ArtifactRecord]:
    """Return a stable manifest of supported result artifacts."""
    root = Path(results_root).resolve()
    if not root.exists():
        return []
    records: list[ArtifactRecord] = []
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        relative = path.relative_to(root)
        preview, truncated = _read_preview(path)
        records.append(
            ArtifactRecord(
                path=relative.as_posix(),
                track=_track(relative),
                kind=_kind(path),
                title=_title(path),
                sha256=_sha256(path),
                bytes=path.stat().st_size,
                claim_boundary=_claim_boundary(path, preview),
                preview=preview,
                truncated=truncated,
            )
        )
    return records


def build_manifest(results_root: Path | str) -> dict[str, Any]:
    root = Path(results_root).resolve()
    artifacts = scan_artifacts(root)
    payload = {
        "schema": "gaugegap-foundry-experience/v1",
        "results_root": root.name,
        "artifact_count": len(artifacts),
        "tracks": sorted({item.track for item in artifacts}),
        "kinds": sorted({item.kind for item in artifacts}),
        "artifacts": [asdict(item) for item in artifacts],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["manifest_sha256"] = hashlib.sha256(canonical).hexdigest()
    return payload


def _json_for_script(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).replace("</", "<\\/")


def render_html(manifest: dict[str, Any], *, title: str = "GaugeGap Foundry") -> str:
    data = _json_for_script(manifest)
    safe_title = html.escape(title)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{safe_title} — Experience / Experiment</title>
<style>
:root{{--bg:#050505;--fg:#f5f5f5;--muted:#858585;--line:#262626;--pulse:#fff}}
*{{box-sizing:border-box}} html,body{{margin:0;height:100%;background:var(--bg);color:var(--fg);font:13px ui-monospace,SFMono-Regular,Menlo,monospace}}
button,input,select{{font:inherit;color:inherit;background:#0a0a0a;border:1px solid var(--line)}} button{{padding:.65rem 1rem;cursor:pointer}}
button.active{{background:var(--fg);color:var(--bg)}} #top{{position:fixed;z-index:8;inset:0 0 auto 0;display:flex;align-items:center;gap:.5rem;padding:12px;border-bottom:1px solid var(--line);background:#050505ee;backdrop-filter:blur(10px)}}
#brand{{font-weight:700;letter-spacing:.18em;margin-right:auto}} #status{{color:var(--muted)}}
#field{{position:fixed;inset:0;width:100%;height:100%;opacity:.42;pointer-events:none}}
main{{position:relative;z-index:2;height:100%;padding-top:58px}}
#experience{{height:100%;display:grid;grid-template-columns:minmax(0,1fr) 320px}}
#stage{{display:grid;place-items:center;overflow:hidden;padding:4vw}} #stage svg{{max-width:90%;max-height:80vh}} #stage pre{{max-width:92%;max-height:76vh;overflow:hidden;white-space:pre-wrap;font-size:clamp(10px,1.1vw,17px);line-height:1.35}}
#sceneMeta{{border-left:1px solid var(--line);padding:24px;display:flex;flex-direction:column;gap:20px;background:#050505d9}} .label{{color:var(--muted);font-size:10px;letter-spacing:.15em;text-transform:uppercase}} .hash{{word-break:break-all;font-size:10px;color:#aaa}}
#experiment{{display:none;height:100%;grid-template-columns:310px 1fr 340px}} #list{{border-right:1px solid var(--line);overflow:auto}} #filters{{position:sticky;top:0;background:#050505;padding:12px;border-bottom:1px solid var(--line)}} #filters input{{width:100%;padding:.7rem}}
.item{{padding:12px;border-bottom:1px solid #171717;cursor:pointer}} .item:hover,.item.active{{background:#111}} .item small{{display:block;color:var(--muted);margin-top:4px}}
#inspect{{padding:24px;overflow:auto}} #inspect pre{{white-space:pre-wrap;word-break:break-word;line-height:1.45}} #evidence{{padding:24px;border-left:1px solid var(--line);overflow:auto}} .metric{{font-size:28px;margin:.2rem 0 1rem}} .claim{{line-height:1.5;border-left:2px solid var(--fg);padding-left:12px}}
#empty{{color:var(--muted)}} @media(max-width:900px){{#experience{{grid-template-columns:1fr}}#sceneMeta{{position:absolute;right:0;bottom:0;width:min(100%,420px);border:1px solid var(--line)}}#experiment{{grid-template-columns:1fr}}#list,#evidence{{display:none}}}}
</style></head><body>
<canvas id="field"></canvas>
<div id="top"><div id="brand">GAUGEGAP / FOUNDRY</div><button id="experienceBtn" class="active">EXPERIENCE</button><button id="experimentBtn">EXPERIMENT</button><button id="playBtn">PAUSE</button><span id="status"></span></div>
<main><section id="experience"><div id="stage"></div><aside id="sceneMeta"></aside></section>
<section id="experiment"><div id="list"><div id="filters"><input id="search" placeholder="filter path, track, kind"></div><div id="items"></div></div><div id="inspect"></div><aside id="evidence"></aside></section></main>
<script>
const manifest={data}; const artifacts=manifest.artifacts||[]; let index=0,playing=true,timer=null,selected=null;
const $=id=>document.getElementById(id), escapeHtml=s=>String(s).replace(/[&<>\"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}}[c]));
function pretty(a){{if(a.path.endsWith('.json')){{try{{return JSON.stringify(JSON.parse(a.preview),null,2)}}catch(e){{}}}}return a.preview}}
function drawScene(){{if(!artifacts.length){{$('stage').innerHTML='<div id="empty">No supported result artifacts found.</div>';$('sceneMeta').innerHTML='';return}}
 const a=artifacts[index%artifacts.length]; let body;if(a.kind==='visual'&&a.preview.includes('<svg'))body=a.preview;else body='<pre>'+escapeHtml(pretty(a).slice(0,16000))+'</pre>';
 $('stage').innerHTML=body;$('sceneMeta').innerHTML=`<div><div class="label">scene ${{index+1}} / ${{artifacts.length}}</div><h2>${{escapeHtml(a.title)}}</h2><div>${{escapeHtml(a.path)}}</div></div><div><div class="label">track / kind</div><div>${{escapeHtml(a.track)}} / ${{escapeHtml(a.kind)}}</div></div><div><div class="label">claim boundary</div><div class="claim">${{escapeHtml(a.claim_boundary)}}</div></div><div><div class="label">sha256</div><div class="hash">${{a.sha256}}</div></div>`;$('status').textContent=`${{manifest.artifact_count}} artifacts · ${{manifest.manifest_sha256.slice(0,12)}}`;}}
function schedule(){{clearInterval(timer);if(playing)timer=setInterval(()=>{{index=(index+1)%Math.max(1,artifacts.length);drawScene()}},5200)}}
function setMode(mode){{const exp=mode==='experience';$('experience').style.display=exp?'grid':'none';$('experiment').style.display=exp?'none':'grid';$('experienceBtn').classList.toggle('active',exp);$('experimentBtn').classList.toggle('active',!exp);}}
function renderList(){{const q=$('search').value.toLowerCase();const rows=artifacts.filter(a=>(a.path+' '+a.track+' '+a.kind).toLowerCase().includes(q));$('items').innerHTML=rows.map(a=>`<div class="item" data-path="${{escapeHtml(a.path)}}"><b>${{escapeHtml(a.title)}}</b><small>${{escapeHtml(a.path)}} · ${{a.kind}}</small></div>`).join('');document.querySelectorAll('.item').forEach(el=>el.onclick=()=>selectArtifact(el.dataset.path));}}
function selectArtifact(path){{selected=artifacts.find(a=>a.path===path);if(!selected)return;document.querySelectorAll('.item').forEach(el=>el.classList.toggle('active',el.dataset.path===path));let body=selected.kind==='visual'&&selected.preview.includes('<svg')?selected.preview:'<pre>'+escapeHtml(pretty(selected))+'</pre>';$('inspect').innerHTML=`<h1>${{escapeHtml(selected.title)}}</h1>${{body}}`;$('evidence').innerHTML=`<div class="label">track</div><div class="metric">${{escapeHtml(selected.track)}}</div><div class="label">kind</div><div class="metric">${{escapeHtml(selected.kind)}}</div><div class="label">bytes</div><div class="metric">${{selected.bytes}}</div><div class="label">claim boundary</div><p class="claim">${{escapeHtml(selected.claim_boundary)}}</p><div class="label">sha256</div><p class="hash">${{selected.sha256}}</p>${{selected.truncated?'<p>Preview truncated; inspect the original artifact for the complete record.</p>':''}}`;}}
$('experienceBtn').onclick=()=>setMode('experience');$('experimentBtn').onclick=()=>{{setMode('experiment');renderList();if(!selected&&artifacts[0])selectArtifact(artifacts[0].path)}};$('playBtn').onclick=()=>{{playing=!playing;$('playBtn').textContent=playing?'PAUSE':'PLAY';schedule()}};$('search').oninput=renderList;
addEventListener('keydown',e=>{{if(e.key==='e')setMode('experience');if(e.key==='x'){{$('experimentBtn').click()}}if(e.key===' '){{$('playBtn').click();e.preventDefault()}}if(e.key==='ArrowRight'){{index=(index+1)%Math.max(1,artifacts.length);drawScene()}}if(e.key==='ArrowLeft'){{index=(index-1+Math.max(1,artifacts.length))%Math.max(1,artifacts.length);drawScene()}}}});
const canvas=$('field'),ctx=canvas.getContext('2d'),seed=manifest.manifest_sha256||'0';let tick=0;function field(){{canvas.width=innerWidth*devicePixelRatio;canvas.height=innerHeight*devicePixelRatio;ctx.fillStyle='#050505';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.fillStyle='#fff';const n=Math.min(800,100+artifacts.length*18);for(let i=0;i<n;i++){{const v=parseInt(seed[(i*7)%seed.length],16)||0;const x=((i*83+tick*(1+v*.08))%canvas.width);const y=((i*i*17+v*97)%canvas.height);ctx.globalAlpha=.08+(v/15)*.35;ctx.fillRect(x,y,1+(v%3),1+(v%3));}}tick+=.55;requestAnimationFrame(field)}}
drawScene();schedule();field();
</script></body></html>'''


def build_experience(
    results_root: Path | str,
    output_path: Path | str,
    *,
    title: str = "GaugeGap Foundry",
    strict: bool = False,
) -> dict[str, Any]:
    """Build the offline interface and return its deterministic manifest."""
    manifest = build_manifest(results_root)
    if strict and not manifest["artifact_count"]:
        raise RuntimeError(f"no supported artifacts found under {Path(results_root)}")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html(manifest, title=title), encoding="utf-8", newline="\n")
    manifest_path = output.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return manifest
