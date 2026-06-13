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

## Two-sided enclosure of the true ground-state energy (Temple's inequality)

The variational bound above is *one-sided* (an upper bound). A rigorous **lower**
bound — and hence a genuine two-sided enclosure of the true `E₀` — comes from
**Temple's inequality**:

```
E₀  ≥  ε − σ² / (β − ε),   with  ε = ⟨ψ|H|ψ⟩,  σ² = ⟨ψ|H²|ψ⟩ − ε²,
```

valid for any trial `ψ` and any `β` with `ε < β ≤ E₁`. Because `λx⁴ ⪰ 0`, the
operator bound `H = HO + λx⁴` gives `Eₙ ≥ n + ½`, so **`E₁ ≥ 3/2`** — a rigorous
`β = 3/2`. The trial vector is the floating-point ground vector of the truncation
(its accuracy affects only tightness, not validity), and `ε, σ²` are evaluated in
interval arithmetic over the exact `(N+4)`-projected Hamiltonian, so
`⟨ψ|H²|ψ⟩ = ‖Hψ‖²` captures every component `H` couples into.

Result (`λ = 1`), a **machine-checked two-sided enclosure** of the true
infinite-dimensional `E₀`:

| N | certified `E₀ ∈` | width |
|---|------------------|-------|
| 20 | `[0.8033255258, 0.8037739947]` | 4.5×10⁻⁴ |
| 30 | `[0.8036369143, 0.8037707785]` | 1.3×10⁻⁴ |

Both endpoints are rigorous, and the enclosure tightens as `N` grows (the
variance `σ²` shrinks).

## Sharpened lower bound (comparison oscillator) & the full low-lying spectrum

Temple's `β` (a lower bound on `E₁`) was originally the weak operator bound
`E₁ ≥ 3/2`. A much sharper rigorous bound comes from a **solvable comparison
oscillator**: since `(x²−a)² ≥ 0`,

```
x⁴ ≥ 2a x² − a²   ⇒   H ⪰ ½p² + ½(1+4λa)x² − λa²  =:  H_a,
```

so by min–max `Eₙ(H) ≥ Eₙ(H_a) = √(1+4λa)(n+½) − λa²` for **every** `a > 0` and
**every** level `n`. Optimizing `a` gives `E₁ ≥ 2.4375` (λ=1), versus the old
`3/2`. Using it as Temple's `β` tightens the ground-state enclosure ~2.4×
(width `1.3×10⁻⁴ → 5.7×10⁻⁵` at N=30).

The comparison-oscillator bounds also give **two-sided enclosures of the excited
states** (lower = comparison oscillator, upper = Rayleigh–Ritz). At `λ=1`,
`N=30`, validated against a high-precision `N=200` diagonalization:

| n | certified `Eₙ ∈` | true | width |
|---|------------------|------|-------|
| 0 | `[0.80371373, 0.80377078]` | 0.80377065 | 5.7×10⁻⁵ |
| 1 | `[2.43749004, 2.73789447]` | 2.73789226 | 0.30 |
| 2 | `[4.59982752, 5.17929787]` | 5.17929169 | 0.58 |

Every certified interval brackets the true level — the ground state tightly
(Temple), the excited states more loosely (the comparison-oscillator lower bounds
loosen with `n`) but genuinely two-sided. A `λ` sweep (`λ ∈ {0.1, 0.5, 1, 2}`)
likewise brackets the documented ground energies.

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
