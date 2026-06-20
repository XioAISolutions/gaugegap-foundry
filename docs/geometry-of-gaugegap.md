# Geometry of GaugeGap — exact 2D projections of higher-dimensional structure

A recurring theme in the symmetries this repo works with is **flattening a
higher-dimensional object into an insightful 2D picture**. That is not a metaphor
here — several of the central objects are literally defined in higher dimensions
and their standard pictures are exact projections:

- An **su(3) irrep** lives in a higher-dimensional representation space, but its
  *weights* are vectors in the rank-2 Cartan subalgebra. The octet hexagon and
  decuplet triangle are genuine projections of those weight vectors onto the
  physics `(T3, Y)` plane, with multiplicities computed exactly by **Freudenthal's
  recursion** (e.g. the octet's centre has multiplicity 2 — two states at the same
  weight).
- The **su(3) root system** (A2) is the hexagonal arrangement of the six roots.
- A **Calabi-Yau (Fermat) cross-section** — the surface `z1^n + z2^n = 1` (a real
  2-surface in `C^2 = R^4`) — is the iconic "Calabi-Yau" image, here projected
  `R^4 -> R^3 -> R^2` exactly (Hanson's construction). Calabi-Yau threefolds (real
  dim 6) are how string theory compactifies its extra dimensions; this is the
  classic lower-dimensional cross-section used to picture them.

These are the same idea as a lattice-gauge weight diagram: an exact structure,
honestly projected.

## Generate the figures

```bash
make geometry-figures           # deterministic SVG -> figures/geometry/
make geometry-figures SACRED=1  # + decorative golden-ratio / Vesica overlay
python scripts/generate_geometry_figures.py --sacred-overlay
```

Produces (byte-deterministic, in `figures/geometry/`):
- su(3) weight diagrams: `su3_fundamental_weight.svg`, `su3_octet_weight.svg`,
  `su3_decuplet_weight.svg`; the `su3_root_system.svg`;
- the **su(2) weight ladder** (`su2_weight_ladder.svg`) and the **su(4) root
  system** (`su4_root_system.svg`) — the rank-1 and rank-3 cases of the same
  A_{N-1} construction (closed under the S_N Weyl group);
- **`lattice_wilson_loop.svg`** — a 3D cubic lattice projected to 2D with a
  highlighted closed **Wilson loop** (geometry only);
- `calabi_yau_cross_section.svg`;
- `geometry_data.json` (exact weights/roots + symmetry invariants);
- **discharged symmetry certificates** `weight_symmetry_<rep>.lean` / `.coq` +
  `weight_symmetry_certificates.json` (see below).

## Exact topology: Calabi-Yau Hodge diamond + Dynkin/Cartan

`visualization/topology.py` carries standard exact invariants:
- the **Fermat quintic** Hodge diamond (`h^{1,1}=1`, `h^{2,1}=101`), with verified
  Hodge symmetry, **Euler characteristic χ = −200**, and Betti numbers
  `[1,0,1,204,1,0,1]` (`calabi_yau_hodge_diamond.svg`, `topology_data.json`);
- the A_{N-1} **Cartan matrix** and **Dynkin diagram** behind the weight diagrams
  (`su4_dynkin_diagram.svg`). The "generations ~ |χ|/2" remark is the standard
  string-compactification heuristic, labelled as such — not a result of this repo.

## Verified symmetry invariant (the "prove" layer)

The weight diagram's balance is a *first-class verified claim*, in the same honest
style as the separation proofs: in the sum-zero R^3 embedding each weight
coordinate is a multiple of 1/3, so the multiplicity-weighted balance
`Σ mult·(3·coord) = 0` is an **exact integer identity**, emitted as discharged
Lean 4 (`norm_num`) and Coq (`lia`) proofs (no holes, no floating point). The
S_N Weyl-orbit closure is reported with a witness. `gaugegap.visualization.
weight_certificate.weight_symmetry_certificate(p, q)` returns these.

## Interactive explorer (flatten the higher-dimensional form)

`make geometry-figures` (or `python scripts/generate_geometry_html.py`) also writes
`figures/geometry/geometry_explorer.html` — a **self-contained, dependency-free**
page (vanilla JS + `<canvas>`, no CDN). Drag to rotate the exact 3D structure and
pull the **flatten** slider to collapse it to its exact 2D shadow:

- the su(3) octet/decuplet weights lie on a plane in the sum-zero R^3 embedding, so
  flattening to `(T3, Y)` is exact;
- the Calabi-Yau Fermat cross-section flattens from its R^3 projection to a 2D
  shadow.

This realises the "rotate the higher-dimensional form, watch it flatten" idea for
outreach/dashboards, with no Python runtime dependency and byte-deterministic
output. (We deliberately avoid matplotlib/plotly/manim here to keep the core
dependency-light and the artifacts reproducible.)

## Library

```python
from gaugegap.visualization.weight_diagrams import su3_weights, su3_dimension
ws = su3_weights(1, 1)            # octet: exact weights + multiplicities
sum(w["mult"] for w in ws)        # == su3_dimension(1, 1) == 8
from gaugegap.visualization.cy_projection import fermat_patches, orthographic
```

## Claim boundary

The weight diagrams and the Fermat cross-section are **faithful projections of
exact mathematical objects** (su(3) representation theory; an algebraic surface) —
nothing here is a new physical claim. The golden-ratio / Vesica-Piscis overlays
(`--sacred-overlay`) are **decorative aesthetic motifs only**, clearly labelled as
such in code and output; they carry no mathematical meaning. This layer is
inspirational-visualisation and outreach, kept strictly separate from the repo's
verified results, and the claim-boundary audit stays at 0 high.
