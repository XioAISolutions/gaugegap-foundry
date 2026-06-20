import Mathlib.Tactic

namespace WeightSymmetry.P0Q1

/-- su(3) irrep (p,q)=(0,1), dim 3. The multiplicity-weighted
    weights sum to zero (balanced about the origin) — exact integer identity
    (3*coord), discharged by norm_num. A verifiable symmetry invariant. -/
theorem balanced_coord0 : ((-2) + (1) + (1) : ℤ) = 0 := by norm_num
theorem balanced_coord1 : ((1) + (-2) + (1) : ℤ) = 0 := by norm_num
theorem balanced_coord2 : ((1) + (1) + (-2) : ℤ) = 0 := by norm_num

end WeightSymmetry.P0Q1
