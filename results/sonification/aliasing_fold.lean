import Mathlib.Tactic

namespace Nyquist.Alias

/-- Sampling rate fs and a tone frequency f (abstract reals). -/
axiom fs : ℝ
axiom f : ℝ

/-- TRUST INPUT 1 -- the tone is above the Nyquist frequency: f > fs/2. -/
axiom over_nyquist : f > fs / 2
/-- TRUST INPUT 2 -- but below the sampling rate: f < fs. -/
axiom below_rate : f < fs

/-- The alias folds strictly into the band: 0 < fs - f < fs/2 (no holes). -/
theorem aliasing_fold : 0 < fs - f ∧ fs - f < fs / 2 := by
  constructor
  · linarith [below_rate]
  · linarith [over_nyquist]

end Nyquist.Alias
