# Certified Finite-Truncation Spectral Screening of the Berry–Keating xp Operator

**Track:** CurveRank · **Status:** certified finite-system benchmark · **Date:** 2026-06-04

> **Claim boundary.** This is a finite-system, finite-truncation benchmark. It
> does **not** claim to resolve the Riemann Hypothesis or the Hilbert–Pólya
> conjecture, asserts no certified continuum (n → ∞) limit, and is a
> finite-system result that requires independent review. We avoid risky phrases
> and use only finite-system, certified-bound language throughout.

## Summary

We screen the truncated Berry–Keating operator `H = ½(xp + px)` as a candidate
Hilbert–Pólya operator by measuring the L2 spectral mismatch `M_n` between its
finite-`n` spectrum and the first `k` non-trivial Riemann zeta zeros. The
contribution here is **methodological rigor**: the mismatch is computed as a
machine-checked certified bound using interval arithmetic, rather than a
floating-point estimate.

For every tested truncation `n ∈ {10, 15, 20}` (comparing against the first 20
zeros), the spectrum is certifiably separated from the zeros by

| n | certified `M_n` enclosure | enclosure width |
|---|---------------------------|-----------------|
| 10 | [27.391322, 27.391322] | ≈ 2.8 × 10⁻¹⁴ |
| 15 | [29.390825, 29.390825] | ≈ 3.5 × 10⁻¹⁴ |
| 20 | [35.535690, 35.535690] | ≈ 6.4 × 10⁻¹⁴ |

The minimum certified separation over the tested truncations is
`M_n ≥ 27.39` (attained at n = 10).

## Method

The certification has three rigorous components, all in `mpmath` interval
arithmetic at 50 decimal places:

1. **Exact operator construction.** The symmetrized `xp` operator on `[0, L]` is
   purely imaginary Hermitian. We build its exact real-symmetric `2n × 2n`
   embedding `[[0, −M], [M, 0]]` (entries are exact rationals), so the operator
   itself carries essentially zero representation error.
   (`curverank_operators.berry_keating_xp_interval`)

2. **Verified eigenvalue enclosures.** For a real symmetric matrix `A` and any
   approximate unit eigenvector `x` with Rayleigh value `θ`, there exists a true
   eigenvalue within `‖Ax − θx‖₂` (the classical residual / Weyl bound). We take
   approximate eigenpairs from a floating-point solver — only a *guess* — and
   then evaluate the residual and norms entirely in interval arithmetic, so each
   returned interval is certified to contain a true eigenvalue. Enclosures are
   ~10⁻¹³ wide. (`rigorous.interval_arithmetic.verified_hermitian_eigenvalues`)

3. **Certified zeros and mismatch.** Structural zero modes (enclosures that
   contain `0`, such as the zero eigenvalue of an odd-dimensional truncation)
   are dropped first, matching the floating-point screening, so a spurious zero
   is not paired with the first zeta zero. Riemann-zero imaginary parts are enclosed
   with `mpmath.zetazero` at working precision; the mismatch `M_n` is then
   bounded below by combining the eigenvalue and zero enclosures conservatively
   (overlapping enclosures contribute zero).
   (`curverank_spectral.riemann_zero_intervals`,
   `curverank_spectral.certified_spectral_mismatch`)

The end-to-end pipeline is `curverank_certified.certified_xp_mismatch`. The
certified midpoints reproduce the previously recorded floating-point screening
values exactly, but now with certified interval bounds.

## What this does and does not establish

- **Does** establish, as a certified finite-system bound: at the tested
  truncations, this specific operator's low-lying spectrum cannot coincide with
  the low-lying zeros — it is bounded away by a definite, machine-checked margin.
- **Does not** establish anything about the `n → ∞` limit. The mismatch is
  observed to be non-decreasing across the tested truncations, but extrapolating
  a few points is not rigorous; we record it only as non-certified evidence and
  make no continuum claim.
- **Does not** bear on the truth of the Riemann Hypothesis or the existence of a
  Hilbert–Pólya operator in general.

## Other candidate operator families

The same certified machinery generalizes to the other CurveRank candidate
families. Real-symmetric operators (quantum-graph Laplacian) use the verified
enclosures directly; complex-Hermitian operators (Dirac–Rindler) use the same
real-symmetric embedding as `xp`. Representative certified mismatch bounds
against the first 20 zeros:

| family | truncation | certified `M_n ≥` |
|--------|-----------|-------------------|
| `xp` (Berry–Keating) | n = 10 | 27.39 |
| `dirac_rindler` | n = 8 | 23.94 |
| `quantum_graph` (star, 3 edges) | n_modes = 8 | 76.16 |

These are produced by `curverank_certified.certified_family_mismatch(family, n, k_zeros)`.
As with `xp`, each is a certified finite-truncation separation, not a continuum
or asymptotic claim.

## Reproducibility

```bash
pip install -e ".[dev]"
python3 scripts/run_curverank_screen.py --family xp --n-basis 10,15,20 --k-zeros 20
python3 scripts/analyze_sprint_results.py      # writes the two-tier certificate
pytest tests/test_curverank_certified.py -q    # exercises the certified pipeline
```

Artifacts: `results/sprint-now/proof_certificate.json` (Tier 1 certified bounds +
Tier 2 non-certified trend) and `results/sprint-now/PROOF_SUMMARY.md`.

## Limitations and next steps

- The certified separation is established only at the tested finite truncations;
  scaling to substantially larger `n` is future work.
- Independent review of the residual-enclosure certification is the highest-value
  next step before any external write-up.
- The certified machinery already covers the `xp`, `dirac_rindler`, and
  `quantum_graph` families; tightening the provenance of the zero enclosures and
  adding further candidate families are natural extensions.
