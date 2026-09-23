# Superformula track — parametric depth-conditioning pipeline

Reproducible pipeline that turns Gielis superformula parameters (r(θ; m1, n1, n2, n3, a, b)) into
conditioned generative stills and motion loops:

1. **Depth render** — z-buffer node for ComfyUI (`node/gielis_comfy_node.py`).
2. **Still** — FLUX.1 [dev] with XLabs depth-ControlNet conditioning (`scripts/`).
3. **Motion** — Wan 2.2 i2v drift loops seeded from the stills.

## What the parameters control today

**Frame one, and nothing after it.** The batch renders a single depth frame
(`frames=1`), conditions one FLUX still on it, and hands that still to Wan 2.2
image-to-video with a text prompt. The video model never sees the parametric
motion, so any rotation in the loops is the model's own. The track's most
distinctive property — exact geometry at every frame — is unused in the video
stage. [`bench/PROTOCOL.md`](bench/PROTOCOL.md) is the pre-registered
experiment for using it (not yet run).

## Renderer: measured defects and the fix

The node now has two modes. `mode="legacy"` reproduces the original renderer
bit for bit (a test asserts it against a verbatim copy), so every published
example stays reproducible. `mode="batch"` is the default.

| | original (`legacy`) | `batch` |
|---|---:|---:|
| depth present on the true silhouette, node defaults (128 samples / 1024 px) | 2.14% | 99.99% |
| same, as the batch script ran it (256 / 1024) | 8.44% | — |
| background distinct from farthest surface | no (both 0) | yes (0 vs 0.08) |
| one depth mapping for the whole sequence | no, per frame | yes |
| one isotropic pixel scale for the whole sequence | no, per axis, per frame | yes |
| rotation read back from its own frames, max error | 0.438°/frame | 0.0032°/frame |

Coverage is measured against a dense (2048-sample) render of the same view.
Two cheaper metrics were tried first and misled in opposite directions — one
counted a star's real concavities as holes, the other counted a sparse dot
cloud as nearly hole-free because the gaps between dots leak to the border.

The batch graph also had a geometry bug of its own: it rendered 1024x1024 and
`ImageScale`d it to 768x1344 with crop disabled, **squashing every shape to
0.571x its width** before FLUX saw it. The node now takes `width`/`height` and
renders at the latent's aspect directly. The batch graph uses it.

New inputs (`mode`, `width`, `height`, `fill_holes`, `surface_floor`) are
optional, so existing graphs load unchanged — but they now get `batch` mode.
To reproduce a published example exactly, use the previous revision of the
graph and set `mode="legacy"`.

## Controllability ruler

`bench/controllability.py` reads parameters back out of silhouettes: the lobe
count `m` (angular harmonics about the centroid, after covariance whitening,
which undoes any linear stretch of the view) and rotation per frame (phase of
harmonic `m`). It abstains rather than guessing.

It was calibrated on clean renders before being pointed at anything else
(`bench/calibrate.py`, results in `bench/results/calibration.json`):
per-pitch abstention thresholds fitted on one split, frozen, and scored on a
disjoint held-out split.

| pitch | 0° | 10° | 20° | 30° | 40° | 50° | 60° |
|---|---:|---:|---:|---:|---:|---:|---:|
| held-out correct (of 30) | 30 | 30 | 23 | 9 | 6 | 6 | 4 |
| abstained | 0 | 0 | 7 | 21 | 24 | 24 | 26 |
| wrong | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Validated domain: **pitch 0–20°**. Above that it stays safe by abstaining but
answers too rarely to be useful: steep views bring the solid's sides into the
outline, a non-linear distortion whitening cannot undo. Before thresholds were
frozen per pitch, the ruler read a 5-lobed shape at 60° as 3-lobed with 0.80
confidence — a negative result retained here because it is the failure a
benchmark instrument must not have.

Rotation read-back is limited to below 180/m degrees per frame; above that the
lobes alias onto their neighbours.

## Contents

| Path | Purpose |
|---|---|
| `node/gielis_comfy_node.py` | ComfyUI node; its numpy core needs no torch or GPU |
| `bench/controllability.py` | read `m` and rotation back from silhouettes |
| `bench/calibrate.py` | frozen-threshold calibration on clean renders |
| `bench/PROTOCOL.md` | the controllability experiment — not yet run |
| `scripts/gielis_flux_run.py` | Single-shape depth map → FLUX still |
| `scripts/gielis_batch.py` | Batch: shapes → stills → Wan drift loops (self-healing SSH tunnel client) |
| `scripts/gielis_flux_graph.json` | ComfyUI graph: FLUX + depth ControlNet |
| `scripts/get_depthcn.sh` | Fetch XLabs flux-controlnet-depth-v3 (1.49 GB, 86 tensors) |
| `scripts/gielis_smoke.py` | Smoke check of the node through ComfyUI |
| `examples/` | 4 sculptures (still + drift loop each), combined reel, first math→image test — rendered with the original renderer |

Tests: `python -m pytest tests/test_superformula_depth.py` (numpy only).

## Run

1. Copy `node/gielis_comfy_node.py` into the target ComfyUI `custom_nodes/` and restart it.
2. Download the depth ControlNet: `bash scripts/get_depthcn.sh`.
3. Render: `python scripts/gielis_flux_run.py` (single) or `python scripts/gielis_batch.py` (batch).

The batch client expects a reachable ComfyUI HTTP endpoint; it opens a loopback tunnel when
configured for a remote host and reconnects on tunnel failure (see `ensure_tunnel`/`tick`).

## Claim boundary (track)

Finite parametric-conditioning pipeline for generative imagery. No claims about aesthetic
superiority, general image quality, or comparison against other systems. The renderer figures
above describe the conditioning signal, not the images generated from it — no generator was run
for this revision. The ruler's accuracy is measured on clean renders only. Examples are
demonstrations of the pipeline, not benchmarks.

## Licensing notes

- Pipeline code: same license as this repository.
- Example outputs were produced with **FLUX.1 [dev]** — non-commercial license; examples are
  research/demo artifacts only. Motion: Wan 2.2 i2v.
