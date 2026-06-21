import Mathlib.Tactic

namespace Branching.D3

/-- The effective branch count N_eff = 1 / Tr(rho^2) (abstract). -/
axiom Neff : ℝ

/-- TRUST INPUT 1 -- Tr(rho^2) <= 1, so the participation ratio N_eff >= 1. -/
axiom neff_lower : Neff ≥ 1
/-- TRUST INPUT 2 -- Tr(rho^2) >= 1/d, so N_eff <= d. -/
axiom neff_upper : Neff ≤ 3.0

/-- The system occupies between 1 and d effective branches (no holes). -/
theorem branch_bracket : 1 ≤ Neff ∧ Neff ≤ 3.0 := by
  constructor
  · linarith [neff_lower]
  · linarith [neff_upper]

end Branching.D3
