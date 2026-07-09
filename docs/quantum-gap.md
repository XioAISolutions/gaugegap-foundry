# The Quantum Gap — one formula for every certificate

## The observation

The GaugeGap Foundry runs many kinds of finite experiment — lattice-gauge spectral gaps,
Riemann-adjacent spectral screening, finite Navier–Stokes surrogates, photonic
quantum-network primitives, and demonstrations of established physical bounds. Read closely,
**every certified result is the same mathematical object**: the verified lower endpoint of a
finite enclosure of an observable, held strictly above an explicit floor.

We name that functional the **Quantum Gap**:

```
QG(O, β) := lower(O) − β
```

- `O` is an observable of a finite system.
- `lower(O)` is the **rigorous lower bound** of a finite enclosure `[low, high]` of `O`
  (interval arithmetic, a certified eigenvalue enclosure, or an exact algebraic bound — never
  a point estimate).
- `β` is a declared floor or target.
- The claim is **certified exactly when `QG > 0`**.

## One formula, every track

| Track | `O` — enclosed observable | `β` — floor | Certified statement |
|---|---|---|---|
| GaugeGap | `E₁ − E₀` (spectral gap) | `0` | finite gap is positive |
| CurveRank | minimum certified level spacing | `0` | spectrum is separated |
| FlowGap | energy-decay rate | `0` | finite dynamics dissipate |
| NetGap (advantage) | average channel fidelity | `2/3` | beats the classical floor |
| NetGap (security) | BB84 key rate `r = 1 − 2h(Q)` | `0` | key is secure |
| Physical limits | demonstrated margin | established bound | bound is respected with slack |

## The module

`src/gaugegap/quantum_gap.py` makes `QG` first class:

- a frozen `QuantumGap(observable, track, enclosure_low, enclosure_high, floor, claim_boundary)`
  with derived `gap = enclosure_low − floor` and `certified = gap > 0`;
- constructors that **reuse the existing certified kernels** rather than re-deriving anything —
  `from_spectrum` (via `certify.certify_spectrum`), `from_threshold`, `from_fidelity`,
  `from_rate`, `from_bound`;
- one generic discharged Lean 4 / Coq emitter, `emit_quantum_gap_certificate`, proving
  `low ≥ β + m ⇒ QG ≥ m` with `linarith` / `lra` — the same shape as the Landauer and NetGap
  certificates, with no `sorry` / `Admitted`;
- `unified_gap_report()`, the end-to-end run: one representative observable from every track,
  each pushed through the *same* formula and reported as a `(low, floor, gap, certified)` row.

## Run it

```bash
foundry run quantumgap-0001-unified   # full report + emitted certificate
foundry run quantumgap-smoke          # reduced deterministic run
```

Evidence lands in `results/quantumgap-0001/` — a ledgered JSON bundle (`run_id`, `git_state`,
`config_hash`), a `rows.csv`, and the discharged `.lean` / `.v` certificate.

## Claim boundary

The Quantum Gap is a **unifying bookkeeping functional over verified finite enclosures**. It
makes the repository's existing certificates one formula; it is **not new physics** and proves
nothing beyond each underlying finite certificate. Every row keeps its own track's claim
boundary (finite-system, toy, or established-bound). In particular, no GaugeGap row is a
continuum Yang–Mills mass-gap claim, and no CurveRank row is a proof of the Riemann Hypothesis.
