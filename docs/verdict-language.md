# Verdict — an eval-first language for honest model claims

Verdict is the AI-side sibling of [Spectra](spectra-language.md). Same philosophy,
different domain: where Spectra makes *certification* first-class, Verdict makes
*evidence* first-class.

Its one rule: **a claim about a model is only valid if a logged, reproducible eval
backs it.** `assert score(E) >= t` can pass only because the eval `E` measured it;
you cannot assert a number you did not run, and `report` writes the full per-case
eval log so the claim is auditable.

> **Scope (binding).** The bundled models are deterministic toy classifiers
> (`src/gaugegap/verdict_lang/models.py`), so every run is hermetic and
> reproducible. Verdict is a demonstration of eval-first semantics — **not** a
> production eval framework, and not a claim about real model quality.

## Example

`examples/sentiment_eval.verdict`:

```
dataset D = cases("examples/sentiment_cases.jsonl")
model   M = keyword_sentiment()
eval    E = run(M, D, metric=accuracy)
assert  score(E) >= 0.8
assert  no_regression(E, baseline=0.75)
report  "results/verdict-demo"
```

Run it:

```bash
python scripts/run_verdict.py examples/sentiment_eval.verdict
```

```
eval E: model=M dataset=D accuracy=1.0000 (8 cases)
assert score(E) >= 0.8: OK (measured 1.0000) -> backed by eval log
report -> results/verdict-demo
```

Swap `keyword_sentiment` for `always_pos` and the score drops to 0.5 — the **same
assertion then fails the program.** That is the point: the language won't let a
model claim outrun its evidence.

## Grammar

One statement per line; `#` starts a comment.

| Statement | Meaning |
|---|---|
| `dataset D = cases("path.jsonl")` | load labelled cases (`{"input":…, "expected":…}` per line) |
| `model M = <name>()` | a registered model (`keyword_sentiment`, `always_pos`, `always_neg`) |
| `eval E = run(M, D, metric=accuracy)` | run the model over the dataset, logging every case |
| `assert score(E) >= t` | pass iff the **measured** score meets `t`, else fail |
| `assert no_regression(E, baseline=b)` | pass iff the measured score ≥ baseline |
| `report "dir"` | write the JSON report + per-case eval log (the evidence) |

## How it relates to Spectra

| | Spectra (quantum/spectral) | Verdict (AI/eval) |
|---|---|---|
| First-class semantic | certification (interval kernel) | evidence (logged eval) |
| A claim is… | `assert separated(M, …)` | `assert score(E) >= t` |
| …backed by | a discharged Lean/Coq certificate | a reproducible per-case eval log |
| Fails when | the kernel can't certify it | the eval doesn't meet the bar |

Both encode the same conviction the rest of this repo enforces by review and CI:
**a claim you can't back is a bug, so make the language refuse it.**

## Metrics

`eval ... metric=<name>` supports `accuracy`, `precision`, `recall`, and `f1`
(macro-averaged over the observed labels). Every eval also records a per-label
breakdown and a confusion matrix in the report as evidence
(`src/gaugegap/verdict_lang/metrics.py`). `assert score(E) >= t` gates on the
chosen metric, so you can require, e.g., F1 rather than raw accuracy.

## Plugging in a real model

The bundled classifiers are deterministic toys, but a real model plugs in behind
the same `Callable[[str], str]` interface:

```python
from gaugegap.verdict_lang import register_model, command_model
register_model("my_llm", lambda text: my_classifier(text))   # any Python callable
register_model("ext", command_model("my-classifier --text {input}"))  # external CLI
```

No provider SDK is imported by the package, so the core stays hermetic and CI-safe.

## CI gate

`scripts/run_verdict.py` exits non-zero on any unbacked or below-threshold claim,
so a `.verdict` program is a drop-in CI gate. The repo ships a composite action
(`.github/actions/verdict`) and a workflow (`.github/workflows/verdict.yml`) that
run `examples/sentiment_f1.verdict` (gated on F1 + a no-regression floor).

## Honest limits & possible extensions

By design the bundled models are toys, so the demo stays hermetic. Real use
registers real models (above). Remaining extensions: baseline-from-prior-run
regression (today the baseline is an inline number), structured (non-string)
input/output, calibration/cost/latency metrics, and a hosted runner. None of that
changes the core rule: **a claim you can't back is a bug, so the language refuses
it.**
