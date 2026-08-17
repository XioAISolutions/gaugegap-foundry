# CurveRank certified coverage screening

`curverank-0001` reports the certified spectral mismatch `M_n` — one number
saying how far a truncated candidate operator's spectrum sits from the first `k`
Riemann zeros. `curverank-0002` answers a proportion-shaped question with the
same machinery:

> Of the first `k` zeros, how many are matched — within a stated tolerance `tau`
> — by the certified spectrum of a finite truncation?

Proportions are exactly the shape of claim that travels well and verifies
badly, so this lane is built so that the number cannot be quoted without the
things that make it meaningful: the truncation, the tolerance, the zero source,
and a pair of bounds rather than a point estimate.

## Bounds, not an estimate

Every count comes from interval enclosures, never from point eigenvalues:

- a zero is **certainly covered** when some eigenvalue enclosure lies within
  `tau` of it for *every* value in both enclosures;
- a zero is **certainly uncovered** when *every* eigenvalue enclosure is farther
  than `tau` from it, for every value in both enclosures;
- anything else is **undetermined** at the working precision.

Undetermined zeros are charged to the upper bound and never to the lower one, so
the reported interval

```text
coverage in [certainly_covered / k, (certainly_covered + undetermined) / k]
```

is a rigorous enclosure of the true coverage at that tolerance. Both endpoints
are exact rationals; the separation bounds behind them are computed with
directed rounding, so neither endpoint can be crossed by a rounding error.
Enclosures containing `0` are dropped first, mirroring the zero-mode filtering
in `certified_spectral_mismatch`, so a structural zero mode cannot be counted as
a match.

## The threshold is an input

The run takes a comparison threshold and reports one of three verdicts:

| Verdict | Meaning |
| --- | --- |
| `CERTIFIED_BELOW_THRESHOLD` | the certified **upper** bound is strictly below the threshold: this finite model cannot reach it at this truncation and tolerance |
| `MEETS_THRESHOLD_AT_TRUNCATION` | the certified **lower** bound reaches the threshold — a finite screening observation, not convergence evidence |
| `UNDETERMINED_AT_PRECISION` | the bounds straddle the threshold; raise the precision or the truncation |

The certificate records the threshold with an explicit `role` field —
*"supplied comparison threshold; an input to this screen, not a result of it"* —
so the JSON cannot be reread later as if the number had been measured.

## What the current run reports

```bash
foundry run curverank-0002-coverage
```

Berry-Keating `xp`, first 12 zeros, `tau = 0.5`, threshold `0.6725`:

| `n` | certified coverage | covered / uncovered / undetermined | `M_n` enclosure | verdict |
| --- | --- | --- | --- | --- |
| 16 | `[0.0000, 0.0000]` | 0 / 12 / 0 | `[31.2699, 31.2699]` | `CERTIFIED_BELOW_THRESHOLD` |
| 24 | `[0.0833, 0.0833]` | 1 / 11 / 0 | `[32.8273, 32.8273]` | `CERTIFIED_BELOW_THRESHOLD` |
| 32 | `[0.3333, 0.3333]` | 4 / 8 / 0 | `[33.5743, 33.5743]` | `CERTIFIED_BELOW_THRESHOLD` |
| 40 | `[0.0000, 0.0000]` | 0 / 12 / 0 | `[34.0371, 34.0371]` | `CERTIFIED_BELOW_THRESHOLD` |

Two things are worth reading carefully.

**No zero is undetermined.** The enclosures are tight enough at 50 decimal
digits that every zero is decided, so the bounds coincide and the verdict does
not depend on precision at this size.

**Coverage is not monotone in the truncation.** It rises from 0 to 4/12 and
falls back to 0 at `n = 40`. Nothing is wrong: at a fixed tolerance the
eigenvalues of successive truncations move, and a coverage percentage carries no
meaning without the truncation and tolerance attached to it. This is the
concrete reason a bare "X% matched" headline is not a result — the same operator
family yields 0%, 33%, and 0% depending on a parameter the headline drops.

The certified mismatch is reported alongside, and it does increase across the
panel: these truncations are getting *farther* from the zeros in the `L2` sense,
not closer.

## Formal artifact

Each run emits `<label>-coverage.coq` next to the JSON: one Coq section per
truncation that fell below its threshold. Following the pattern in
`gaugegap.rigorous.curverank_formal_emit`, the interval computation is not
re-derived inside Coq. The certified upper bound enters as one clearly labelled
hypothesis, and Coq discharges the remaining real-arithmetic step with `lra`,
closed with `Qed`:

```coq
Variable coverage_xp_n32_k12 : R.
Hypothesis certified_upper_bound_xp_n32_k12 :
  coverage_xp_n32_k12 <= 1 / 3.

Definition comparisonThreshold_xp_n32_k12 : R := 269 / 400.

Theorem coverage_below_threshold_xp_n32_k12 :
  coverage_xp_n32_k12 < comparisonThreshold_xp_n32_k12.
```

The emitted file is picked up by `scripts/compile_coq_certificates.py`, which
compiles it with `coqc` rather than grepping it for `Admitted`.

## Claim boundary

Published density theorems about the proportion of nontrivial zeta zeros lying
on the critical line — Selberg, Levinson, Conrey and their successors — are
statements about the zeros of the zeta function itself. **This lane neither
evaluates, reproduces, nor contradicts any of them.** It measures a different
finite quantity: spectral coverage by one truncated candidate operator at one
tolerance.

A negative certificate here rules out exactly one finite truncation of one
operator family at one tolerance. It is not evidence for or against the Riemann
Hypothesis, and it is not a verdict on the Hilbert-Polya program. Language this
artifact does not earn: any claim about the proportion of zeros on the critical
line, any comparison with a published density result, any statement about a
continuum limit.

What it does earn: a finite-system benchmark, an enclosure rather than an
estimate, a reproducible certificate digest, and a machine-checked inequality —
all of which a screenshot of a percentage does not have.

## Commands

```bash
foundry run curverank-coverage-smoke   # n = 12, k = 6, reduced CI gate
foundry run curverank-0002-coverage    # n in {16, 24, 32, 40}, k = 12

python scripts/run_curverank_coverage.py \
  --family dirac_rindler --n-basis 16 24 --k-zeros 10 \
  --tolerance 0.25 --threshold 0.5 \
  --label curverank-0002-dirac --output-dir results/curverank-coverage
```
