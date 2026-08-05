# GaugeGap Jump Lab v0.3 — Multi-world E-J-A benchmarks

Jump Lab adds an experimental **E → J → A → S** path beside GaugeGap's
verification-first infrastructure:

1. **Experience:** black-box worlds expose sensor readings and controllable
   interventions while causal state remains hidden from the executive.
2. **Jump:** an auditable abductive executive preserves competing explanations
   and selects discriminating experiments.
3. **Axiom:** a winning explanation is compiled into an explicitly scoped,
   falsifiable machine-readable candidate only after evidence gates are met.
4. **Systematic deduction:** a deterministic verifier sweeps the candidate's
   stated scope and separately probes an excluded boundary.
5. **Salience:** a lightweight spiking controller ranks attention. It can retain
   bounded semantic preferences, but it never determines truth.

## Worlds

### Einstein Elevator

Two hidden causes—uniform gravity and upward frame acceleration—produce matching
local mechanical readings. The executive tests sensor failure, object-specific
forces, hidden uniform forces, and a local reference-frame equivalence. The
candidate remains explicitly local and Newtonian.

```bash
gaugegap-jump-lab \
  --out artifacts/elevator.eja.json \
  --html artifacts/elevator.html \
  --memory-out artifacts/elevator-memory.json
```

### Force/Mass Cart

Two carts have different hidden force and mass values but the same initial
force-to-mass ratio. Their kinematic trajectories match until interventions
change that ratio or expose a latent parameter.

```bash
gaugegap-jump-cart \
  --out artifacts/cart.eja.json \
  --html artifacts/cart.html
```

The scoped candidate states that equal force-to-mass ratios and matched initial
conditions produce equal tested kinematics in the frictionless constant-force
toy model. It does not identify force and mass separately.

## Multi-world suite

The suite runs:

- the elevator task with salience;
- the cart task with cold salience memory;
- the cart task with only semantic attention associations transferred from the
  elevator run;
- a fixed-order cart baseline.

```bash
gaugegap-jump-suite \
  --out-dir artifacts/jump-lab-suite \
  --report artifacts/jump-lab-suite.json \
  --html artifacts/jump-lab-suite.html
```

Transferred memory contains bounded preferences such as `boundary_probe` and
`parameter_probe`. It excludes hidden state, hypothesis scores, candidate
axioms, and verifier verdicts. The suite reports neutral or harmful transfer as
well as improvements; no positive result is assumed.

Each warm cart artifact records the elevator artifact hash as a parent, giving
CrumbLLM enough provenance to construct a discovery lineage graph.

## Salience-memory files

Both direct demonstrations support memory import and export:

```bash
gaugegap-jump-lab --memory-out artifacts/memory.json
gaugegap-jump-cart --memory-in artifacts/memory.json
```

A memory snapshot stores attention associations only. It cannot authorize an
axiom or override evidence gates.

## Single-world policy benchmark

The original paired intervention-ordering test remains available:

```bash
gaugegap-jump-benchmark
```

It compares salience ordering with a fixed order inside the elevator world. The
multi-world suite is a separate test and does not turn the single-world result
into evidence of general SNN superiority.

## CRUMB handoff

Every run is a CRUMB EJA artifact:

```bash
crumblm eja validate artifacts/elevator.eja.json
crumblm eja validate-pack artifacts/jump-lab-suite
crumblm eja audit-pack artifacts/jump-lab-suite
crumblm eja lineage-pack artifacts/jump-lab-suite
```

## Honest claim boundary

v0.3 proves that the same auditable software pattern can be exercised in two
hand-authored deterministic toy worlds. It does **not** recreate historical
scientific discoveries, establish open-ended machine abduction, validate the
candidate axioms in real physical systems, or show that salience transfer will
generalize beyond these benchmarks.
