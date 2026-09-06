import GaugeGapLean.InfoGap.Defs

/-!
# InfoGap finite no-hiding statements (DAG nodes)

`B01`, `B02`, `B04`, `B05` and `B06` correspond one-to-one with the theorems in
`formal/infogap/no_hiding_finite.v`. That file states `system_zero_probability`
and `system_one_probability` as literally the same equation (the second is
proved by `apply` on the first), so it maps to a single node here; `B03` states
the fact that pairing was reaching for -- the two branches exhaust the
probability. `B07` is not in the Coq source: it states the no-hiding content
directly, that the measured system statistics carry no information about the
input.
-/

namespace GaugeGap.InfoGap

/-- **B01** — the input probabilities partition unity.
Coq: `input_probability_normalized`. -/
def Stmt_B01_InputNormalised : Prop :=
  ∀ ar ai br bi : ℝ, inputNorm ar ai br bi = 1 →
    pairProbability ar ai + pairProbability br bi = 1

/-- **B02** — a measured system branch has weight exactly `1/2`.
Coq: `system_zero_probability` (and its duplicate `system_one_probability`). -/
def Stmt_B02_BranchWeightHalf : Prop :=
  ∀ h ar ai br bi : ℝ, h ^ 2 = 1 / 2 → inputNorm ar ai br bi = 1 →
    branchWeight h ar ai br bi = 1 / 2

/-- **B03** — the two system branches exhaust the probability. -/
def Stmt_B03_BranchesExhaust : Prop :=
  ∀ h ar ai br bi : ℝ, h ^ 2 = 1 / 2 → inputNorm ar ai br bi = 1 →
    branchWeight h ar ai br bi + branchWeight h ar ai br bi = 1

/-- **B04** — recovery on `B` returns `|alpha| ^ 2` exactly.
Coq: `recovery_zero_probability`. -/
def Stmt_B04_RecoveryAlpha : Prop :=
  ∀ h ar ai : ℝ, h ^ 2 = 1 / 2 → recoveredPair h ar ai = pairProbability ar ai

/-- **B05** — recovery on `B` returns `|beta| ^ 2` exactly.
Coq: `recovery_one_probability`. -/
def Stmt_B05_RecoveryBeta : Prop :=
  ∀ h br bi : ℝ, h ^ 2 = 1 / 2 → recoveredPair h br bi = pairProbability br bi

/-- **B06** — the recovered probabilities stay normalised.
Coq: `recovered_probability_normalized`. -/
def Stmt_B06_RecoveredNormalised : Prop :=
  ∀ h ar ai br bi : ℝ, h ^ 2 = 1 / 2 → inputNorm ar ai br bi = 1 →
    recoveredPair h ar ai + recoveredPair h br bi = 1

/-- **B07** — the no-hiding content, absent from the Coq source: the measured
system statistics are the same for every normalised input, so nothing about
`alpha` and `beta` survives in the system. Everything is recovered on `B` by
`B04` and `B05`. -/
def Stmt_B07_SystemCarriesNoInformation : Prop :=
  ∀ h a1 a2 a3 a4 b1 b2 b3 b4 : ℝ, h ^ 2 = 1 / 2 →
    inputNorm a1 a2 a3 a4 = 1 → inputNorm b1 b2 b3 b4 = 1 →
    branchWeight h a1 a2 a3 a4 = branchWeight h b1 b2 b3 b4 ∧
      branchWeight h a1 a2 a3 a4 = 1 / 2

end GaugeGap.InfoGap
