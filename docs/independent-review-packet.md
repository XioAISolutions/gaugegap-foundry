# Independent-Review Packet — Certified Finite-Truncation Spectral Screening

**Purpose.** This document is a self-contained audit trail for the certified
spectral-screening result. It is written *for an external reviewer* who has not
seen the codebase and who should be able to (a) reproduce every certified number
from a single command, (b) follow the trust chain from raw operator to certified
bound, and (c) find every place where the rigor depends on an assumption that
the reviewer — not the authors — must sign off on.

It is deliberately conservative. Where the implementation is rigorous, it says
so and points at the line. Where rigor rests on a trusted component or an
unverified assumption, it flags that as a **verification obligation** rather
than glossing over it.

> **Claim boundary (unchanged from the preprint).** Every result here is a
> certified bound on a *finite truncation* of a candidate operator. Nothing in
> this packet addresses the truncation → ∞ limit, the infinite-dimensional
> spectrum, the Riemann Hypothesis, or the Hilbert–Pólya conjecture. A large
> certified mismatch at finite size is evidence against a candidate, not a
> disproof; a small one is necessary but not sufficient.

---

## 1. What is claimed, precisely

For a candidate operator family `F`, a truncation size `n`, and `k` Riemann
zeros, the pipeline returns an interval `[M_lower, M_upper]` with the guarantee:

> The L2 spectral mismatch
> `M_n = ‖ sort(|eig(F_n)|)[:n] − sort(Im ρ)[:k] ‖₂ / √n`
> between the spectrum of the truncated operator `F_n` and the first `k`
> non-trivial zeta zeros satisfies `M_lower ≤ M_n ≤ M_upper`,
> **subject to the verification obligations in §5.**

`M_lower` is the headline number: a machine-checked lower bound on how far the
truncated spectrum sits from the low-lying zeros.

The certified panel (regenerated at the current commit):

| family | n | dim | certified `M_n ≥` | `M` width | max eig-enclosure width | min enclosure gap | disjoint |
|--------|---|-----|-------------------|-----------|-------------------------|-------------------|----------|
| `xp` (Berry–Keating) | 10 | 10 | 27.391322 | 2.8e-14 | 7.1e-14 | 1.879 | ✅ |
| `xp` (Berry–Keating) | 15 | 15 | 29.390825 | 3.6e-14 | 6.1e-14 | 1.765 | ✅ |
| `xp` (Berry–Keating) | 20 | 20 | 35.535690 | 6.7e-14 | 1.4e-13 | 1.588 | ✅ |
| `dirac_rindler` | 8 | 16 | 23.940135 | 6.8e-14 | 1.3e-13 | 1.514 | ✅ |
| `quantum_graph` (star, 3 edges) | 8 | 24 | 76.165716 | 2.1e-13 | 1.4e-12 | 2.265 | ✅ |

The two rightmost columns are the audit-relevant diagnostics, not decoration:
the **min enclosure gap** (1.5–2.3) exceeds the **max eigenvalue-enclosure
width** (≤ 1.4e-12) by twelve orders of magnitude, so the eigenvalue enclosures
are pairwise disjoint — which is the condition §5.2 requires.

---

## 2. One-command reproduction

```bash
pip install -e ".[dev]"          # installs numpy + mpmath
python3 scripts/certify_screening.py
```

This rebuilds the table above from scratch — it reads **no** pre-recorded result
file — and prints, per row, the certified mismatch, its width, the largest
eigenvalue-enclosure radius, the minimum gap between enclosures, and whether the
enclosures are disjoint. Add `--json out.json` to capture machine-readable
output, or `--k-zeros K` to vary the zero count.

The test suite independently checks the same machinery:

```bash
pytest tests/test_curverank_certified.py -q
```

Relevant regression tests, by obligation:
- `test_embedding_eigenvalues_enclosed` — every true eigenvalue lands in an enclosure.
- `test_lower_bound_is_valid_lower_bound` — `M_lower` never exceeds the float mismatch.
- `test_overlapping_enclosures_stay_a_valid_lower_bound` — the order-statistic bound stays valid when enclosures overlap (the previously-fixed bug).
- `test_zero_mode_is_excluded` — structural zero modes are dropped, not paired with the first zero.

---

## 3. Trust chain (raw operator → certified bound)

```
operator family  →  interval matrix  →  verified eigenvalue enclosures  →  certified mismatch
   (§3.1)              (§3.1)                  (§3.2)                            (§3.3)
```

### 3.1 Operator construction — `gaugegap.curverank_operators`
Each truncation is built as an `IntervalMatrix`. For `xp` the entries are exact
rationals (zero-width intervals); for `dirac_rindler` and `quantum_graph` the
transcendental entries (`exp(aξ)`, `((m+1)π/ℓ)²`) are enclosed at working
precision. Complex-Hermitian families use the real embedding
`[[Re, −Im], [Im, Re]]`, whose spectrum is the operator spectrum with every
eigenvalue doubled; the doubled pairs are merged afterward in
`curverank_certified._collapse_doubled_spectrum`.

### 3.2 Verified eigenvalue enclosures — `verified_hermitian_eigenvalues`
`src/gaugegap/rigorous/interval_arithmetic.py:353`. The rigorous core. For a real
symmetric `A`, any scalar `θ` and unit vector `x` satisfy
`|λ − θ| ≤ ‖Ax − θx‖₂ / ‖x‖₂` for **some** eigenvalue `λ` (the residual / Weyl /
Bauer–Fike bound). The code:
1. takes approximate eigenpairs `(θ_i, x_i)` from `numpy.linalg.eigh` on the
   midpoint matrix — these are **guesses**; correctness does not depend on them;
