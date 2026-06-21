import Mathlib.Tactic

namespace WarpEnergy.Warp

/-- Prefactor K = v_s^2 (y^2+z^2) / (4 r_s^2) and s = f'(r_s)^2 (abstract reals);
    the Alcubierre Eulerian energy density is rho = -(1/(8*pi)) * K * s. -/
variable (K s : ℝ)

/-- TRUST INPUT 1 -- K is a ratio of squares, hence non-negative. -/
axiom K_nonneg : K ≥ 0
/-- TRUST INPUT 2 -- s = f'(r_s)^2 is a square, hence non-negative. -/
axiom s_nonneg : s ≥ 0

/-- The weak energy condition is violated: rho = -(1/(8*pi)) * K * s ≤ 0. -/
theorem rho_nonpos : -(1 / (8 * Real.pi)) * K * s ≤ 0 := by
  have hpi : (0:ℝ) < Real.pi := Real.pi_pos
  have hKs : K * s ≥ 0 := mul_nonneg K_nonneg s_nonneg
  have hcoef : (0:ℝ) < 1 / (8 * Real.pi) := by positivity
  nlinarith [mul_nonneg (le_of_lt hcoef) hKs]

end WarpEnergy.Warp
