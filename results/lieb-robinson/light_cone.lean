import Mathlib.Tactic

namespace LiebRobinson.Front

/-- Measured front velocity vf, Lieb-Robinson speed vlr, and time t (abstract). -/
axiom vf : ℝ
axiom vlr : ℝ
axiom t : ℝ

/-- TRUST INPUT 1 -- the front velocity respects the Lieb-Robinson speed. -/
axiom front_bounded : vf ≤ vlr
/-- TRUST INPUT 2 -- time is non-negative. -/
axiom time_nonneg : t ≥ 0

/-- The information front stays inside the linear light cone (no holes). -/
theorem light_cone : vf * t ≤ vlr * t := by
  nlinarith [front_bounded, time_nonneg]

end LiebRobinson.Front
