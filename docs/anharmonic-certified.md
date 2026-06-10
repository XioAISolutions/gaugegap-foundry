# Certified Variational Bounds for the Quartic Anharmonic Oscillator

A genuinely new certified result (not infrastructure): machine-checked **upper
bounds on the true energy levels** of the quantum quartic anharmonic oscillator,

```
H = ½ p² + ½ x² + λ x⁴        (ħ = m = ω = 1)
```

— the textbook quantum system whose spectrum has **no closed form** (the levels
are transcendental numbers known only numerically).

> **Claim boundary.** This certifies *upper bounds* on the eigenvalues of a
> quantum-mechanical anharmonic oscillator, via the variational principle. It is
> a rigorous **one-sided** bound — not a two-sided enclosure of the true energy,
> and not a statement about any field theory, continuum limit, or Millennium
> Prize problem.

## Why this is rigorous (and one-sided)

In the harmonic-oscillator basis, `½ p² + ½ x²` is diagonal (`n + ½`) and the
quartic term has exact matrix elements via `x = (a + a†)/√2`. Projecting `H` onto
the first `N` basis states and diagonalizing gives, by the **Rayleigh–Ritz /
min–max theorem**, eigenvalues that bound the true ones from above:

```
E_n^(N)  ≥  E_n^(true)   for every truncation N,   and   E_n^(N) ↓ E_n^(true) as N → ∞.
```

We build the projected Hamiltonian as an **interval matrix** (the only irrational
entries are the `√((k+1)/2)` off-diagonals of `x`, enclosed with directed-rounding
`√`; `x⁴` is formed in an `(N+pad)` space and the exact `N×N` block is taken) and
run it through `verified_hermitian_eigenvalues`. The **upper endpoint** of each
certified enclosure is then a machine-checked upper bound on `E_n^(true)`.

## Result (λ = 1)

The certified upper bound on the ground state decreases monotonically toward the
documented value `E₀ ≈ 0.8037706512`:

| N | certified `E₀ ≤` |
|---|------------------|
| 10 | 0.8056137533 |
| 20 | 0.8037739947 |
| 30 | 0.8037707785 |
| ∞ (reference) | 0.8037706512 |

At `N = 30` the certified bound sits `≈ 1.3×10⁻⁷` above the true value — a tight,
rigorous, one-sided bound. The enclosures themselves are `~10⁻¹³` wide.

Sanity check: at `λ = 0` the system is the harmonic oscillator and the certified
levels are exactly `{0.5, 1.5, 2.5, 3.5, …}` (zero width).

## Run it

```bash
python3 scripts/run_anharmonic.py --lam 1.0 --n-basis 30
pytest tests/test_anharmonic.py -q
```

## Files

| component | path |
|-----------|------|
| Module | `src/gaugegap/anharmonic.py` |
| Runner | `scripts/run_anharmonic.py` |
| Tests | `tests/test_anharmonic.py` |
