# Product brief — Verdict (eval-first guardrails for AI claims)

The strongest *product* pivot in this repo: turn the **Verdict** DSL into a small
tool for the AI-evaluation / guardrails market. Honest timeline: a product is
**months**, not asap — this is the roadmap, not a promise of revenue.

## The idea

> A claim about a model is invalid unless a **logged, reproducible eval** backs it.

`assert score(E) >= t` / `assert no_regression(...)` only pass if the eval `E`
measured it; otherwise **the run fails** and the per-case log is the evidence.
Make it a **CI gate**: PRs that assert model quality fail unless the eval proves
it — the same "honest-by-construction" rule this repo applies to numerics.

Seed already built: `src/gaugegap/verdict_lang/` + `docs/verdict-language.md`
(deterministic toy models, hermetic tests).

## Why now / market

LLM teams need trustworthy, reproducible evals and regression gates; "evals" and
guardrails are an active spend area. The differentiator is **enforcement**
(claims fail without evidence) + **auditable logs**, not another dashboard.

> Be honest in any go-to-market: the space is crowded (eval/observability vendors,
> OSS eval harnesses). Win on the narrow, opinionated "fail-closed in CI" wedge —
> do **not** claim traction, customers, or benchmarks you don't have.

## MVP scope (Phase 1)

- Real model adapters (OpenAI / Anthropic / local) behind the existing
  capability-gated pattern — keep a deterministic offline mode for tests.
- Metrics beyond accuracy (F1, exact-match, pass-rate, calibration, cost/latency).
- A **GitHub Action**: run the `.verdict` program, fail the check on an unbacked or
  below-threshold claim, attach the eval log as an artifact.
- `verdict.yaml`/`.verdict` config + a hosted-or-local runner.

## Phased roadmap

1. **MVP** (above) — open-source core, free.
2. **Hosted runner + dashboards** — logged eval history, regression tracking (paid).
3. **Policy/guardrail packs** — safety/PII/regression policy bundles.

## Pricing sketch (placeholder)

- OSS core: free. Hosted/team: **[$/seat or $/run]**. Design-partner pilots first.

## Honest scope

Verdict is general AI-eval tooling; it is unrelated to the RH/quantum science in
this repo and makes no scientific claim. Today's bundled models are toy
demonstrations — productization means real adapters and real evals.

> Blanks: product name/entity, pricing, design partners, hosting plan.
