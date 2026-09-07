import Mathlib

/-!
# Hadamard Gram identity definitions

Lean restatement of `formal/hadamard/gram_identity.v`, so the arithmetic the
Hadamard Forge verifier actually executes is checked by two independent kernels.

The verifier never materialises a ±1 matrix: each row is a bitmask, and the
inner product of rows `u` and `v` is computed as `n - 2 * popcount(u XOR v)`.
`mismatches` is that popcount, and `inner` is the textbook sum of products; the
statements relate the two.

CLAIM BOUNDARY: statements about a single pair of finite ±1 vectors of equal
length. Not a formalisation of the Hadamard conjecture, and not the theorem that
an order `n ≥ 3` admitting a Hadamard matrix satisfies `4 ∣ n`. The even-length
condition below is the elementary half of that necessary condition.
-/

namespace GaugeGap.Hadamard

/-- The ±1 alphabet, as the verifier's two bit values. -/
inductive Sign where
  | pos : Sign
  | neg : Sign
  deriving DecidableEq

/-- The integer a sign denotes. -/
def Sign.value : Sign → ℤ
  | .pos => 1
  | .neg => -1

/-- One if the two signs differ, zero otherwise: a single popcount bit. -/
def disagree : Sign → Sign → ℤ
  | .pos, .pos => 0
  | .neg, .neg => 0
  | _, _ => 1

/-- Textbook inner product over the ±1 alphabet. -/
def inner : List Sign → List Sign → ℤ
  | a :: u, b :: v => a.value * b.value + inner u v
  | [], _ => 0
  | _, [] => 0

/-- The quantity the implementation obtains from `popcount (u XOR v)`. -/
def mismatches : List Sign → List Sign → ℤ
  | a :: u, b :: v => disagree a b + mismatches u v
  | [], _ => 0
  | _, [] => 0

end GaugeGap.Hadamard
