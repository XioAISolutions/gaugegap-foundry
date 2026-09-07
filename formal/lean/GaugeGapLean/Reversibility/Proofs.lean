import GaugeGapLean.Reversibility.Statements

/-!
# Reversibility proofs

Every gate here acts on at most eight states, so each statement is settled by
splitting on every input bit and reducing. That is kernel evaluation over the
whole domain, not a sampled check. The gates are pattern matches on `Bool`, so
the ground goals close by `rfl` -- no decision procedure is even needed except
for the two disequalities. No `sorry`, no `axiom`, no `native_decide`.
-/

namespace GaugeGap.Reversibility

theorem e01_andNotInjective : Stmt_E01_AndNotInjective := by
  unfold Stmt_E01_AndNotInjective
  refine ⟨rfl, by decide, fun h => ?_⟩
  exact absurd (h (rfl : andGate (false, false) = andGate (false, true))) (by decide)

theorem e02_andFibreSizes : Stmt_E02_AndFibreSizes := by
  unfold Stmt_E02_AndFibreSizes
  refine ⟨fun a b => ?_, rfl, rfl⟩
  cases a <;> cases b <;> decide

theorem e03_toffoliInvolutive : Stmt_E03_ToffoliInvolutive := by
  unfold Stmt_E03_ToffoliInvolutive
  rintro ⟨a, b, c⟩
  cases a <;> cases b <;> cases c <;> rfl

theorem e04_toffoliBijective : Stmt_E04_ToffoliBijective := by
  unfold Stmt_E04_ToffoliBijective
  have h : Function.Involutive toffoli := e03_toffoliInvolutive
  exact h.bijective

theorem e05_toffoliComputesAnd : Stmt_E05_ToffoliComputesAnd := by
  unfold Stmt_E05_ToffoliComputesAnd
  intro a b
  cases a <;> cases b <;> rfl

theorem e06_reversibilityKeepsTheInputs : Stmt_E06_ReversibilityKeepsTheInputs := by
  unfold Stmt_E06_ReversibilityKeepsTheInputs
  intro a b c
  cases a <;> cases b <;> cases c <;> exact ⟨rfl, rfl⟩

theorem e07_fredkinInvolutive : Stmt_E07_FredkinInvolutive := by
  unfold Stmt_E07_FredkinInvolutive
  rintro ⟨a, b, c⟩
  cases a <;> cases b <;> cases c <;> rfl

end GaugeGap.Reversibility
