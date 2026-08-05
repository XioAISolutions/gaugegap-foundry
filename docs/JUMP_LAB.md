# GaugeGap Jump Lab v0.4 — Blind holdout benchmarks

Jump Lab adds an experimental **E → J → A → S** path beside GaugeGap's
verification-first infrastructure:

1. **Experience:** black-box worlds expose sensor readings and controllable
   interventions while causal state remains hidden from the executive.
2. **Jump:** an auditable executive preserves competing explanations or, in the
   holdout lane, selects among anonymous pre-registered prediction models.
3. **Axiom:** a winning explanation is compiled into an explicitly scoped,
   falsifiable machine-readable candidate only after evidence gates are met.
4. **Systematic deduction:** a deterministic verifier sweeps the candidate's
   stated scope and separately probes an excluded boundary.
5. **Salience:** a lightweight spiking controller ranks attention. It can retain
   bounded semantic preferences, but it never determines truth.

## Training worlds

### Einstein Elevator

Two hidden causes—uniform gravity and upward frame acceleration—produce matching
local mechanical readings.

```bash
gaugegap-jump-lab \
  --out artifacts/elevator.eja.json \
  --html artifacts/elevator.html \
  --memory-out artifacts/elevator-memory.json
```

### Force/Mass Cart

Two carts have different hidden force and mass values but the same initial
force-to-mass ratio.

```bash
gaugegap-jump-cart \
  --out artifacts/cart.eja.json \
  --html artifacts/cart.html
```

## Blind pendulum holdout

The new holdout uses two ideal pendulum boxes with different hidden length and
gravity values but matching initial periods. During selection, the executive
sees:

- raw observations;
- permitted interventions;
- anonymous model IDs;
- each model's pre-registered prediction fingerprint.

It does **not** see the semantic model statements, target formula, or hidden
model-to-ID mapping. The mapping is randomized by deterministic seed and hashed.
Semantic statements are revealed only after the run for audit and reporting.

```bash
gaugegap-jump-pendulum \
  --out artifacts/pendulum-holdout.eja.json \
  --html artifacts/pendulum-holdout.html
```

The intervention set includes:

- stable repetition;
- scaling length and gravity together;
- adding the same length to both systems;
- increasing amplitude to cross the small-angle boundary;
- controlled exposure of a latent length sensor.

The candidate axiom states, within the ideal tested small-angle scope, that the
period follows the square root of the length-to-gravity ratio. The verifier also
checks that large amplitude creates a measurable boundary and that equal periods
do not imply identical latent parameters.

This lane is honestly classified as **blinded pre-registered model selection**.
It is not described as open-ended hypothesis invention.

## Cross-world holdout suite

The v0.4 suite runs, for each seed:

1. elevator training with salience;
2. cart training with only bounded semantic salience memory transferred;
3. pendulum holdout with cold salience;
4. pendulum holdout with trained salience memory;
5. pendulum holdout with fixed intervention ordering.

```bash
gaugegap-jump-holdout \
  --out-dir artifacts/jump-lab-holdout \
  --report artifacts/jump-lab-holdout.json \
  --html artifacts/jump-lab-holdout.html
```

The report measures:

- anonymous-model selection accuracy;
- discovery-completion rate;
- experiments required;
- target-language leakage rate;
- cold versus warm experiment savings;
- warm versus fixed-order experiment savings;
- agreement on the post-run semantic model;
- parent-artifact lineage.

Transferred memory contains only bounded attention associations such as
`boundary_probe`, `parameter_probe`, `ratio_probe`, and `repeat_probe`. It
excludes hidden state, candidate statements, model mappings, scores, axioms, and
verifier verdicts.

## Earlier benchmarks

The v0.3 multi-world suite and v0.2 elevator policy benchmark remain available:

```bash
gaugegap-jump-suite
gaugegap-jump-benchmark
```

## CRUMB review workflow

Every run is a CRUMB EJA artifact. A complete review flow is:

```bash
crumblm eja validate-pack artifacts/jump-lab-holdout
crumblm eja audit-pack artifacts/jump-lab-holdout
crumblm eja evidence-pack artifacts/jump-lab-holdout \
  --html artifacts/eja-evidence.html
crumblm eja lineage-pack artifacts/jump-lab-holdout
crumblm eja bundle-pack artifacts/jump-lab-holdout \
  --out artifacts/eja-review-bundle.zip
```

## Honest claim boundary

v0.4 demonstrates a replayable, blinded model-selection benchmark on one new
hand-authored deterministic holdout world. It improves resistance to phrase
leakage and makes evidence references auditable. It does **not** establish
open-ended machine abduction, autonomous invention of scientific hypotheses,
real-world pendulum validation, general cross-domain transfer, or broad SNN
superiority.
