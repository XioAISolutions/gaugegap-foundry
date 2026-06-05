# Certified Finite-Truncation Spectral Screening of Hilbert–Pólya Candidate Operators

**Authors:** Xio AI Solutions (corresponding author TBD)
**Affiliation:** GaugeGap Foundry / CurveRank track
**Preprint draft — v0.1 (2026-06-04). Not peer reviewed.**

> **Scope and claim boundary.** This is a finite-system, finite-truncation
> computational benchmark. It does **not** claim to resolve the Riemann
> Hypothesis or the Hilbert–Pólya conjecture, asserts no certified continuum
> (truncation → ∞) limit, and makes no statement about infinite-dimensional
> spectra. All results are certified finite-system bounds and require
> independent review. We deliberately avoid risky phrasing and use only
> finite-system, certified-bound language.

## Abstract

The Hilbert–Pólya program seeks a self-adjoint operator whose spectrum
reproduces the imaginary parts of the non-trivial zeros of the Riemann zeta
function. A standard computational heuristic screens candidate operators by
truncating them to finite dimension and measuring the L2 distance between their
spectra and the low-lying zeros. Such screening is normally carried out in
floating-point arithmetic, so the reported separations are estimates rather than
certificates. We replace the floating-point step with interval arithmetic and
report **certified** finite-truncation separation bounds: for each tested
truncation, a machine-checked lower bound on the spectral mismatch between the
candidate's spectrum and the first `k` Riemann zeros. The certification combines
(i) verified Hermitian eigenvalue enclosures via the classical residual bound,
(ii) certified zeta-zero enclosures, and (iii) an order-statistic construction
that makes the mismatch bound valid for every ordering consistent with the
eigenvalue enclosures. We apply the method to three candidate families
(Berry–Keating `xp`, a truncated Dirac–Rindler operator, and a quantum-graph
Laplacian) and obtain enclosures of width ≈ 10⁻¹³. The contribution is
methodological: turning a routine floating-point screening into a reproducible,
independently checkable certificate, within explicit finite-system claim
boundaries.

## 1. Introduction

The non-trivial zeros of the Riemann zeta function lie, conjecturally, on the
critical line `Re(s) = ½`. The Hilbert–Pólya idea is that their imaginary parts
`{t_j}` might be the eigenvalues of some self-adjoint operator. The
Berry–Keating proposal `H = ½(xp + px)` is the most studied semiclassical
candidate. A practical, modest question downstream of this program is: *for a
given finite truncation of a candidate operator, how close can its spectrum get
to the low-lying zeros?* This is a screening question — a large separation at
finite size is evidence against (not a disproof of) the candidate, and a small
separation is necessary but far from sufficient.

Screening is typically done numerically: diagonalize a truncation, sort the
eigenvalues, and compute an L2 mismatch to the first `k` zeros. Because the
diagonalization and the mismatch are floating-point, the resulting numbers carry
unquantified rounding error and are not certificates. This note closes that gap:
we compute the same mismatch as a rigorously certified enclosure, so the
reported finite-truncation separation is independently checkable.

We emphasize what is and is not claimed. A certified finite-truncation
separation says only that, at the tested size, the candidate's low-lying
spectrum cannot coincide with the low-lying zeros — by a definite, machine-checked
margin. It says nothing about the truncation → ∞ limit, about the candidate at
infinite dimension, or about the Riemann Hypothesis itself.

## 2. Methods

All interval arithmetic is carried out with `mpmath` at 50 decimal digits of
working precision.

### 2.1 Candidate operators

We construct each candidate truncation as an exact (or precision-enclosed)
interval matrix:

- **Berry–Keating `xp`.** The symmetrized position-space operator on `[0, L]` is
  purely imaginary Hermitian; its entries are exact rationals, so its real
  symmetric `2n × 2n` embedding has zero-width entries.
- **Dirac–Rindler.** A truncated Dirac-type operator in Rindler coordinates;
  its transcendental Rindler factors `exp(a ξ)` are enclosed at working
  precision.
- **Quantum-graph Laplacian.** A real-symmetric operator built from a metric
  star graph; diagonal entries `((m+1)π/ℓ)²` are enclosed at working precision,
  coupling entries are exact integers.

A complex Hermitian operator `H = Re + iIm` (with `Re` symmetric, `Im`
antisymmetric) has the same spectrum, each eigenvalue doubled, as the real
symmetric matrix `[[Re, −Im], [Im, Re]]`. We work with this real embedding for
the complex families and collapse the doubled spectrum afterward.

### 2.2 Verified Hermitian eigenvalue enclosures

