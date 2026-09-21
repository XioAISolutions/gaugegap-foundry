# StyleGap — finite linguistic-screening benchmark

Fourth foundry track, added 2026-09-21. Companion to GaugeGap / FlowGap /
CurveRank, applied to *text* instead of operators: reproducible,
finite-corpus comparison of human-authored vs LLM-generated content.

## Claim boundary

This track provides **finite linguistic screening infrastructure**. It is:

- a finite-corpus benchmark with deterministic splits and bootstrap CIs
- transparent proxy features (explicit open lexicons; LIWC dictionaries are
  proprietary and are NOT shipped)
- a screening protocol, scored corpus-locally

It is **NOT**:

- an AI-text detector product
- evidence that machine-generated text is identifiable in general
- a claim of SOTA detection performance

Reported numbers are local to the supplied corpus. Never describe this as
"solving" machine-text identification.

## Source paper

Rodrigues, F. A., Sturm, C. and Pinheiro, F. L. (2026). *A linguistic
comparison between human- and AI-generated content.* iScience 29, 114976.
doi:10.1016/j.isci.2026.114976 (CC BY). Their protocol: descriptive
metrics, LIWC-category comparisons, SAGE n-gram salience, and a detection
model whose accuracy degrades on LLM text (93% human / 75% AI). StyleGap
implements the protocol shape with open proxies.

## Module and runner

- `src/gaugegap/stylegap_linguistic.py`
  - `document_features(text)` — 9 features per document
  - `relative_difference(human_docs, ai_docs)` — delta% + bootstrap CI (seeded)
  - `ngram_log_odds(docs_a, docs_b, n)` — Monroe-style salience (SAGE proxy)
  - `screening_protocol(human_docs, ai_docs, seed)` — held-out nearest-centroid baseline
- `scripts/run_stylegap_screen.py --output-dir OUT [--input corpus.jsonl]`
  - corpus format: one JSON object per line: {"text": "...", "label": "human"|"ai"}
  - omit `--input` for the built-in demo corpus (protocol smoke only)

## Verification

```bash
python -m pytest tests/test_stylegap_linguistic.py -q
python scripts/run_stylegap_screen.py --output-dir /tmp/stylegap-smoke
```

Outputs `stylegap_report.json` carrying the claim-boundary string and the
paper reference alongside the numbers, consistent with the foundry's
reproducibility conventions.
