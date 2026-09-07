import GaugeGapLean.Reversibility.Defs

/-!
# Reversibility statements (DAG nodes)

Every node here is a statement about a *named* gate. A theorem of the shape
"for any matrix `P` with `Pᵀ * P = 1`, `Pᵀ * P = 1`" would be true, vacuous, and
say nothing about Toffoli; the statements below quantify over the gate's inputs,
not over the gate.
-/

namespace GaugeGap.Reversibility

/-- **E01** — `AND` destroys information: two distinct inputs share an output,
so the map is not injective and the input cannot be recovered. -/
def Stmt_E01_AndNotInjective : Prop :=
  andGate (false, false) = andGate (false, true) ∧
    ((false, false) : Bool × Bool) ≠ (false, true) ∧
    ¬ Function.Injective andGate

/-- **E02** — how much it destroys, as exact fibre sizes: three of the four
inputs map to `false` and one to `true`. The first conjunct is what makes the
other two a statement about `AND` rather than about a list: `inputs2` misses no
input, so the counts are counts over the whole domain. These are the numbers the
Shannon average `H(X | Y) = (3/4) log₂ 3` is computed from, exactly, in
`gaugegap.reversibility_theorem`. -/
def Stmt_E02_AndFibreSizes : Prop :=
  (∀ a b : Bool, (a, b) ∈ inputs2) ∧
  (inputs2.filter fun p => !andGate p).length = 3 ∧
  (inputs2.filter fun p => andGate p).length = 1

/-- **E03** — `Toffoli` is an involution: applying it twice is the identity. -/
def Stmt_E03_ToffoliInvolutive : Prop :=
  ∀ x : Bool × Bool × Bool, toffoli (toffoli x) = x

/-- **E04** — hence bijective, so it destroys nothing. -/
def Stmt_E04_ToffoliBijective : Prop := Function.Bijective toffoli

/-- **E05** — and it still computes `AND`: with the third bit set to `false`,
the third output is the conjunction of the first two inputs. -/
def Stmt_E05_ToffoliComputesAnd : Prop :=
  ∀ a b : Bool, (toffoli (a, b, false)).2.2 = (a && b)

/-- **E06** — the price, stated rather than glossed: `Toffoli` is reversible
*because* it carries its inputs forward. The first two outputs are the first two
inputs, always. Reversible computation does not avoid the cost of erasure; it
defers it to whenever those retained bits are cleared. -/
def Stmt_E06_ReversibilityKeepsTheInputs : Prop :=
  ∀ a b c : Bool, (toffoli (a, b, c)).1 = a ∧ (toffoli (a, b, c)).2.1 = b

/-- **E07** — `Fredkin` is an involution too, so the result is not an accident
of one gate. -/
def Stmt_E07_FredkinInvolutive : Prop :=
  ∀ x : Bool × Bool × Bool, fredkin (fredkin x) = x

end GaugeGap.Reversibility
