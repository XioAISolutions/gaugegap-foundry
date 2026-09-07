import GaugeGapLean.AnomalyForge.Statements

/-!
# Anomaly Forge proofs

One theorem per statement in `GaugeGapLean/AnomalyForge/Statements.lean`.
Statements and proofs are split so that a proof edit does not invalidate the
statement module that other nodes depend on.

No `sorry`, no `axiom`, no `native_decide`: everything is discharged by
`ring`/`linarith`/`linear_combination`/`norm_num` over `ℚ`.
-/

namespace GaugeGap.AnomalyForge

theorem a01_su3Automatic : Stmt_A01_SU3Automatic := by
  unfold Stmt_A01_SU3Automatic su3U1
  intro YQ YH
  ring

theorem a02_su2FixesLepton : Stmt_A02_SU2FixesLepton := by
  unfold Stmt_A02_SU2FixesLepton su2U1
  intro n YQ YL
  constructor
  · intro h
    linarith
  · intro h
    rw [h]
    ring

theorem a03_gravReduces : Stmt_A03_GravReduces := by
  unfold Stmt_A03_GravReduces gravU1
  intro n YQ YH
  ring

theorem a04_uniqueness : Stmt_A04_Uniqueness := by
  unfold Stmt_A04_Uniqueness su2U1 gravU1
  intro n YQ Yu Yd YL Ye YH hu hd he hsu2 hgrav
  subst hu
  subst hd
  subst he
  have hYL : YL = -(n * YQ) := by linarith
  subst hYL
  have hq : n * YQ = YH := by linear_combination -hgrav
  exact ⟨hq, by linear_combination -hq, by linear_combination hq,
    by linear_combination hq, by linear_combination -hq⟩

theorem a05_u1CubedAutomatic : Stmt_A05_U1CubedAutomatic := by
  unfold Stmt_A05_U1CubedAutomatic u1Cubed
  intro n YQ YH h
  subst h
  ring

theorem a06_standardModelPoint : Stmt_A06_StandardModelPoint := by
  unfold Stmt_A06_StandardModelPoint IsAnomalyFree
  refine ⟨?_, ?_, ?_, ?_⟩
  · norm_num [su3U1]
  · norm_num [su2U1]
  · norm_num [gravU1]
  · norm_num [u1Cubed]

theorem a07_perturbationRejected : Stmt_A07_PerturbationRejected := by
  unfold Stmt_A07_PerturbationRejected IsAnomalyFree
  rintro ⟨h, -, -, -⟩
  norm_num [su3U1] at h

theorem a08_rightNeutrinoFamily : Stmt_A08_RightNeutrinoFamily := by
  unfold Stmt_A08_RightNeutrinoFamily IsAnomalyFree
  intro n YQ YH
  refine ⟨?_, ?_, ?_, ?_⟩
  · unfold su3U1; ring
  · unfold su2U1; ring
  · unfold gravU1; ring
  · unfold u1Cubed; ring

theorem a09_familyMeetsStandardModel : Stmt_A09_FamilyMeetsStandardModel := by
  unfold Stmt_A09_FamilyMeetsStandardModel
  intro n YQ YH h
  subst h
  ring

theorem a10_chargeQuantisation : Stmt_A10_ChargeQuantisation := by
  unfold Stmt_A10_ChargeQuantisation
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
    norm_num [electricCharge, protonCharge, neutronCharge]

theorem a11_wittenParity : Stmt_A11_WittenParity := by
  unfold Stmt_A11_WittenParity weakDoublets
  refine ⟨by norm_num, ⟨6, by norm_num⟩, by norm_num, ?_⟩
  intro h
  rw [Nat.even_iff] at h
  omega

theorem a12_generationScaling : Stmt_A12_GenerationScaling := by
  unfold Stmt_A12_GenerationScaling
  intro g A hg
  constructor
  · intro h
    rcases mul_eq_zero.mp h with h' | h'
    · exact absurd h' hg
    · exact h'
  · intro h
    rw [h, mul_zero]

theorem a13_mainTheorem : Stmt_A13_MainTheorem := by
  unfold Stmt_A13_MainTheorem IsAnomalyFree
  intro n YQ Yu Yd YL Ye YH hu hd he hsu2 hgrav
  obtain ⟨hq, hL, -, -, -⟩ := a04_uniqueness n YQ Yu Yd YL Ye YH hu hd he hsu2 hgrav
  subst hu
  subst hd
  subst he
  have hYL : YL = -(n * YQ) := by
    rw [hL, hq]
  subst hYL
  refine ⟨hq, ?_, hsu2, hgrav, ?_⟩
  · unfold su3U1; ring
  · exact a05_u1CubedAutomatic n YQ YH hq.symm

/-- Helper, not a DAG node: two assignments agreeing componentwise are equal. -/
theorem assignment_eq_of_components {p q : Assignment}
    (hQ : p.YQ = q.YQ) (hu : p.Yu = q.Yu) (hd : p.Yd = q.Yd)
    (hL : p.YL = q.YL) (he : p.Ye = q.Ye) (hn : p.Yn = q.Yn) : p = q := by
  cases p
  cases q
  simp_all

theorem a14_familySpannedByHyperchargeAndBL :
    Stmt_A14_FamilySpannedByHyperchargeAndBL := by
  unfold Stmt_A14_FamilySpannedByHyperchargeAndBL
  intro n x h
  refine assignment_eq_of_components ?_ ?_ ?_ ?_ ?_ ?_ <;>
    simp only [Assignment.smul, Assignment.add, familyMember, smDirection,
      blDirection] <;>
    ring

theorem a15_blDirectionAnomalyFree : Stmt_A15_BLDirectionAnomalyFree := by
  unfold Stmt_A15_BLDirectionAnomalyFree IsAnomalyFreeAssignment blDirection
  intro n
  simpa using a08_rightNeutrinoFamily n 1 0

theorem a16_hyperchargeDirectionAnomalyFree :
    Stmt_A16_HyperchargeDirectionAnomalyFree := by
  unfold Stmt_A16_HyperchargeDirectionAnomalyFree IsAnomalyFreeAssignment
    smDirection
  intro n
  simpa using a08_rightNeutrinoFamily n 1 n

theorem a17_directionsIndependent : Stmt_A17_DirectionsIndependent := by
  unfold Stmt_A17_DirectionsIndependent
  intro n a b hn heq
  have hneutrino : (Assignment.add (Assignment.smul a (smDirection n))
      (Assignment.smul b (blDirection n))).Yn = Assignment.zero.Yn := by rw [heq]
  have hquark : (Assignment.add (Assignment.smul a (smDirection n))
      (Assignment.smul b (blDirection n))).YQ = Assignment.zero.YQ := by rw [heq]
  simp only [Assignment.add, Assignment.smul, Assignment.zero, smDirection,
    blDirection] at hneutrino hquark
  have hbn : b * n = 0 := by linear_combination -hneutrino
  have hsum : a + b = 0 := by linear_combination hquark
  have hb : b = 0 := by
    rcases mul_eq_zero.mp hbn with hzero | hzero
    · exact hzero
    · exact absurd hzero hn
  exact ⟨by linarith, hb⟩

end GaugeGap.AnomalyForge
