import GaugeGapLean.Variational.Statements

/-!
# Variational bound proofs

No `sorry`, no `axiom`, no `native_decide`. The whole track reduces to summing
a pointwise inequality, which is exactly why assuming it was unnecessary.
-/

namespace GaugeGap.Variational

theorem d01_rayleighLowerBound : Stmt_D01_RayleighLowerBound := by
  unfold Stmt_D01_RayleighLowerBound normSq rayleigh
  intro n lam c lo h
  rw [Finset.mul_sum]
  refine Finset.sum_le_sum fun i _ => ?_
  exact mul_le_mul_of_nonneg_right (h i) (sq_nonneg (c i))

theorem d02_rayleighUpperBound : Stmt_D02_RayleighUpperBound := by
  unfold Stmt_D02_RayleighUpperBound normSq rayleigh
  intro n lam c hi h
  rw [Finset.mul_sum]
  refine Finset.sum_le_sum fun i _ => ?_
  exact mul_le_mul_of_nonneg_right (h i) (sq_nonneg (c i))

theorem d03_normalisedBracket : Stmt_D03_NormalisedBracket := by
  unfold Stmt_D03_NormalisedBracket
  intro n lam c lo hi hlo hhi hnorm
  have hlow := d01_rayleighLowerBound n lam c lo hlo
  have hupp := d02_rayleighUpperBound n lam c hi hhi
  rw [hnorm, mul_one] at hlow hupp
  exact ⟨hlow, hupp⟩

theorem d04_variationalPrinciple : Stmt_D04_VariationalPrinciple := by
  unfold Stmt_D04_VariationalPrinciple
  intro n lam c E0 h hnorm
  have hlow := d01_rayleighLowerBound n lam c E0 h
  rw [hnorm, mul_one] at hlow
  exact hlow

theorem d05_certifiedBracket : Stmt_D05_CertifiedBracket := by
  unfold Stmt_D05_CertifiedBracket
  intro n lam c E0 lower upper h hnorm hlower hupper
  exact ⟨hlower, le_trans (d04_variationalPrinciple n lam c E0 h hnorm) hupper⟩

end GaugeGap.Variational
