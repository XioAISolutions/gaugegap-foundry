import Mathlib.Tactic

namespace WeightSymmetry.P1Q0

/-- su(3) irrep (p,q)=(1,0), dim 3. The multiplicity-weighted
    weights sum to zero (balanced about the origin) — exact integer identity
    (3*coord), discharged by norm_num. A verifiable symmetry invariant. -/
theorem balanced_coord0 : ((-1) + (-1) + (2) : ℤ) = 0 := by norm_num
theorem balanced_coord1 : ((-1) + (2) + (-1) : ℤ) = 0 := by norm_num
theorem balanced_coord2 : ((2) + (-1) + (-1) : ℤ) = 0 := by norm_num

end WeightSymmetry.P1Q0
