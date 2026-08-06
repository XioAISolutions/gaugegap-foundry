# GaugeGap Jump Lab v0.6 — Frozen calibration and unseen challenge tests

Jump Lab adds an experimental **E → J → A → S** path beside GaugeGap's
verification-first infrastructure:

1. **Experience:** black-box worlds expose sensor readings and controllable
   interventions while causal state remains hidden from the executive.
2. **Jump:** an auditable executive preserves competing explanations or selects
   among anonymous pre-registered prediction models.
3. **Axiom:** a winning explanation is compiled only after evidence, confidence,
   margin, and scope gates are met.
4. **Systematic deduction:** a deterministic verifier tests the candidate inside
   its declared scope and separately probes an excluded boundary.
5. **Salience:** a lightweight spiking controller ranks attention. It can retain
   bounded preferences, but it never determines truth.
6. **Abstention:** when the registered deck does not adequately explain the
   evidence, the executive must return `abstain` rather than inventing support.
7. **Frozen calibration:** selection thresholds are chosen on a disjoint
   calibration split, committed, and frozen before unseen test seeds run.

## Training worlds

The Einstein elevator and force/mass cart remain the two training environments:

```bash
gaugegap-jump-lab --out artifacts/elevator.eja.json
gaugegap-jump-cart --out artifacts/cart.eja.json
```

Only bounded attention associations may transfer between worlds. Hidden state,
model mappings, scores, candidate axioms, answer keys, and verifier verdicts are
excluded.

## Blinded pendulum and sealed challenge lanes

The v0.4 and v0.5 commands remain available:

```bash
gaugegap-jump-pendulum
gaugegap-jump-holdout
gaugegap-jump-challenge
```

The agent sees anonymous model IDs and prediction fingerprints, not semantic
statements or the hidden model-to-ID mapping. The sealed challenge additionally
commits to the hidden case specification and expected answer before execution.
These lanes are pre-registered model selection, not open-ended hypothesis
invention.

## v0.6 disjoint threshold calibration

Earlier suites used hand-selected score and margin gates. v0.6 removes that
researcher degree of freedom.

```bash
gaugegap-jump-calibrate \
  --calibration-seeds 2101,2102,2103,2104 \
  --test-seeds 2201,2202,2203,2204,2205 \
  --max-false-discovery-rate 0 \
  --out-dir artifacts/jump-lab-calibration \
  --report artifacts/jump-lab-calibration/calibration-suite.json \
  --html artifacts/jump-lab-calibration/calibration-suite.html
```

The calibration and test seed sets must be non-empty and disjoint. The suite
calibrates one frozen threshold pair over three case kinds:

- `ratio_supported`: the registered ratio model is adequate;
- `deceptive_no_fit`: one repeat measurement violates the ratio model while its
  raw score remains just above the legacy 0.70 confidence gate;
- `hybrid_no_fit`: stronger mutually inconsistent evidence prevents the deck
  from completing its evidence gates.

The deceptive case makes calibration consequential. A legacy 0.70 gate may
accept a false explanation, while a threshold selected under a zero
false-discovery constraint must reject it without sacrificing the clean positive
case.

## Calibration protocol

For each calibration seed, the system records a raw evidence-complete run and a
canonical record containing:

- expected outcome;
- leading anonymous and semantic model identifiers after reveal;
- top score and runner-up margin;
- evidence-gate completion;
- intervention count;
- source artifact hash;
- record hash.

A deterministic grid evaluates candidate minimum-score and minimum-margin pairs.
The selector then:

1. maximizes calibration accuracy;
2. enforces the configured maximum false-discovery rate;
3. minimizes positive abstention;
4. maximizes coverage;
5. chooses the least restrictive tied threshold.

The complete calibration record hashes, candidate grid, objective, false-
discovery constraint, and selected threshold are committed with SHA-256 before
any test run is executed.

Each test artifact records:

```json
{
  "calibration_protocol": {
    "protocol": "disjoint_frozen_threshold_calibration_v1",
    "split": "test",
    "threshold_frozen_before_test": true,
    "threshold_commitment_hash": "sha256:...",
    "frozen_threshold": {
      "minimum_score": 0.75,
      "minimum_margin": 0.05
    },
    "test_answers_used_for_calibration": false
  }
}
```

The exact selected values are data-dependent; the example above illustrates the
record shape rather than promising a result.

## Test scorecard

The unseen split runs each case under:

1. cold salience;
2. attention memory trained through elevator and cart;
3. fixed intervention ordering.

The report measures:

- overall and answerable accuracy;
- abstention accuracy;
- false-discovery and positive-abstention rates;
- coverage and selective accuracy;
- mean leading-model score;
- frozen-decision reproduction rate;
- coarse empirical reliability bins;
- threshold-commitment validity;
- calibration/test split disjointness.

The reliability table is descriptive. Anonymous-model scores are not asserted to
be calibrated probabilities.

## Python verification

```python
from gaugegap.jump_lab import verify_calibration_commitment

assert verify_calibration_commitment(report)
```

The verifier recomputes the threshold commitment from the calibration seeds,
case kinds, candidate grid, false-discovery constraint, record hashes, selected
threshold, and deterministic selection objective.

## CRUMB review workflow

```bash
crumblm eja validate-pack artifacts/jump-lab-calibration
crumblm eja audit-pack artifacts/jump-lab-calibration
crumblm eja evidence-pack artifacts/jump-lab-calibration
crumblm eja challenge-pack artifacts/jump-lab-calibration
crumblm eja calibration-pack \
  artifacts/jump-lab-calibration/calibration-suite.json \
  --out artifacts/jump-lab-calibration/calibration-audit.json \
  --html artifacts/jump-lab-calibration/calibration-audit.html
crumblm eja bundle-pack artifacts/jump-lab-calibration \
  --out artifacts/jump-lab-calibration/review-bundle.zip
```

## Earlier suites

```bash
gaugegap-jump-suite
gaugegap-jump-benchmark
```

## Honest claim boundary

v0.6 demonstrates frozen threshold selection on a disjoint deterministic
calibration split and evaluation on unseen deterministic seeds. It reduces
post-hoc threshold tuning and directly measures false discoveries versus
coverage. It does **not** establish real-world probability calibration,
open-ended machine abduction, autonomous invention of scientific hypotheses,
physical validity outside the toy worlds, general cross-domain transfer, or
broad SNN superiority.
