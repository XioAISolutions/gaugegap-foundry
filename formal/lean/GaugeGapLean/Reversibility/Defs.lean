import Mathlib

/-!
# Logical reversibility and erasure

Landauer's principle bounds the heat a physical device must dissipate when it
performs a *logically irreversible* operation. The physics is not in dispute and
is not restated here. What this track establishes is the logical premise that
bound is applied to: which gates actually destroy information, and what it costs
to avoid destroying it.

`AND` is irreversible because it is not injective -- three of its four inputs
map to `false`, so the input cannot be recovered from the output. `Toffoli` is
reversible because it is an involution, and it computes `AND` anyway: it keeps
its first two inputs and XORs the third with their conjunction. That is
Bennett's embedding, and it makes the trade explicit -- reversibility is bought
by carrying the inputs along, not for free.

CLAIM BOUNDARY: exact statements about finite Boolean functions. Nothing here
computes a heat, asserts Landauer's bound (that lives in
`src/gaugegap/quantum/landauer.py`), or says anything about gauge theory. A
truncated Hilbert space in a lattice simulation is an approximation in a model,
not a physical erasure, and no claim of that kind is made or implied.
-/

namespace GaugeGap.Reversibility

/-- Classical `AND`: two bits in, one bit out. -/
def andGate : Bool × Bool → Bool
  | (a, b) => a && b

/-- The Toffoli (controlled-controlled-NOT) gate: three bits in, three out. -/
def toffoli : Bool × Bool × Bool → Bool × Bool × Bool
  | (a, b, c) => (a, b, xor c (a && b))

/-- The Fredkin (controlled-SWAP) gate, the other standard reversible gate: it
swaps the last two bits when the first is set. Written as a pattern match on the
control bit rather than an `if`, so every ground instance reduces by iota alone
and the proofs below need no decidability instance at all. -/
def fredkin : Bool × Bool × Bool → Bool × Bool × Bool
  | (false, b, c) => (false, b, c)
  | (true, b, c) => (true, c, b)

/-- Every input of `andGate`, listed. `E02` counts fibres inside this list and
separately checks that the list misses nothing, so the counts are counts over
the whole domain rather than over a sample. -/
def inputs2 : List (Bool × Bool) :=
  [(false, false), (false, true), (true, false), (true, true)]

end GaugeGap.Reversibility
