import Mathlib.Tactic

namespace CurveRankCertified.MonotoneXp

/-- Certified L2 mismatch lower bounds for the Berry-Keating xp truncations at
    n ∈ [10, 15, 20, 25, 30], against the first 20 Riemann zeros. Each entry is a certified
    lower bound on the corresponding M_n (produced by the interval kernel). -/
def L : List ℝ := [27.391322449240906, 29.390824646996478, 35.5356899424466, 36.603410611887064, 40.00965971015598]

/-- The certified lower bounds are strictly increasing across the tested panel.
    This is a finite statement about the COMPUTED BOUNDS — not a continuum
    monotonicity claim about M_n, and not a proof of the Riemann Hypothesis.
    Discharged by `norm_num` (no proof holes). -/
theorem certified_bounds_strictly_increasing : (27.391322449240906 < 29.390824646996478) ∧ (29.390824646996478 < 35.5356899424466) ∧ (35.5356899424466 < 36.603410611887064) ∧ (36.603410611887064 < 40.00965971015598) := by
  norm_num

end CurveRankCertified.MonotoneXp
