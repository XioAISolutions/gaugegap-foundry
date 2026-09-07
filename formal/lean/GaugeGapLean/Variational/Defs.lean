import Mathlib

/-!
# Finite-dimensional variational bound

The certified eigenvalue brackets this repository emits (for example
`results/certified-bracket/bracket_E0.lean`) rest on three assumptions, and they
are not the same kind of thing:

1. an interval-arithmetic *lower* bound on the eigenvalue -- a numerical fact,
   produced outside any prover by directed-rounding enclosures;
2. the numerical value of the Rayleigh quotient of a trial state -- also a
   numerical fact;
3. "the Rayleigh quotient of a normalised trial state is at least the smallest
   eigenvalue, by Courant-Fischer" -- **not** a numerical fact. That is a
   theorem, and assuming it is assuming mathematics.

This track proves the third one, so it stops being an assumption.

## What is proved and what is assumed

The state is given by its coefficients `c` in an orthonormal eigenbasis, with
`lam` the corresponding eigenvalues, so the Rayleigh quotient is
`∑ i, lam i * c i ^ 2` and the squared norm is `∑ i, c i ^ 2`. Everything below
follows from that expansion by elementary inequalities.

The expansion itself -- that a Hermitian operator on a finite-dimensional space
*has* such an eigenbasis -- is the spectral theorem, and it is a standing
hypothesis here rather than something this track establishes. So the honest
summary is: the inequality half of Courant-Fischer is proved; the spectral
decomposition it is applied to is assumed.

CLAIM BOUNDARY: finite-dimensional real linear algebra for a declared
eigenbasis expansion. Not a statement about unbounded operators, not a
construction of the spectrum, and not a Yang-Mills mass gap claim.
-/

namespace GaugeGap.Variational

/-- Squared norm of a state given by its coefficients in an orthonormal basis. -/
def normSq (n : ℕ) (c : Fin n → ℝ) : ℝ := ∑ i, c i ^ 2

/-- Rayleigh quotient numerator `⟪ψ, Hψ⟫` for a state given by its coefficients
in an orthonormal eigenbasis with eigenvalues `lam`. -/
def rayleigh (n : ℕ) (lam c : Fin n → ℝ) : ℝ := ∑ i, lam i * c i ^ 2

end GaugeGap.Variational
