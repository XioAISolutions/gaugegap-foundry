import GaugeGapLean.InfoGap.Statements

/-!
# InfoGap finite no-hiding proofs

`B03`, `B06` and `B07` are proved from the earlier nodes rather than from
scratch, mirroring how the Coq certificate chains its theorems. No `sorry`, no
`axiom`, no `native_decide`.
-/

namespace GaugeGap.InfoGap

theorem b01_inputNormalised : Stmt_B01_InputNormalised := by
  unfold Stmt_B01_InputNormalised inputNorm pairProbability
  intro ar ai br bi hn
  linear_combination hn

theorem b02_branchWeightHalf : Stmt_B02_BranchWeightHalf := by
  unfold Stmt_B02_BranchWeightHalf inputNorm branchWeight
  intro h ar ai br bi hh hn
  linear_combination h ^ 2 * hn + hh

theorem b03_branchesExhaust : Stmt_B03_BranchesExhaust := by
  unfold Stmt_B03_BranchesExhaust
  intro h ar ai br bi hh hn
  rw [b02_branchWeightHalf h ar ai br bi hh hn]
  norm_num

theorem b04_recoveryAlpha : Stmt_B04_RecoveryAlpha := by
  unfold Stmt_B04_RecoveryAlpha recoveredPair pairProbability
  intro h ar ai hh
  linear_combination (2 * (ar ^ 2 + ai ^ 2)) * hh

theorem b05_recoveryBeta : Stmt_B05_RecoveryBeta := by
  unfold Stmt_B05_RecoveryBeta recoveredPair pairProbability
  intro h br bi hh
  linear_combination (2 * (br ^ 2 + bi ^ 2)) * hh

theorem b06_recoveredNormalised : Stmt_B06_RecoveredNormalised := by
  unfold Stmt_B06_RecoveredNormalised
  intro h ar ai br bi hh hn
  rw [b04_recoveryAlpha h ar ai hh, b05_recoveryBeta h br bi hh]
  exact b01_inputNormalised ar ai br bi hn

theorem b07_systemCarriesNoInformation : Stmt_B07_SystemCarriesNoInformation := by
  unfold Stmt_B07_SystemCarriesNoInformation
  intro h a1 a2 a3 a4 b1 b2 b3 b4 hh hna hnb
  refine ⟨?_, b02_branchWeightHalf h a1 a2 a3 a4 hh hna⟩
  rw [b02_branchWeightHalf h a1 a2 a3 a4 hh hna,
    b02_branchWeightHalf h b1 b2 b3 b4 hh hnb]

end GaugeGap.InfoGap
