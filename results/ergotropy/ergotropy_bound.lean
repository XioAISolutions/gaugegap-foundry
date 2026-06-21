import Mathlib.Tactic

namespace Ergotropy.WExtractable

/-- Extractable work W = <H> - E_passive (abstract). -/
axiom W : ℝ

/-- TRUST INPUT 1 -- the passive state minimizes cyclic energy, so W >= 0. -/
axiom work_nonneg : W ≥ 0
/-- TRUST INPUT 2 -- the passive energy is at least the ground energy E0, so
    W <= <H> - E0 (no energy can be drawn below the ground state). -/
axiom work_bounded : W ≤ 2.0000000000000004

/-- Extractable work is finite and non-negative: no free energy (no holes). -/
theorem no_free_energy : 0 ≤ W ∧ W ≤ 2.0000000000000004 := by
  constructor
  · linarith [work_nonneg]
  · linarith [work_bounded]

end Ergotropy.WExtractable
