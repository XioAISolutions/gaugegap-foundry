# Lottery Forge Selection V3

Selection V3 is deliberately separate from the sealed LOTTO 6/49 prospective protocol.
It does not claim to predict fair lottery draws.

The selector ranks valid combinations for estimated human-choice / prize-sharing risk using bounded behavioural proxies and, where available, OLG-published popular-combination data. Broad shape guardrails prevent optimizer artifacts such as selecting every number above the birthday range merely because birthdays are commonly chosen.

The live weekly screen currently covers:

- LOTTO MAX under the current 7-of-52 format beginning April 14, 2026;
- DAILY GRAND main numbers (5 of 49) plus a separately fixed Grand Number heuristic;
- a reminder that the existing sealed LOTTO 6/49 prediction must not be replaced mid-protocol.

Predictive diagnostics remain separate. Frequency, cold-frequency, recency, and hybrid rules are walk-forward tested and family-wise corrected. Their output is not used as the recommended selection unless a predeclared corrected evidence gate passes.

Run:

```bash
python scripts/run_lottery_week.py --output-dir results/lottery-week
```

The runner fetches and hashes official WCLC source material, runs the diagnostic family, performs a deterministic selection search, and writes `lottery_week.json` plus `summary.md`.

## Claim boundary

Every valid combination has the same draw probability in a fair lottery. Selection V3 is an attempt to reduce obvious human-choice overlap and optimizer bias; it cannot make a valid line more likely to be drawn.
