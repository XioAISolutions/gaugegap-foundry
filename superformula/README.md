# Superformula track — parametric depth-conditioning pipeline

Reproducible pipeline that turns Gielis superformula parameters (r(θ; m1, n1, n2, n3, a, b)) into
conditioned generative stills and motion loops:

1. **Depth render** — vectorized z-buffer node for ComfyUI (`node/gielis_comfy_node.py`).
2. **Still** — FLUX.1 [dev] with XLabs depth-ControlNet conditioning (`scripts/`).
3. **Motion** — Wan 2.2 i2v drift loops seeded from the stills.

## Claim boundary (track)

Finite parametric-conditioning pipeline for generative imagery. No claims about aesthetic
superiority, general image quality, or comparison against other systems. Examples are
demonstrations of the pipeline, not benchmarks.

## Contents

| Path | Purpose |
|---|---|
| `node/gielis_comfy_node.py` | ComfyUI custom node: superformula → vectorized z-buffer depth map |
| `scripts/gielis_flux_run.py` | Single-shape depth map → FLUX still |
| `scripts/gielis_batch.py` | Batch: multiple shape sets → stills → Wan drift loops (self-healing SSH tunnel client) |
| `scripts/gielis_flux_graph.json` | ComfyUI graph: FLUX + depth ControlNet |
| `scripts/get_depthcn.sh` | Fetch XLabs flux-controlnet-depth-v3 (1.49 GB, 86 tensors) |
| `scripts/gielis_smoke.py` | Standalone smoke check of the depth math |
| `examples/` | 4 sculptures (still + drift loop each), combined reel, first math→image test |

## Run

1. Copy `node/gielis_comfy_node.py` into the target ComfyUI `custom_nodes/` and restart it.
2. Download the depth ControlNet: `bash scripts/get_depthcn.sh`.
3. Render: `python scripts/gielis_flux_run.py` (single) or `python scripts/gielis_batch.py` (batch).

The batch client expects a reachable ComfyUI HTTP endpoint; it opens a loopback tunnel when
configured for a remote host and reconnects on tunnel failure (see `ensure_tunnel`/`tick`).

## Licensing notes

- Pipeline code: same license as this repository.
- Example outputs were produced with **FLUX.1 [dev]** — non-commercial license; examples are
  research/demo artifacts only. Motion: Wan 2.2 i2v.
