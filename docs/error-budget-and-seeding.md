# Error-budget separation & seed repeatability (issue #12, A6)

Two small disciplines that make finite-system results trustworthy: keeping the
*sources* of uncertainty separate, and making every stochastic computation
reproducible.

> **Claim boundary.** Bookkeeping for finite-system numerical uncertainty and
> reproducibility. No continuum or first-principles claim.

## Error budget — `gaugegap.error_budget`

`ErrorBudget` collects named contributions, each tagged with a **category**
(`statistical` / `systematic` / `truncation` / `numerical`) and a **combination
kind**:

- `stochastic` (shot noise, sampling) → combined in **quadrature**;
- `bound` (truncation bounds, systematic offsets) → combined **linearly** (worst case).

The conservative total is `sqrt(Σ stochastic²) + Σ bounds`, and the budget
exposes `by_category()` and `dominant()` so the thing to reduce first is explicit.

```python
from gaugegap.error_budget import ErrorBudget

b = ErrorBudget("mass gap")
b.add("shot noise", 3e-3, "statistical", "stochastic")
b.add("Trotter step", 1e-3, "systematic", "bound")
b.add("basis truncation", 2e-3, "truncation", "bound")
print(b.report())
print("dominant:", b.dominant().name)   # 'basis truncation'
```

The certified tracks already separate sources implicitly: an interval **width**
is the numerical error, while the difference of an enclosure from a target is the
*finite-truncation* (systematic) bound — never conflated with a statistical
estimate.

## Seed repeatability — `gaugegap.seeding`

`make_rng(seed)` returns a NumPy `Generator`:

- `None` → the reproducible **default seed** (overridable process-wide with the
  `GAUGEGAP_SEED` environment variable);
- `int` → that seed;
- an existing `Generator` → returned unchanged (threading an rng through).

Stochastic routines take a `seed`/`rng` and use `make_rng` **instead of the
global `numpy.random` state**. Global seeding (`np.random.seed(42)`) is a footgun:
it silently couples unrelated code and destroys reproducibility guarantees. As
part of A6, the offending call sites were fixed:

- `quantum_metrology.mass_gap_metrology`, `adaptive_quantum_sensing` — now take `seed`;
- `optimal_control.crab_optimization` — replaced an internal `np.random.seed(42)`
  with a local seeded generator;
- `topological_quantum.measure_topological_charge` — now takes `seed`.

`child_seeds(parent, n)` derives independent, reproducible sub-stream seeds via
`SeedSequence` spawning for parallel/independent sub-tasks.

## Repeated-seed runs & confidence intervals (A6)

`gaugegap.repeated_runs` turns the seeding + budget primitives into a hardened
error budget:

```python
from gaugegap.repeated_runs import repeated_run
stats = repeated_run(estimator, parent_seed=1234, n_runs=20, level=0.95)
stats.mean, stats.ci_low, stats.ci_high, stats.ci_halfwidth
```

`repeated_run(fn, ...)` runs `fn(seed)` over `n_runs` independent `child_seeds`
and returns mean / sample std / SEM / a normal-approximation confidence interval.

`scripts/run_error_budget.py` (`make error-budget`) is the worked example: it
estimates `|λ_min|` of the Berry-Keating xp truncation from the QCELS quantum
signal under modelled shot noise + dephasing, repeated over child seeds for a 95%
**statistical** CI, then combines it with the **certified-enclosure** (truncation)
bound and a **numerical-precision** bound into a single source-separated
`ErrorBudget` (statistical in quadrature, systematic bounds linear).

### What a confidence interval here does and does NOT imply

- **Does:** quantify the statistical spread of a stochastic estimator at a
  **fixed** finite truncation / shot count.
- **Does not:** bound the truncation error (that is the separate certified
  component), nor imply anything about the continuum / thermodynamic limit. The CI
  is a finite-system statistical statement, never a continuum mass-gap claim.

## Tested

`tests/test_error_budget_and_seeding.py` checks the quadrature/linear
combination math, `dominant`/`by_category`, seed reproducibility, child-seed
independence, and — crucially — that the fixed functions are reproducible **and
do not pollute the global NumPy RNG state**. `tests/test_repeated_runs.py` checks
the confidence-interval math and the reproducibility of repeated-seed runs.
