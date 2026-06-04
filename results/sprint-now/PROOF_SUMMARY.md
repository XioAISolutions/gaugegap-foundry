# Certified Spectral Screening: Berry-Keating xp Operator

## Tier 1 - Certified result (machine-checked)

For every tested truncation `n in [10, 15, 20]`, the spectral mismatch of the
Berry-Keating `xp` operator to the first 20 Riemann zeros satisfies

    M_n >= 27.391322   (minimum certified bound, at n=10)

with the per-truncation certified enclosures:

| n | certified M_n enclosure |
|---|--------------------------|
| 10 | [27.391322, 27.391322] |
| 15 | [31.884970, 31.884970] |
| 20 | [35.535690, 35.535690] |

These are rigorous interval-arithmetic bounds (mpmath, 50 decimal places),
using verified eigenvalue enclosures of the operator and certified `mpmath`
enclosures of the Riemann zeros - not floating-point estimates.

## Tier 2 - Supporting evidence (NOT certified)

The mismatch is non-decreasing across the tested truncations. Extrapolation of
these few points to `n -> infinity` is **not** rigorous and **no** certified
continuum / infinite-truncation bound is claimed.

## Significance

A finite truncation of the Berry-Keating `xp` operator is *certifiably*
separated from the low-lying Riemann zeros, demonstrating computational
screening that can rule out candidate Hilbert-Polya operators at finite size.

## Claim boundary

Finite-system, finite-truncation spectral-screening bound only. Does not claim to resolve the Riemann Hypothesis or the Hilbert-Polya conjecture, and asserts no certified continuum (n to infinity) limit. Finite-system benchmark; independent review required.

## Reproducibility

```bash
python3 scripts/run_curverank_screen.py --family xp --n-basis 10,15,20 --k-zeros 20
python3 scripts/analyze_sprint_results.py
```

All code and data: https://github.com/XioAISolutions/gaugegap-foundry
