import GaugeGapLean.Variational.Defs

/-!
# Variational bound statements (DAG nodes)

`D05` is deliberately shaped like the emitted certificate
`results/certified-bracket/bracket_E0.lean`, so the two can be compared line by
line: the certificate assumes all three of its inputs, while `D05` takes only
the two numerical ones as hypotheses and derives the Courant-Fischer step from
`D04`.
-/

namespace GaugeGap.Variational

/-- **D01** — a lower bound on every eigenvalue is a lower bound on the
Rayleigh quotient, scaled by the squared norm. -/
def Stmt_D01_RayleighLowerBound : Prop :=
  ∀ (n : ℕ) (lam c : Fin n → ℝ) (lo : ℝ), (∀ i, lo ≤ lam i) →
    lo * normSq n c ≤ rayleigh n lam c

/-- **D02** — and dually for an upper bound. -/
def Stmt_D02_RayleighUpperBound : Prop :=
  ∀ (n : ℕ) (lam c : Fin n → ℝ) (hi : ℝ), (∀ i, lam i ≤ hi) →
    rayleigh n lam c ≤ hi * normSq n c

/-- **D03** — for a normalised state the Rayleigh quotient lies between any
bounds on the spectrum. -/
def Stmt_D03_NormalisedBracket : Prop :=
  ∀ (n : ℕ) (lam c : Fin n → ℝ) (lo hi : ℝ),
    (∀ i, lo ≤ lam i) → (∀ i, lam i ≤ hi) → normSq n c = 1 →
    lo ≤ rayleigh n lam c ∧ rayleigh n lam c ≤ hi

/-- **D04** — the variational principle, the step the emitted certificates
assume: no normalised trial state has a Rayleigh quotient below the ground
energy. -/
def Stmt_D04_VariationalPrinciple : Prop :=
  ∀ (n : ℕ) (lam c : Fin n → ℝ) (E0 : ℝ), (∀ i, E0 ≤ lam i) → normSq n c = 1 →
    E0 ≤ rayleigh n lam c

/-- **D05** — the certified bracket, with the mathematics separated from the
numerics. `lower ≤ E0` is an interval-arithmetic enclosure and
`rayleigh ≤ upper` is an evaluated trial state: both are numerical inputs and
stay hypotheses. The Courant-Fischer step between them is `D04`, so it is no
longer assumed. -/
def Stmt_D05_CertifiedBracket : Prop :=
  ∀ (n : ℕ) (lam c : Fin n → ℝ) (E0 lower upper : ℝ),
    (∀ i, E0 ≤ lam i) → normSq n c = 1 →
    lower ≤ E0 → rayleigh n lam c ≤ upper →
    lower ≤ E0 ∧ E0 ≤ upper

end GaugeGap.Variational
