import GaugeGapLean.Hadamard.Statements

/-!
# Hadamard Gram identity proofs

`C04`, `C06`, `C07` and `C08` are proved from the earlier nodes, mirroring how
the Coq certificate chains its lemmas. No `sorry`, no `axiom`, no
`native_decide`.
-/

namespace GaugeGap.Hadamard

theorem c01_disagreeBounds : Stmt_C01_DisagreeBounds := by
  unfold Stmt_C01_DisagreeBounds
  intro a b
  cases a <;> cases b <;> norm_num [disagree]

theorem c02_productFromDisagree : Stmt_C02_ProductFromDisagree := by
  unfold Stmt_C02_ProductFromDisagree
  intro a b
  cases a <;> cases b <;> norm_num [Sign.value, disagree]

theorem c03_mismatchesNonneg : Stmt_C03_MismatchesNonneg := by
  unfold Stmt_C03_MismatchesNonneg
  intro u
  induction u with
  | nil => intro v; simp [mismatches]
  | cons a u ih =>
    intro v
    cases v with
    | nil => simp [mismatches]
    | cons b v =>
      have hbit := (c01_disagreeBounds a b).1
      have hrest := ih v
      simp only [mismatches]
      linarith

theorem c04_innerEqPopcountForm : Stmt_C04_InnerEqPopcountForm := by
  unfold Stmt_C04_InnerEqPopcountForm
  intro u
  induction u with
  | nil => intro v _; simp [inner, mismatches]
  | cons a u ih =>
    intro v hlen
    cases v with
    | nil => simp at hlen
    | cons b v =>
      simp only [List.length_cons] at hlen
      have hlen' : u.length = v.length := by omega
      have hrest := ih v hlen'
      have hprod := c02_productFromDisagree a b
      simp only [inner, mismatches, List.length_cons]
      push_cast
      linear_combination hprod + hrest

theorem c05_mismatchesSelf : Stmt_C05_MismatchesSelf := by
  unfold Stmt_C05_MismatchesSelf
  intro u
  induction u with
  | nil => simp [mismatches]
  | cons a u ih => cases a <;> simp [mismatches, disagree, ih]

theorem c06_innerSelfEqLength : Stmt_C06_InnerSelfEqLength := by
  unfold Stmt_C06_InnerSelfEqLength
  intro u
  rw [c04_innerEqPopcountForm u u rfl, c05_mismatchesSelf u]
  ring

theorem c07_orthogonalLengthTwicePopcount : Stmt_C07_OrthogonalLengthTwicePopcount := by
  unfold Stmt_C07_OrthogonalLengthTwicePopcount
  intro u v hlen horth
  have h := c04_innerEqPopcountForm u v hlen
  rw [horth] at h
  linarith

theorem c08_orthogonalLengthIsEven : Stmt_C08_OrthogonalLengthIsEven := by
  unfold Stmt_C08_OrthogonalLengthIsEven
  intro u v hlen horth
  refine ⟨mismatches u v, ?_⟩
  rw [c07_orthogonalLengthTwicePopcount u v hlen horth]
  ring

end GaugeGap.Hadamard
