-- The whole library is imported deliberately: these files are tiny, the
-- Mathlib cache supplies the oleans, and a narrower import set is one more
-- thing to get wrong in a proof nobody can rerun locally without a toolchain.
import Mathlib

/-!
# Anomaly Forge definitions

Exact rational gauge-anomaly coefficients for a *declared finite chiral field
inventory*: one generation of `n` colours with left-handed quark doublet `Q`,
right-handed `u`, `d`, left-handed lepton doublet `L`, right-handed `e`, and an
optional right-handed neutrino `Yn` (absent is modelled by `Yn = 0`, which is
faithful because a right-handed neutrino contributes to every coefficient below
only through `Yn` and `Yn ^ 3`).

Right-handed fields enter through their left-handed conjugates, matching
`src/gaugegap/anomaly_audit.py`.  The overall generation factor `N_g` is a
nonzero scalar multiple and is handled separately by
`Stmt_A12_GenerationScaling`, so everything here is per generation.

CLAIM BOUNDARY: these are exact rational cancellation conditions for the
declared inventory.  Nothing here is a statement about every possible chiral
gauge theory, about the continuum, or about any Millennium Prize problem.
-/

namespace GaugeGap.AnomalyForge

/-- `SU(3)^2-U(1)` coefficient (per generation). -/
def su3U1 (YQ Yu Yd : ℚ) : ℚ := 2 * YQ - Yu - Yd

/-- `SU(2)^2-U(1)` coefficient (per generation). -/
def su2U1 (n YQ YL : ℚ) : ℚ := n * YQ + YL

/-- `gravity^2-U(1)` coefficient (per generation). -/
def gravU1 (n YQ Yu Yd YL Ye Yn : ℚ) : ℚ :=
  2 * n * YQ - n * Yu - n * Yd + 2 * YL - Ye - Yn

/-- `U(1)^3` coefficient (per generation). -/
def u1Cubed (n YQ Yu Yd YL Ye Yn : ℚ) : ℚ :=
  2 * n * YQ ^ 3 - n * Yu ^ 3 - n * Yd ^ 3 + 2 * YL ^ 3 - Ye ^ 3 - Yn ^ 3

/-- All four registered local coefficients vanish. -/
def IsAnomalyFree (n YQ Yu Yd YL Ye Yn : ℚ) : Prop :=
  su3U1 YQ Yu Yd = 0 ∧
  su2U1 n YQ YL = 0 ∧
  gravU1 n YQ Yu Yd YL Ye Yn = 0 ∧
  u1Cubed n YQ Yu Yd YL Ye Yn = 0

/-- Electric charge from the `Q = T3 + Y` convention. -/
def electricCharge (T3 Y : ℚ) : ℚ := T3 + Y

/-- Charge of the `uud` composite. -/
def protonCharge (YQ : ℚ) : ℚ := 3 * YQ + 1 / 2

/-- Charge of the `udd` composite. -/
def neutronCharge (YQ : ℚ) : ℚ := 3 * YQ - 1 / 2

/-- Left-handed weak doublets for `g` generations of `n` colours:
`n` coloured quark doublets plus one lepton doublet per generation. -/
def weakDoublets (n g : ℕ) : ℕ := g * (n + 1)

end GaugeGap.AnomalyForge
