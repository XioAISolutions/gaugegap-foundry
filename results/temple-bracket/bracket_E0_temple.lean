import Mathlib.Tactic

namespace Bracket.E0Temple

/-- The eigenvalue E (abstract); the only used facts are the two certified bounds. -/
axiom E : ℝ

/-- TRUST INPUT 1 -- certified lower bound from the interval-arithmetic kernel. -/
axiom certified_lower : E ≥ -3.493959207442449

/-- TRUST INPUT 2 -- variational (Ritz) upper bound: <psi|H|psi> >= E by
    Courant-Fischer, supplied by the quantum subspace eigensolver. -/
axiom variational_upper : E ≤ -3.488277972662546

/-- Two-sided certified bracket, discharged by linarith (no holes). -/
theorem bracket : -3.493959207442449 ≤ E ∧ E ≤ -3.488277972662546 := by
  constructor
  · linarith [certified_lower]
  · linarith [variational_upper]

end Bracket.E0Temple
