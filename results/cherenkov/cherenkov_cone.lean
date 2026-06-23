import Mathlib.Tactic

namespace Cherenkov.Cone

/-- c = cos(theta_c) and nb = n*beta (abstract reals). -/
axiom c : ℝ
axiom nb : ℝ

/-- TRUST INPUT 1 -- at/above threshold: n*beta >= 1. -/
axiom above_threshold : nb ≥ 1
/-- TRUST INPUT 2 -- the cone cosine is positive. -/
axiom cos_pos : c > 0
/-- TRUST INPUT 3 -- the Cherenkov relation cos(theta_c) * (n beta) = 1. -/
axiom cherenkov_relation : c * nb = 1

/-- The cone cosine is a valid cosine: 0 < c <= 1 (theta_c is a real angle). -/
theorem cone_valid : 0 < c ∧ c ≤ 1 := by
  refine ⟨cos_pos, ?_⟩
  nlinarith [cherenkov_relation, above_threshold, cos_pos]

end Cherenkov.Cone
