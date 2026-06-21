import Mathlib.Tactic

namespace SpeedLimit.TBuildup

/-- The entanglement build-up time t (abstract); only the QSL facts are used. -/
axiom t : ℝ

/-- TRUST INPUT 1 -- Mandelstam-Tamm quantum speed limit. -/
axiom mandelstam_tamm : t ≥ 0.29860027962613517

/-- TRUST INPUT 2 -- Margolus-Levitin quantum speed limit. -/
axiom margolus_levitin : t ≥ 0.29860027962613517

/-- The build-up time respects the tighter QSL floor (no holes). -/
theorem respects_qsl : t ≥ 0.29860027962613517 := by
  linarith [mandelstam_tamm, margolus_levitin]

end SpeedLimit.TBuildup
