import Mathlib.Tactic

namespace WeightSymmetry.P2Q0

/-- su(3) irrep (p,q)=(2,0), dim 6. The multiplicity-weighted
    weights sum to zero (balanced about the origin) — exact integer identity
    (3*coord), discharged by norm_num. A verifiable symmetry invariant. -/
theorem balanced_coord0 : ((-2) + (-2) + (1) + (-2) + (1) + (4) : ℤ) = 0 := by norm_num
theorem balanced_coord1 : ((-2) + (1) + (-2) + (4) + (1) + (-2) : ℤ) = 0 := by norm_num
theorem balanced_coord2 : ((4) + (1) + (1) + (-2) + (-2) + (-2) : ℤ) = 0 := by norm_num

end WeightSymmetry.P2Q0
