import Mathlib.Tactic

namespace CurveRankCertified.DiracRindlerN20

/-- The certified L2 spectral mismatch `M` between the Dirac-Rindler truncation
    (n = 20) and the first 20 Riemann zeros. `M` is abstract; its only used
    property is the certified lower bound below. -/
axiom M : ℝ

/-- TRUST INPUT — interval-arithmetic certificate (external to Lean, produced by
    directed-rounding verified Hermitian eigenvalue enclosures and Arb-certified
    zeta-zero enclosures): `M ≥ 26.191066278053995`. This is the single axiom; everything
    below is discharged by Lean. -/
axiom certified_lower_bound : M ≥ 26.191066278053995

/-- Separation (impossibility) margin. -/
def separationThreshold : ℝ := 1.0

/-- Separation theorem (finite truncation, NOT the Riemann Hypothesis): the
    certified mismatch is bounded away from zero by the threshold. Fully
    discharged by `linarith` from the certificate (no proof holes). -/
theorem separated_from_zeros : M ≥ separationThreshold := by
  have h := certified_lower_bound
  unfold separationThreshold
  linarith

end CurveRankCertified.DiracRindlerN20
