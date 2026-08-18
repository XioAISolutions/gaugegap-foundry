# Lottery Forge

Lottery Forge is a verification-first experiment for studying apparent structure in LOTTO 6/49 history without turning post-hoc patterns into prediction claims.

## Three questions kept separate

1. **Historical diagnostics** — Fibonacci counts, number frequencies, pair co-occurrence, temporal ordering, and DMD/Koopman structure are compared with fair-draw or shuffled-order nulls.
2. **Prediction tests** — deterministic rules are trained only on earlier draws and scored on strictly later draws. The gate corrects across every tested model/window combination.
3. **Anti-crowd heuristics** — if someone plays anyway, combinations are ranked against explicit human-choice features and OLG's published top combinations. This is a sharing-risk heuristic only.

A result in (1) cannot open the predictive gate. By default (3) has `--neutrality-weight 0`, so historical winning-number frequencies do not leak into candidate ranking.

## Ready-to-run commands

Fair-null smoke test:

```bash
foundry run lottery-forge-smoke
```

Official WCLC two-calendar-year run:

```bash
foundry run lottery-forge-649-live
```

Equivalent direct command:

```bash
python scripts/run_lottery_forge.py \
  --wclc-live \
  --years 2 \
  --null-trials 5000 \
  --dmd-trials 128 \
  --candidate-samples 250000 \
  --windows 26,52,104 \
  --compare 32,37,41,43,47,49 \
  --output-dir results/lottery-forge-649
```

Lottery Forge fetches two official WCLC surfaces: the since-inception print/PDF historical snapshot and the current LOTTO 6/49 winning-numbers page. The current page supplements the snapshot so monthly publication lag does not silently omit the newest draws. Both raw payloads are SHA-256 hashed; parse counts and resolved date interval are embedded in the report.

## Validated two-year reference run

The dedicated GitHub Actions lane has successfully completed a live WCLC run on the PR implementation using 2,000 null trials, 64 DMD permutations, a deterministic 100,000-candidate anti-crowd sample, and 26/52/104-draw holdout windows.

The validated snapshot contained **208 Classic draws from 2024-08-17 through 2026-08-15**. Results:

- Fibonacci subset null p-value: **0.778611**;
- temporal-order permutation p-value: **0.57921**;
- DMD lower-error permutation p-value: **0.553846**;
- pairs surviving BH q < 0.05: **0**;
- strongest tested holdout: **hybrid / 104 draws**, mean hits **0.8269** versus exact chance **0.7347**, raw empirical p **0.122439**, Bonferroni-adjusted p **1.0**;
- predictive evidence gate: **FALSE**;
- top deterministic anti-crowd candidate in that 100,000-combination sample: **9-38-43-44-46-47**;
- reference **32-37-41-43-47-49** ranks substantially worse under the explicit anti-crowd objective used in that run.

The candidate ranking is a sharing-risk heuristic only. It is not evidence that the top candidate is more likely to be drawn.

## Outputs

Every run writes:

- `draws.csv` — normalized exact input used by the analysis;
- `analysis.json` — full diagnostics and source metadata;
- `proofpack.json` — content-hashed result with a hard claim boundary;
- `summary.md` — concise verdict, strongest corrected holdout, candidates, and reference comparisons.

Verify a saved proofpack independently:

```bash
python scripts/verify_lottery_proofpack.py results/lottery-forge-649/proofpack.json
```

## Historical tests

- per-number count and finite-sample z-score;
- pre-declared Fibonacci subset count versus Monte Carlo fair histories;
- all 1,176 pairs with exact binomial upper tails and Benjamini-Hochberg FDR q-values;
- maximum absolute lag-1 correlation versus whole-draw order permutations;
- finite-data DMD/Koopman reconstruction error versus shuffled draw order.

These are diagnostics only.

## Holdout family and gate

Four pre-declared rules are evaluated at each requested window: `frequency`, `cold-frequency`, `recency`, and `hybrid`. For each later draw, a rule sees only its immediately preceding training window. Random valid 6/49 combinations form the null.

The family-wise gate requires both:

1. mean holdout hits above the exact fair expectation `6*6/49`;
2. **Bonferroni-adjusted empirical p < 0.01** across all model/window tests.

A gate pass would still require a newly sealed future holdout and replication. It would not establish a causal mechanism.

## Anti-crowd model

The transparent player-choice proxy audits birthday-heavy selections, Fibonacci/lucky numbers, round numbers, repeated last digits, arithmetic progressions, adjacency, and the simplistic all-above-31 rule. The repository also stores OLG's published top 10 LOTTO 6/49 combinations for May 25, 2025–May 25, 2026 and applies a soft penalty for exact or near overlap.

OLG publishes only a top list, not the full ticket-choice distribution, so this remains bounded. Crowd data is never used as evidence that a number is more or less likely to be drawn.

Use `--compare` to score a fixed set without treating it as a prediction:

```bash
--compare 32,37,41,43,47,49
```

Use `--candidate-exhaustive` to search all `13,983,816` valid 6/49 combinations. The default deterministic sampled search is faster and records its sample count and seed.

## CSV mode

A custom source can be supplied as:

```text
date,n1,n2,n3,n4,n5,n6,bonus
2026-08-15,1,9,17,34,36,43,24
```

```bash
python scripts/run_lottery_forge.py \
  --input data/lotto649.csv \
  --start-date 2024-08-17 \
  --end-date 2026-08-15 \
  --output-dir results/lottery-forge-csv
```

The input file itself is hashed into source metadata.

## Claim boundary

Every valid six-number combination has equal draw probability under a fair LOTTO 6/49 Classic draw. Lottery Forge is designed to falsify attractive historical stories, test whether a pre-declared rule survives later-draw testing, and separately explore player-choice sharing risk.
