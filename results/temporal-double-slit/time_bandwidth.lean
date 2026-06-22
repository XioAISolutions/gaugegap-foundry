import Mathlib.Tactic

namespace TimeBandwidth.Tb

/-- Temporal width sigma_t and spectral width sigma_omega (abstract reals). -/
axiom sigma_t : ℝ
axiom sigma_omega : ℝ

/-- TRUST INPUT -- Fourier uncertainty (Gabor), denominator cleared:
    sigma_omega * (2 * sigma_t) >= 1  (i.e. sigma_omega >= 1 / (2 sigma_t)). -/
axiom fourier_uncertainty : sigma_omega * (2 * sigma_t) ≥ 1

/-- The time-bandwidth product respects the 1/2 floor (no holes). -/
theorem time_bandwidth : sigma_t * sigma_omega ≥ 1 / 2 := by
  nlinarith [fourier_uncertainty]

end TimeBandwidth.Tb
