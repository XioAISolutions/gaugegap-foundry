# Lottery Forge

Lottery Forge is a verification-first experiment for studying apparent structure in historical lottery draws without turning post-hoc patterns into prediction claims.

## Three questions kept separate

1. **Historical structure** — does a declared subset, pair pattern, or temporal statistic look unusual versus a fair independent-draw null?
2. **Prediction** — does a deterministic rule trained only on earlier draws beat random valid picks on strictly later holdouts?
3. **Sharing-risk heuristics** — if a person chooses to play anyway, which combinations look less conventional under an explicit human-selection proxy?

A result in question 1 does not imply question 2. Question 3 never changes draw probability.

## Implemented analyses

- per-number frequency and finite-sample z-scores;
- pre-declared Fibonacci-subset Monte Carlo test;
- all-pair co-occurrence scan with exact binomial upper tails and Benjamini-Hochberg FDR correction;
- temporal-order test using maximum lag-1 correlation and whole-draw permutation controls;
- DMD/Koopman one-step reconstruction diagnostic compared against shuffled draw order;
- strict walk-forward backtests for frequency, cold-frequency, recency, and hybrid rules;
- deterministic sampled or exhaustive candidate search;
- anti-crowd proxy, historical-neutrality score, and optional measured-popularity proximity penalty;
- content-hashed proofpacks with a hard claim boundary.

## Fair-null smoke test

```bash
foundry run lottery-forge-smoke
```

Or directly:

```bash
python scripts/run_lottery_forge.py \
  --demo-draws 220 \
  --null-trials 2000 \
  --dmd-trials 64 \
  --candidate-samples 100000 \
  --popular-combinations data/lottery/olg_649_popular_2025-05-25_2026-05-25.csv \
  --output-dir results/lottery-forge-null
```

A fair-null run should normally fail the predictive evidence gate. Individual small exploratory p-values can still appear when many statistics are inspected; pair scans therefore report BH-corrected q-values.

## Historical 6/49 input

Prepare a CSV with one row per draw:

```text
date,n1,n2,n3,n4,n5,n6
2026-08-15,4,12,19,27,33,46
...
```

Then run:

```bash
python scripts/run_lottery_forge.py \
  --input data/lotto649.csv \
  --number-columns n1,n2,n3,n4,n5,n6 \
  --date-column date \
  --pool-size 49 \
  --pick-count 6 \
  --null-trials 10000 \
  --dmd-trials 256 \
  --candidate-samples 500000 \
  --popular-combinations data/lottery/olg_649_popular_2025-05-25_2026-05-25.csv \
  --windows 26,52,104 \
  --output-dir results/lottery-forge-649
```

Outputs:

- `analysis.json` — full diagnostics;
- `proofpack.json` — same result with SHA-256 content hash;
- `summary.md` — concise verdict and candidate heuristics.

## Predictive gate

The initial gate requires both:

- empirical holdout p-value `< 0.01` versus random valid picks; and
- mean holdout hits greater than the fair-draw expectation.

A serious predictive claim would need more than this gate: pre-registration, correction for the number of models/windows tried, a fresh untouched future holdout, and replication.

## Crowd model

The baseline anti-crowd score is a transparent behavioural proxy. It penalizes birthday-heavy, Fibonacci/lucky-number-heavy, round-number, repeated-last-digit and simple-progression choices. Consecutive pairs get a small credit because people often avoid them even though fair draws do not. The scorer also penalizes the simplistic `all numbers above 31` strategy so the optimizer cannot merely rediscover one obvious rule.

The bundled OLG snapshot contains the ten most-played LOTTO 6/49 combinations published for May 25, 2025 through May 25, 2026. When supplied, Lottery Forge applies a soft penalty for exact or near-exact overlap with those measured popular combinations. Because OLG publishes a top list rather than the complete ticket-selection distribution, this remains a bounded heuristic rather than an estimate of true ticket popularity.

Crowd data is never used as evidence that any number is more or less likely to be drawn.

## Claim boundary

Every valid six-number LOTTO 6/49 combination has the same draw probability in a fair draw. Lottery Forge is designed to falsify apparent patterns first and to keep anti-sharing heuristics separate from prediction.

## Next upgrades

- ingest a source-hashed official WCLC/OLG historical draw dataset;
- add exact feature-distribution controls for sums, gaps, parity and clustering;
- add model-family multiple-testing correction to the predictive gate;
- pre-register candidate rules before a sealed future holdout;
- replace top-list crowd calibration with fuller measured ticket-selection data if a defensible dataset becomes available;
- benchmark sampled candidate search against exhaustive enumeration of all 13,983,816 6/49 combinations.
