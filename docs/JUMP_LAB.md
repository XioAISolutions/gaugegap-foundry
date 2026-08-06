# GaugeGap Jump Lab v0.5 — Sealed challenge benchmarks

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

## Training worlds

The Einstein elevator and force/mass cart remain the two training environments:

```bash
gaugegap-jump-lab --out artifacts/elevator.eja.json
gaugegap-jump-cart --out artifacts/cart.eja.json
```

Only bounded attention associations may transfer between worlds. Hidden state,
model mappings, scores, candidate axioms, and verifier verdicts are excluded.

## Blinded pendulum holdout

The v0.4 holdout remains available:

```bash
gaugegap-jump-pendulum \
  --out artifacts/pendulum-holdout.eja.json \
  --html artifacts/pendulum-holdout.html

gaugegap-jump-holdout \
  --out-dir artifacts/jump-lab-holdout \
  --report artifacts/jump-lab-holdout.json \
  --html artifacts/jump-lab-holdout.html
```

The agent sees anonymous model IDs and prediction fingerprints, not semantic
statements or the hidden model-to-ID mapping. This is pre-registered model
selection, not open-ended hypothesis invention.

## Sealed answerable and none-of-the-above challenge

v0.5 adds two committed case types:

- `ratio_supported`: the pre-registered length/gravity-ratio model is adequate;
- `hybrid_no_fit`: one controlled sensor perturbation creates mutually
  inconsistent evidence, so no model in the deck clears the evidence and margin
  gates.

Before execution, the evaluator commits to both the hidden case specification
and expected answer using canonical SHA-256 hashes. The agent sees neither. After
submission, the evaluator reveals the case and answer payloads so reviewers can
recompute both commitments.

```bash
gaugegap-jump-challenge \
  --out-dir artifacts/jump-lab-challenge \
  --report artifacts/jump-lab-challenge.json \
  --html artifacts/jump-lab-challenge.html
```

For every seed, the suite runs both case types under:

1. cold salience;
2. attention memory trained through elevator and cart;
3. fixed intervention ordering.

The report measures:

- answerable-case selection accuracy;
- none-of-the-above abstention accuracy;
- false-discovery rate on no-fit cases;
- policy coverage;
- selection margin;
- experiments required;
- cold/warm/fixed policy comparisons;
- commitment validity;
- parent-artifact lineage.

A no-fit run records:

```json
{
  "candidate_axiom": null,
  "metrics": {
    "abstained": true,
    "selected_outcome": "abstain",
    "false_discovery": false
  },
  "verification": {
    "verdict": "not_evaluated_due_to_abstention"
  }
}
```

The reference verifier may be retained for evaluator review, but it is explicitly
withheld from selection and cannot authorize a candidate axiom after abstention.

## Commitment verification

Python callers can independently recompute the sealed commitments:

```python
from gaugegap.jump_lab import verify_challenge_commitments

checks = verify_challenge_commitments(artifact)
assert all(checks.values())
```

The challenge artifact records separate hashes for:

- hidden case specification;
- hidden expected answer;
- submitted selection and evidence references;
- complete EJA artifact.

## CRUMB review workflow

```bash
crumblm eja validate-pack artifacts/jump-lab-challenge
crumblm eja audit-pack artifacts/jump-lab-challenge
crumblm eja evidence-pack artifacts/jump-lab-challenge
crumblm eja challenge-pack artifacts/jump-lab-challenge \
  --out artifacts/eja-challenge-audit.json \
  --html artifacts/eja-challenge-audit.html
crumblm eja bundle-pack artifacts/jump-lab-challenge \
  --out artifacts/eja-review-bundle.zip
```

## Earlier suites

```bash
gaugegap-jump-suite
gaugegap-jump-benchmark
```

## Honest claim boundary

v0.5 demonstrates replayable selection and calibrated abstention over a sealed,
hand-authored deterministic challenge family. It improves resistance to answer
leakage and false axiom compilation. It does **not** establish open-ended machine
abduction, autonomous invention of scientific hypotheses, real-world physical
validity, general cross-domain transfer, or broad SNN superiority.