For a real symmetric matrix `A`, a unit vector `x`, and scalar `θ`, the
classical residual bound states that some eigenvalue `λ` of `A` satisfies
`|λ − θ| ≤ ‖Ax − θx‖₂`. We obtain approximate eigenpairs `(θ_i, x_i)` from a
floating-point symmetric eigensolver — these are only guesses — and then
evaluate the residual and the vector norm entirely in interval arithmetic. The
returned interval `[θ_i − ρ_i, θ_i + ρ_i]` is therefore certified to contain a
true eigenvalue of `A`, independent of solver accuracy. In our matrices the
residual radius is ≈ 10⁻¹³.

### 2.3 Certified zeta-zero enclosures

The imaginary parts of the first `k` zeros are enclosed with `mpmath.zetazero`
at working precision, giving intervals that bracket the true zeros up to that
precision.

### 2.4 Order-statistic certified mismatch

The mismatch `M_n = ‖sort(|eig|)[:n] − sort(zeros)[:n]‖₂ / √n` pairs the `i`-th
smallest eigenvalue magnitude with the `i`-th zero. If two eigenvalue enclosures
overlap, their true order is ambiguous, so pairing whole enclosures sorted by
midpoint is not a valid certificate. We instead use an order-statistic
construction: for interval data the `k`-th smallest true value lies in
`[k-th smallest lower endpoint, k-th smallest upper endpoint]` (sort lower and
upper endpoints independently). Pairing those per-rank enclosures yields a
mismatch lower bound valid for every ordering consistent with the intervals, and
it reduces to the naive pairing when the enclosures are disjoint. Structural
zero modes — enclosures that contain `0`, e.g. the zero eigenvalue of an
odd-dimensional symmetric truncation — are dropped before the order statistics,
consistently with the floating-point screening, so a spurious zero is not paired
with the first zeta zero.

## 3. Results

For each family we report the certified mismatch lower bound against the first
20 Riemann zeros. The `xp` enclosures reproduce previously recorded
floating-point screening values, now with certified bounds of width ≈ 10⁻¹³.

| family | truncation | certified `M_n ≥` | enclosure width |
|--------|-----------|-------------------|-----------------|
| `xp` (Berry–Keating) | n = 10 | 27.39 | ≈ 3 × 10⁻¹⁴ |
| `xp` (Berry–Keating) | n = 15 | 29.39 | ≈ 4 × 10⁻¹⁴ |
| `xp` (Berry–Keating) | n = 20 | 35.54 | ≈ 6 × 10⁻¹⁴ |
| `dirac_rindler` | n = 8 | 23.94 | ≈ 2 × 10⁻¹³ |
| `quantum_graph` (star, 3 edges) | n_modes = 8 | 76.16 | ≈ 1 × 10⁻¹² |

For `xp`, the certified mismatch is non-decreasing across the tested
truncations. We record this trend as non-certified supporting evidence only and
make no continuum claim.

## 4. Discussion

The value here is not a new bound but a new *guarantee*. A floating-point
screening that reports `M_10 ≈ 27.39` becomes, under this method, a certified
statement that the truncated `xp` spectrum is separated from the first 20 zeros
by at least a machine-checked margin. Because the certificate is reproducible
and independently checkable, it is suitable as infrastructure for
verification-first computational mathematics, and the same machinery applies
unchanged across candidate families.

## 5. Limitations

- Results are certified only at the tested finite truncations; the truncation →
  ∞ behaviour is not addressed.
- The certificate concerns separation of the candidate's spectrum from the
  zeros; it does not bear on the Riemann Hypothesis or on the existence of a
  Hilbert–Pólya operator in general.
- Independent review of the residual-enclosure certification is a prerequisite
  before any external claims.

## 6. Reproducibility

```bash
pip install -e ".[dev]"
python3 scripts/certify_screening.py            # regenerates the certified table (§3)
pytest tests/test_curverank_certified.py -q
```

The single command `scripts/certify_screening.py` reproduces every certified
number above from scratch (reading no pre-recorded result file) and additionally
reports the diagnostics the certificate depends on. For the full trust chain,
the rigorous-vs-trusted breakdown, and the reviewer checklist, see
[`docs/independent-review-packet.md`](independent-review-packet.md).

Implementation: `gaugegap.rigorous.interval_arithmetic.verified_hermitian_eigenvalues`,
`gaugegap.curverank_spectral.{riemann_zero_intervals, certified_spectral_mismatch}`,
and the orchestration in `gaugegap.curverank_certified`.

## References (to be completed)

1. M. V. Berry and J. P. Keating, *H = xp and the Riemann zeros* (1999).
2. A. Connes, trace-formula approach to the zeta function (1999).
3. S. M. Rump, *Verification methods: rigorous results using floating-point
   arithmetic*, Acta Numerica (2010).
4. The `mpmath` library for arbitrary-precision and interval arithmetic.
5. Standard references on the residual / Weyl eigenvalue perturbation bound for
   symmetric matrices.
