# QSVT eigenvalue transform (certified)

Quantum Singular-value / eigenvalue Transformation (QSVT) applies a degree-d
polynomial `P` to the eigenvalues of a (block-encoded) Hermitian operator. This
layer computes that transform and **certifies** it against the verified spectrum.

## Method

`gaugegap.quantum.qsvt.qsvt_eigenvalue_transform(H, coeffs)`:
- Rescales `H`'s spectral window (from the certified enclosures) to `[-1, 1]`.
- Applies the monomial polynomial `P` (Horner on the matrix) → `P(H)`, whose
  eigenvalues are `P(λ)`.
- **Certifies**: for each certified eigenvalue enclosure `[lo, hi]`, evaluates `P`
  in **interval arithmetic** (`rigorous.interval_arithmetic.Interval`, outward
  rounded) to get a rigorous enclosure of `P(λ)`, and checks every transformed
  eigenvalue lands inside one. Also cross-checks against `P` applied to the classical
  eigenvalues.

So the polynomial-of-the-spectrum result is bracketed by the interval kernel — the
verification-first treatment of QSVT.

## Use it

```bash
make qsvt
python scripts/run_qsvt.py --operator berry_keating_xp --coeffs 0,0,1   # P(x)=x^2
```

```python
from gaugegap.quantum.qsvt import qsvt_eigenvalue_transform
r = qsvt_eigenvalue_transform(H, [0.0, 1.5, 0.0, -0.5])   # P(x)=1.5x - 0.5 x^3
r.all_inside        # transformed spectrum inside certified P-enclosures
```

For `P(x)=x^2` and `P(x)=1.5x−0.5x^3` on the Berry-Keating truncation, every
transformed eigenvalue is certified and matches the reference to ~1e-16.

## Claim boundary

A **certified polynomial transform of a finite Hermitian spectrum** — the classical
reference of what QSVT realises on hardware (phase-factor synthesis is **not** faked
here). Simulation/classical level; not a continuum, Yang-Mills, or Millennium claim.
Dependency-light (numpy + the interval kernel).
