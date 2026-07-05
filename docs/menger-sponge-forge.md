# Menger Sponge Forge

Menger Sponge Forge is a finite topology/fractal benchmark.  It turns the
classic Menger sponge construction into a reproducible artifact that can be
visualized, checked, and folded into Deep Boil without claiming a new topology
theorem.

## Core Model

The unit `menger-0001` evaluates construction stages:

1. start with one cube;
2. divide each retained cube into a 3 by 3 by 3 grid;
3. remove the center cube and the six face-center cubes;
4. repeat on the retained cubes.

For finite stage `n`, the runner records:

- retained cubes: `N_n = 20^n`;
- grid width: `3^n`;
- volume: `V_n = (20/27)^n`;
- surface area: `A_n = 2*(20/9)^n + 4*(8/9)^n`;
- dimension estimate: `log(20)/log(3)`.

The artifact exposes the intuition gap: volume trends down, surface area trends
up, and the Hausdorff dimension lies between 2 and 3 even though the ideal limit
is usually discussed as a one-dimensional universal curve in the topological
sense.

The runner also exports a compact `voxels.csv` sample from the final finite
stage.  A voxel survives exactly when, at every ternary digit level, no two of
its local `x,y,z` digits are simultaneously the center digit `1`.  This is a
geometry handoff for visualization or 3D-model experiments, not a full mesh of
the ideal limit object.

## Why This Fits Foundry

GaugeGap already treats "gap" as a finite, claim-bounded separation signal.  The
Menger sponge contributes a topology gap:

- apparent dimension vs measured fractal dimension;
- finite volume collapse vs finite surface growth;
- visual 3D cube intuition vs limit-object boundary language.

This gives the Experience a rigorous way to discuss hidden structure without
turning compactification, perception, or quantum analogies into loose metaphor.

## Claim Boundary

Allowed language:

- finite Menger sponge stage benchmark;
- volume decreases over registered stages;
- surface area increases over registered stages;
- finite dimension estimate matches `log(20)/log(3)`;
- exported voxel sample follows the ternary retention rule;
- topological-dimension statement is a literature boundary.

Avoid:

- proof of the ideal Menger sponge's topological dimension;
- claim that a finite stage has zero volume or infinite surface area;
- claim that this is a physical material design;
- claim that fractal topology proves hidden dimensions.

## Run

```bash
python scripts/run_menger_sponge_forge.py --iterations 4 --output-dir /tmp/menger-0001
```

The script emits `summary.json`, `stages.csv`, `ledger.jsonl`, and
`voxels.csv`, and `menger_sponge_forge.svg`.
