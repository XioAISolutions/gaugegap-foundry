import GaugeGapLean.Hadamard.Defs

/-!
# Hadamard Gram identity statements (DAG nodes)

One node per named result in `formal/hadamard/gram_identity.v`, lemmas
included: `C01`-`C08` correspond to `disagree_bounds`, `product_from_disagree`,
`mismatches_nonnegative`, `inner_eq_popcount_form`, `mismatches_self`,
`inner_self_eq_length`, `orthogonal_length_even` and
`orthogonal_length_is_even`.
-/

namespace GaugeGap.Hadamard

/-- **C01** — a single popcount bit is zero or one. Coq: `disagree_bounds`. -/
def Stmt_C01_DisagreeBounds : Prop :=
  ∀ a b : Sign, 0 ≤ disagree a b ∧ disagree a b ≤ 1

/-- **C02** — the ±1 product in popcount form. Coq: `product_from_disagree`. -/
def Stmt_C02_ProductFromDisagree : Prop :=
  ∀ a b : Sign, a.value * b.value = 1 - 2 * disagree a b

/-- **C03** — a popcount is never negative. Coq: `mismatches_nonnegative`. -/
def Stmt_C03_MismatchesNonneg : Prop :=
  ∀ u v : List Sign, 0 ≤ mismatches u v

/-- **C04** — the core identity: on equal-length vectors the popcount form the
verifier computes agrees with the sum-of-products definition.
Coq: `inner_eq_popcount_form`. -/
def Stmt_C04_InnerEqPopcountForm : Prop :=
  ∀ u v : List Sign, u.length = v.length →
    inner u v = (u.length : ℤ) - 2 * mismatches u v

/-- **C05** — a vector never disagrees with itself. Coq: `mismatches_self`. -/
def Stmt_C05_MismatchesSelf : Prop :=
  ∀ u : List Sign, mismatches u u = 0

/-- **C06** — the diagonal gate: every diagonal entry of `H * Hᵀ` is the order.
Coq: `inner_self_eq_length`. -/
def Stmt_C06_InnerSelfEqLength : Prop :=
  ∀ u : List Sign, inner u u = (u.length : ℤ)

/-- **C07** — the off-diagonal gate: orthogonal equal-length ±1 rows make the
length twice the popcount. Coq: `orthogonal_length_even`. -/
def Stmt_C07_OrthogonalLengthTwicePopcount : Prop :=
  ∀ u v : List Sign, u.length = v.length → inner u v = 0 →
    (u.length : ℤ) = 2 * mismatches u v

/-- **C08** — hence that length is even. This is the elementary half of the
necessary condition on Hadamard orders; `4 ∣ n` is strictly stronger and is not
stated here. Coq: `orthogonal_length_is_even`. -/
def Stmt_C08_OrthogonalLengthIsEven : Prop :=
  ∀ u v : List Sign, u.length = v.length → inner u v = 0 →
    Even (u.length : ℤ)

end GaugeGap.Hadamard
