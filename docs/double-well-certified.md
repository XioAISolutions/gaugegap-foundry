# Certified Enclosures for the Symmetric Quartic Double Well

A second certified quantum-mechanics result: the symmetric double well

```
H = ½ p² − ½ x² + λ x⁴        (ħ = m = 1, λ > 0)
```

with two degenerate classical minima separated by a barrier of height `1/(16λ)`.
Quantum tunnelling splits the would-be degenerate pairs into close doublets; the
**ground-state tunnelling splitting** `Δ = E₁ − E₀` is the canonical observable.

> **Claim boundary.** The level *upper* bounds (Rayleigh–Ritz) and the
> comparison-oscillator *lower* bounds are rigorous statements about the true
> (infinite-dimensional) operator. The tunnelling-splitting enclosure is certified
> for the **finite truncation**; it converges to the true splitting (shown by
> stability in `N`), but a two-sided bound on the true splitting of a
> near-degenerate doublet is *not* claimed. Not a field-theory / continuum /
> Millennium-Prize claim.

## Method

Built on the same interval-arithmetic eigensolver: `½p² + ½x² = diag(n+½)` in the
harmonic-oscillator basis, so `H = diag(n+½) − x² + λx⁴`, with `x²` and `x⁴` taken
as exact `N×N` blocks of an `(N+pad)` product. Lower bounds use the
comparison-oscillator inequality `x⁴ ≥ 2a x² − a²` (here requiring `4λa > 1` for a
harmonic envelope): `Eₙ(H) ≥ √(4λa−1)(n+½) − λa²`.

## Result (λ = 0.1, barrier 0.625)

Certified two-sided level enclosures (validated against a high-precision `N=160`
diagonalization — every interval brackets the true level):

| n | certified `Eₙ ∈` | true |
|---|------------------|------|
| 0 | `[−0.575929, −0.154125]` | −0.154125 |
| 1 | `[−0.226113, +0.142765]` | +0.142765 |
| 2 | `[+0.363382, +1.010189]` | +1.010189 |
| 3 | `[+1.122238, +1.949137]` | +1.949137 |

The upper bounds are tight (`~10⁻¹³`); the comparison-oscillator lower bounds are
crude (the doublet is not resolved from below — expected for near-degenerate
tunnelling levels).

**Tunnelling splitting** (finite truncation), certified to `~10⁻¹³` and stable in
`N`:

```
N=40:  Δ ∈ [0.296889931004, 0.296889931005]
N=50:  Δ ∈ [0.296889931004, 0.296889931005]
|Δ(40) − Δ(50)| ≈ 1e-12   ⇒  the truncated splitting has converged.
```

So the certified (truncated) splitting is `0.29688993100`, with strong evidence it
equals the true double-well splitting to `~10⁻¹²`.

## Run it

```bash
python3 scripts/run_double_well.py --lam 0.1 --n-basis 40
pytest tests/test_double_well.py -q
```

## Files

| component | path |
|-----------|------|
| Module | `src/gaugegap/double_well.py` |
| Runner | `scripts/run_double_well.py` |
| Tests | `tests/test_double_well.py` |
