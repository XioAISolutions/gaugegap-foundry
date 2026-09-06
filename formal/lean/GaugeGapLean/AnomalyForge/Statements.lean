import GaugeGapLean.AnomalyForge.Defs

/-!
# Anomaly Forge statements (DAG nodes)

Every node of `formal/lean/dag.json` is a `Prop`-valued definition here.  Proofs
live in `GaugeGapLean/AnomalyForge/Proofs.lean`, so editing a proof never forces
a recompile of anything that only depends on a statement.

Naming: `Stmt_<node id>_<slug>`; the node id is the key used by
`scripts/run_lean_forge.py` and by the Python mirror
`src/gaugegap/anomaly_theorem.py`.

CLAIM BOUNDARY: exact rational identities for the declared finite inventory.
`A08` deliberately records that the uniqueness in `A04`/`A13` *fails* once a
right-handed neutrino is admitted: a one-parameter family survives.
-/

namespace GaugeGap.AnomalyForge

/-- **A01** — gauge-invariant up/down Yukawa terms make the `SU(3)^2-U(1)`
coefficient vanish identically, for every colour count and every hypercharge. -/
def Stmt_A01_SU3Automatic : Prop :=
  ∀ YQ YH : ℚ, su3U1 YQ (YQ + YH) (YQ - YH) = 0

/-- **A02** — the `SU(2)^2-U(1)` condition is equivalent to `YL = -(n * YQ)`. -/
def Stmt_A02_SU2FixesLepton : Prop :=
  ∀ n YQ YL : ℚ, su2U1 n YQ YL = 0 ↔ YL = -(n * YQ)

/-- **A03** — under the Yukawa relations, `YL = -(n * YQ)` and no right-handed
neutrino, the `gravity^2-U(1)` coefficient collapses to `YH - n * YQ`. -/
def Stmt_A03_GravReduces : Prop :=
  ∀ n YQ YH : ℚ,
    gravU1 n YQ (YQ + YH) (YQ - YH) (-(n * YQ)) (-(n * YQ) - YH) 0 = YH - n * YQ

/-- **A04** — uniqueness (division-free form).  The three Yukawa relations plus
`SU(2)^2-U(1)` and `gravity^2-U(1)` cancellation determine the whole assignment
in terms of the Higgs hypercharge `YH`: `n * YQ = YH`, `YL = -YH`,
`n * Yu = YH * (n + 1)`, `n * Yd = YH * (1 - n)`, `Ye = -2 * YH`. -/
def Stmt_A04_Uniqueness : Prop :=
  ∀ n YQ Yu Yd YL Ye YH : ℚ,
    Yu = YQ + YH → Yd = YQ - YH → Ye = YL - YH →
    su2U1 n YQ YL = 0 → gravU1 n YQ Yu Yd YL Ye 0 = 0 →
    n * YQ = YH ∧ YL = -YH ∧ n * Yu = YH * (n + 1) ∧ n * Yd = YH * (1 - n) ∧
      Ye = -2 * YH

/-- **A05** — at the assignment of `A04` the `U(1)^3` coefficient vanishes for
every colour count: the cubic condition is implied, not imposed. -/
def Stmt_A05_U1CubedAutomatic : Prop :=
  ∀ n YQ YH : ℚ, YH = n * YQ →
    u1Cubed n YQ (YQ + YH) (YQ - YH) (-(n * YQ)) (-(n * YQ) - YH) 0 = 0

/-- **A06** — the Standard Model point `n = 3`, `YH = 1/2` is anomaly free. -/
def Stmt_A06_StandardModelPoint : Prop :=
  IsAnomalyFree 3 (1 / 6) (2 / 3) (-(1 / 3)) (-(1 / 2)) (-1) 0

/-- **A07** — the audited perturbation `Yu = 7/10` is rejected, mirroring
`python scripts/run_anomaly_forge.py --y-u 7/10 --require-pass`. -/
def Stmt_A07_PerturbationRejected : Prop :=
  ¬ IsAnomalyFree 3 (1 / 6) (7 / 10) (-(1 / 3)) (-(1 / 2)) (-1) 0

/-- **A08** — admitting a Dirac right-handed neutrino `Yn = YL + YH` destroys
uniqueness: *every* `YQ` gives an anomaly-free assignment, so a one-parameter
family survives.  This is the boundary on `A04`, stated rather than hidden. -/
def Stmt_A08_RightNeutrinoFamily : Prop :=
  ∀ n YQ YH : ℚ,
    IsAnomalyFree n YQ (YQ + YH) (YQ - YH) (-(n * YQ)) (-(n * YQ) - YH)
      (-(n * YQ) + YH)

/-- **A09** — the `A08` family meets the neutrino-free Standard Model exactly
where the right-handed neutrino hypercharge vanishes, i.e. at `YH = n * YQ`. -/
def Stmt_A09_FamilyMeetsStandardModel : Prop :=
  ∀ n YQ YH : ℚ, YH = n * YQ → -(n * YQ) + YH = 0

/-- **A10** — electric charges and composite charges at the Standard Model
point, under `Q = T3 + Y`. -/
def Stmt_A10_ChargeQuantisation : Prop :=
  electricCharge (1 / 2) (1 / 6) = 2 / 3 ∧
  electricCharge (-(1 / 2)) (1 / 6) = -(1 / 3) ∧
  electricCharge (-(1 / 2)) (-(1 / 2)) = -1 ∧
  electricCharge (1 / 2) (-(1 / 2)) = 0 ∧
  protonCharge (1 / 6) = 1 ∧
  neutronCharge (1 / 6) = 0

/-- **A11** — Witten global `SU(2)` parity: three generations of three colours
give twelve left-handed doublets (even, admissible), while two colours give
nine (odd, inadmissible). -/
def Stmt_A11_WittenParity : Prop :=
  weakDoublets 3 3 = 12 ∧ Even (weakDoublets 3 3) ∧
  weakDoublets 2 3 = 9 ∧ ¬ Even (weakDoublets 2 3)

/-- **A12** — the generation factor is a nonzero scalar, so the per-generation
coefficients used here decide the generation-universal ones. -/
def Stmt_A12_GenerationScaling : Prop :=
  ∀ g A : ℚ, g ≠ 0 → (g * A = 0 ↔ A = 0)

/-- **A13** — flagship statement.  The three Yukawa relations together with the
`SU(2)^2-U(1)` and `gravity^2-U(1)` conditions pin the assignment *and* leave
the remaining two coefficients cancelling automatically. -/
def Stmt_A13_MainTheorem : Prop :=
  ∀ n YQ Yu Yd YL Ye YH : ℚ,
    Yu = YQ + YH → Yd = YQ - YH → Ye = YL - YH →
    su2U1 n YQ YL = 0 → gravU1 n YQ Yu Yd YL Ye 0 = 0 →
    n * YQ = YH ∧ IsAnomalyFree n YQ Yu Yd YL Ye 0

end GaugeGap.AnomalyForge
