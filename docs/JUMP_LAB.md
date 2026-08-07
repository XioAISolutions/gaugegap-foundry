# GaugeGap Jump Lab v0.7 — Finite-grammar symbolic synthesis

Jump Lab remains an experimental **E → J → A → S** lane beside GaugeGap's
verification-first infrastructure. Earlier releases added hidden-cause worlds,
blinded model selection, abstention, sealed commitments, and frozen threshold
calibration. v0.7 changes the hypothesis step itself.

## What changes in v0.7

The v0.4-v0.6 pendulum lane selected among a pre-registered set of complete
prediction models. The new synthesis lane does **not** receive a complete model
deck. Instead, it receives a committed finite grammar:

```text
variables: x, z
response:  y
form:      C * x^a * z^b
exponents: {-2, -1, -0.5, 0, 0.5, 1, 2}
operators: multiply, power
```

The system dynamically generates the Cartesian product of exponent primitives,
fits the multiplicative constant from measurements, ranks the generated
expressions by empirical fit and complexity, and either compiles the best
expression into a scoped candidate axiom or abstains.

This is deliberately described as **bounded symbolic synthesis**. The grammar is
hand-authored and finite, so this is stronger than selecting a fixed list of full
models but still not open-ended hypothesis invention.

## Run the synthesis suite

```bash
gaugegap-jump-synthesize \
  --calibration-seeds 3101,3102,3103,3104 \
  --test-seeds 3201,3202,3203,3204,3205 \
  --max-false-discovery-rate 0 \
  --out-dir artifacts/jump-lab-synthesis \
  --report artifacts/jump-lab-synthesis/synthesis-suite.json \
  --html artifacts/jump-lab-synthesis/synthesis-suite.html
```

## Calibration targets

The synthesis threshold is calibrated only on:

- `linear_ratio`: exponent pair `(1, -1)`;
- `inverse_square`: exponent pair `(1, -2)`;
- `calibration_no_fit`: a mild piecewise perturbation that no single grammar
  expression exactly represents.

The calibration records include the best generated expression, its score, the
runner-up margin, target reveal, and canonical record hash. A deterministic grid
chooses score and margin thresholds under the configured false-discovery limit.
The complete threshold decision is then committed and frozen before test runs.

## Held-out synthesis targets

The unseen test split contains:

- `sqrt_ratio_holdout`: exponent pair `(0.5, -0.5)`;
- `inverse_product_holdout`: exponent pair `(-0.5, -0.5)`;
- `test_no_fit`: a separate piecewise perturbation requiring abstention.

The positive held-out exponent pairs are absent from the calibration target
pairs. They are discoverable only because their primitive exponent tokens are
present in the committed grammar.

For each positive case, the desired behavior is:

```text
measurements
    ↓
generate 49 candidate exponent pairs from grammar primitives
    ↓
fit C independently for every candidate
    ↓
rank by fit, then complexity
    ↓
recover held-out exponent pair
    ↓
compile scoped scaling-law axiom
    ↓
verify on deterministic points not used for fitting
```

For the no-fit case:

```text
best generated expression fails frozen acceptance gate
    ↓
abstain
    ↓
candidate_axiom = null
    ↓
verification = not_evaluated_due_to_abstention
```

## Commitments and provenance

Every synthesis artifact records:

- grammar payload and grammar SHA-256 commitment;
- hidden case commitment;
- hidden target commitment;
- `target_visible_to_agent: false`;
- `target_expression_pre_registered: false`;
- all generated candidates and their fitted scores;
- the frozen synthesis threshold and its calibration commitment;
- whether the selected exponents exactly match the post-run target reveal;
- deterministic verifier results on held-out probe points;
- canonical artifact hash.

Python callers can recompute the suite commitment:

```python
from gaugegap.jump_lab import verify_synthesis_commitment

assert verify_synthesis_commitment(report)
```

## Earlier lanes remain available

```bash
gaugegap-jump-lab
gaugegap-jump-cart
gaugegap-jump-pendulum
gaugegap-jump-holdout
gaugegap-jump-challenge
gaugegap-jump-calibrate
gaugegap-jump-suite
gaugegap-jump-benchmark
```

Those lanes remain useful controls because they separate model selection,
calibrated abstention, attention ordering, and symbolic synthesis rather than
mixing every capability into one benchmark.

## CRUMB review workflow

```bash
crumblm eja validate-pack artifacts/jump-lab-synthesis
crumblm eja audit-pack artifacts/jump-lab-synthesis
crumblm eja evidence-pack artifacts/jump-lab-synthesis
crumblm eja synthesis-pack artifacts/jump-lab-synthesis \
  --suite artifacts/jump-lab-synthesis/synthesis-suite.json \
  --out artifacts/jump-lab-synthesis/synthesis-audit.json \
  --html artifacts/jump-lab-synthesis/synthesis-audit.html
```

## Honest claim boundary

v0.7 demonstrates deterministic generation and evaluation of symbolic power-law
expressions inside a finite committed grammar, including recovery of exponent
combinations not used as calibration targets and abstention when no generated
expression adequately fits. It does **not** demonstrate unrestricted symbolic
reasoning, autonomous invention of new operators or variables, causal discovery
from arbitrary real-world data, or open-ended scientific hypothesis invention.