2. evaluates the residual `Ax_i − θ_i x_i` and the norms **in interval
   arithmetic** (`mpmath`, 50 digits);
3. returns `[θ_i − ρ_i, θ_i + ρ_i]`, certified to contain a true eigenvalue.

Because the bound holds for *any* `x`, rounding the float eigenvector to a
zero-width interval is sound — `x` is just "some unit vector." Observed radius
`ρ_i ≈ 10⁻¹³`.

### 3.3 Certified mismatch — `certified_spectral_mismatch`
`src/gaugegap/curverank_spectral.py:113`. Uses **order-statistic enclosures**:
for interval data the k-th smallest true value lies in `[k-th smallest lower
endpoint, k-th smallest upper endpoint]`. Pairing per-rank enclosures gives a
mismatch lower bound valid for *every* ordering consistent with the intervals
(so overlap can never inflate the bound), reducing to naive pairing when
disjoint. Zeta zeros come from `mpmath.zetazero` (§5.3). Structural zero modes
(enclosures containing 0) are dropped before ranking so a spurious zero is not
paired with the first zeta zero.

---

## 4. What is genuinely rigorous

- **The residual eigenvalue bound (§3.2).** Standard, correctly applied; its
  validity is independent of the float eigensolver's accuracy.
- **The order-statistic mismatch (§3.3).** Valid for any interval ordering;
  guarded by a dedicated regression test.
- **Disjointness diagnostic.** The regenerator measures it rather than assuming
  it, and all current rows satisfy it by a 12-orders-of-magnitude margin.

---

## 5. Verification obligations — what a reviewer must check

These are the load-bearing assumptions. None is hidden; each is something an
external auditor should independently confirm before endorsing the certificate.

### 5.1 Directed rounding (the most important caveat)
The `Interval` class (`interval_arithmetic.py:21`) implements `+,−,×,÷,√,exp`
using `mpmath`'s **round-to-nearest** `mpf` operations at 50 digits, **not**
outward-directed rounding. Consequently an enclosure endpoint can be wrong in
its last ~ulp at 50 digits, i.e. by `O(10⁻⁵⁰)`. This is ~37 orders of magnitude
below the residual widths (`~10⁻¹³`) that dominate every reported number, so it
does not affect any digit shown — **but it means the enclosures are rigorous "up
to last-digit rounding at 50 dps," not unconditionally.** A fully rigorous
implementation should switch the trusted path to `mpmath.iv` (directed-rounding
interval type) or add explicit outward rounding. *Obligation: confirm this slack
is acceptable for the intended use, or request the `mpmath.iv` hardening.*

### 5.2 One-to-one spectral correspondence
The residual bound certifies each enclosure contains *some* eigenvalue; it does
**not** by itself guarantee the n enclosures capture the n distinct eigenvalues
(two could bracket the same one, another could be missed). The clean
correspondence follows from a counting argument **only when the enclosures are
pairwise disjoint.** The regenerator reports `min enclosure gap` and a
`disjoint` flag for exactly this reason; all current rows pass. *Obligation:
confirm disjointness holds (it is printed) for any new family/size before
trusting its mismatch as a per-rank certificate.*

### 5.3 Trust in `mpmath.zetazero`
The zeta-zero enclosures (`curverank_spectral.py:84`) trust `mpmath.zetazero` to
its documented working-precision accuracy and use a heuristic half-width
`eps = 10^-(dps-5) = 10⁻⁴⁵`. This is a trust assumption on `mpmath`, not an
independent certification of the zeros. *Obligation: accept `mpmath`'s
zero accuracy, or replace with an independently certified zero source.*

### 5.4 Scope of the interval library
Only `+,−,×,÷,√,exp` are on the trusted path used by the screening. The `sin`
/`cos` methods (`interval_arithmetic.py:133`) use naive endpoint bounds that do
**not** track interior extrema and are *not* sound for wide intervals — they are
not used by this pipeline, but must not be reused elsewhere without fixing.
`Interval.contains` (`:61`) applies a `1e-12` tolerance and is a test/diagnostic
helper, never part of a certificate.

---

## 6. Reviewer checklist

- [ ] `python3 scripts/certify_screening.py` reproduces §1's table on your machine.
- [ ] `pytest tests/test_curverank_certified.py -q` passes.
- [ ] Read `verified_hermitian_eigenvalues` and agree the residual bound is correctly applied (§3.2).
- [ ] Read `certified_spectral_mismatch` and agree the order-statistic pairing is a valid lower bound under overlap (§3.3).
- [ ] Decide whether the round-to-nearest slack of §5.1 is acceptable, or require `mpmath.iv` hardening.
- [ ] Confirm the `disjoint` flag is `True` for every row you rely on (§5.2).
- [ ] Accept or replace the `mpmath.zetazero` trust assumption (§5.3).

---

## 7. Files

| component | path |
|-----------|------|
| Regenerator (entry point) | `scripts/certify_screening.py` |
| Verified eigenvalue enclosures | `src/gaugegap/rigorous/interval_arithmetic.py` |
| Mismatch + zero enclosures | `src/gaugegap/curverank_spectral.py` |
| Pipeline orchestration | `src/gaugegap/curverank_certified.py` |
| Operator builders | `src/gaugegap/curverank_operators.py` |
| Tests | `tests/test_curverank_certified.py` |
| Preprint draft | `docs/preprint-curverank-certified-screening.md` |
