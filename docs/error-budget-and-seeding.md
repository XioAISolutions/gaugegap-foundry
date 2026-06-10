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

## Tested

`tests/test_error_budget_and_seeding.py` checks the quadrature/linear
combination math, `dominant`/`by_category`, seed reproducibility, child-seed
independence, and — crucially — that the fixed functions are reproducible **and
do not pollute the global NumPy RNG state**.
