import Mathlib.Tactic

namespace Bracket.E0

/-- The eigenvalue E (abstract); the only used facts are the two certified bounds. -/
axiom E : ℝ

/-- TRUST INPUT 1 -- certified lower bound from the interval-arithmetic kernel. -/
axiom certified_lower : E ≥ -12.787631637507566

/-- TRUST INPUT 2 -- variational (Ritz) upper bound: <psi|H|psi> >= E by
    Courant-Fischer, supplied by the quantum subspace eigensolver. -/
axiom variational_upper : E ≤ -12.787631637495053

/-- Two-sided certified bracket, discharged by linarith (no holes). -/
theorem bracket : -12.787631637507566 ≤ E ∧ E ≤ -12.787631637495053 := by
  constructor
  · linarith [certified_lower]
  · linarith [variational_upper]

end Bracket.E0
