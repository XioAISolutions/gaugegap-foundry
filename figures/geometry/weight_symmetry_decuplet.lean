import Mathlib.Tactic

namespace WeightSymmetry.P3Q0

/-- su(3) irrep (p,q)=(3,0), dim 10. The multiplicity-weighted
    weights sum to zero (balanced about the origin) — exact integer identity
    (3*coord), discharged by norm_num. A verifiable symmetry invariant. -/
theorem balanced_coord0 : ((-3) + (-3) + (0) + (-3) + (0) + (3) + (-3) + (0) + (3) + (6) : ℤ) = 0 := by norm_num
theorem balanced_coord1 : ((-3) + (0) + (-3) + (3) + (0) + (-3) + (6) + (3) + (0) + (-3) : ℤ) = 0 := by norm_num
theorem balanced_coord2 : ((6) + (3) + (3) + (0) + (0) + (0) + (-3) + (-3) + (-3) + (-3) : ℤ) = 0 := by norm_num

end WeightSymmetry.P3Q0
