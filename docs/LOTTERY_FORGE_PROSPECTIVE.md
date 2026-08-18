# Lottery Forge 0002 — Prospective Holdout

This lane exists to answer the question the historical analysis cannot answer: **can one frozen rule outperform chance on draws whose outcomes were genuinely unknown when the prediction was sealed?**

## Frozen protocol

Protocol `lottery-forge-0002-prospective-v1` fixes:

- game: LOTTO 6/49 Classic, six numbers from 1–49;
- model: `hybrid`;
- rolling training window: exactly 104 previous official Classic draws;
- output: deterministic top six numbers from that frozen rule;
- decision checkpoints: 26, 52, and 104 scored future draws only;
- family-wise alpha: 0.01;
- correction: Bonferroni across those three checkpoints;
- primary null: exact overlap distribution between a fixed six-number prediction and an independent fair 6-of-49 draw.

No tuning of the model, window, alpha, metric, or checkpoints is permitted until all 104 prospective draws are complete. Any change starts a new protocol ID and cannot inherit evidence from this one.

## No-peeking seal

Each prediction:

1. is generated from WCLC results available before the target draw;
2. must target a later local calendar date than the date on which it is generated;
3. records hashes of the full training data and exact 104-draw window;
4. binds to the hash of the frozen protocol;
5. is committed to the `lottery-forge-prospective-ledger` branch before the outcome exists;
6. is never overwritten. A differing artifact at the same target date causes the workflow to fail.

The Git commit history is the external timestamped seal.

## Automated cadence

The `Lottery Forge Prospective` GitHub Actions workflow runs Tuesday and Friday before the normal Wednesday/Saturday draw schedule. On each run it:

- verifies/scorers any older sealed prediction whose official result now exists;
- generates the next prediction;
- refuses same-day or already-known targets;
- updates the append-only ledger branch;
- recomputes the prospective evaluation;
- uploads the current prediction/evaluation as a workflow artifact.

## Commands

Generate the next prediction manually:

```bash
python scripts/run_lottery_prospective.py predict \
  --output results/lottery-prospective/next.json
```

Verify it:

```bash
python scripts/run_lottery_prospective.py verify \
  --artifact results/lottery-prospective/next.json
```

Score a prediction after the result is published:

```bash
python scripts/run_lottery_prospective.py score \
  --prediction data/lottery/prospective/predictions/YYYY-MM-DD.json \
  --output data/lottery/prospective/scores/YYYY-MM-DD.json \
  --allow-pending
```

## Interpretation

Interim hit counts and p-values are descriptive only. The predictive evidence gate can open only at the three pre-declared checkpoints after family-wise correction. Even a passing checkpoint would warrant independent replication before making a practical prediction claim.
