import Mathlib

/-!
# InfoGap finite no-hiding definitions

Lean restatement of the quantities in `formal/infogap/no_hiding_finite.v`, so
the same finite identities are checked by two independent kernels.

`ar`, `ai`, `br`, `bi` are the real and imaginary parts of the input
amplitudes `alpha` and `beta`; `h` is the Hadamard amplitude, used only
through `h ^ 2 = 1 / 2`. The expressions keep the shape the Coq certificate
uses -- squares of `h * x` rather than a pre-factored `h ^ 2` -- so the
correspondence is a transliteration rather than a paraphrase.

CLAIM BOUNDARY: exact algebraic probability identities for the implemented
three-qubit circuit. Not a formalisation of the general no-hiding theorem: no
Hilbert spaces, no Stinespring dilation, no Schmidt decomposition.
-/

namespace GaugeGap.InfoGap

/-- Probability carried by one amplitude pair, `|alpha| ^ 2` or `|beta| ^ 2`. -/
def pairProbability (x y : ℝ) : ℝ := x ^ 2 + y ^ 2

/-- Normalisation functional of the input state. -/
def inputNorm (ar ai br bi : ℝ) : ℝ := ar ^ 2 + ai ^ 2 + br ^ 2 + bi ^ 2

/-- Weight of one measured system branch after the Hadamard. -/
def branchWeight (h ar ai br bi : ℝ) : ℝ :=
  (h * ar) ^ 2 + (h * ai) ^ 2 + (h * br) ^ 2 + (h * bi) ^ 2

/-- Probability recovered on `B` from the amplitudes of one branch. -/
def recoveredPair (h x y : ℝ) : ℝ := 2 * ((h * x) ^ 2 + (h * y) ^ 2)

end GaugeGap.InfoGap
