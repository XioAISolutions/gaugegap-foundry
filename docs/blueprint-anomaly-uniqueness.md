# Blueprint: hypercharge uniqueness in the Anomaly Forge

Formalisation target for `formal/lean`. This is the written argument that the
Lean statements in `formal/lean/GaugeGapLean/AnomalyForge/Statements.lean`
encode, node by node.

## Claim boundary

Exact rational anomaly-cancellation conditions for a **declared finite chiral
field inventory**: one generation of `n` colours carrying `Q`, `u`, `d`, `L`,
`e`, optionally a Dirac right-handed neutrino, and one Higgs doublet. Nothing
here is a statement about arbitrary chiral gauge theories, about the continuum
limit, or about any Millennium Prize problem. The uniqueness result below is
uniqueness *under the listed assumptions*; node A08 records that it fails as
soon as a right-handed neutrino is admitted.

## Setup

Right-handed fields enter through their left-handed conjugates, matching
`src/gaugegap/anomaly_audit.py`. Per generation, with `n` colours:

```text
SU(3)^2-U(1)   = 2Y_Q - Y_u - Y_d
SU(2)^2-U(1)   = n Y_Q + Y_L
U(1)^3         = 2n Y_Q^3 - n Y_u^3 - n Y_d^3 + 2Y_L^3 - Y_e^3 - Y_nu^3
gravity^2-U(1) = 2n Y_Q - n Y_u - n Y_d + 2Y_L - Y_e - Y_nu
```

The generation factor `N_g` multiplies all four and is nonzero, so per-generation
cancellation decides the generation-universal statement (node A12). A missing
right-handed neutrino is modelled by `Y_nu = 0`, which is faithful because the
field enters only through `Y_nu` and `Y_nu^3`.

Gauge invariance of the three Yukawa terms with a single Higgs doublet of
hypercharge `Y_H` gives:

```text
Y_u = Y_Q + Y_H      Y_d = Y_Q - Y_H      Y_e = Y_L - Y_H
```

`Y_H` is a normalisation convention, not an extra fact: every condition below is
homogeneous, so the assignment is fixed only up to overall scale. The Standard
Model numbers come from `n = 3`, `Y_H = 1/2`.

## Lemmas

**Lemma 1 (A01).** Substituting `Y_u = Y_Q + Y_H`, `Y_d = Y_Q - Y_H` into
`2Y_Q - Y_u - Y_d` gives `0` identically. The `SU(3)^2-U(1)` condition carries
no information once the Yukawa terms are gauge invariant.

**Lemma 2 (A02).** `n Y_Q + Y_L = 0` iff `Y_L = -n Y_Q`. One rearrangement.

**Lemma 3 (A03).** Substituting the Yukawa relations, `Y_L = -n Y_Q`,
`Y_e = Y_L - Y_H` and `Y_nu = 0` into the gravitational coefficient collapses it
to `Y_H - n Y_Q`. Every quark term cancels; what survives is one linear
equation.

**Lemma 4 (A04, uniqueness).** The three Yukawa relations together with
`SU(2)^2-U(1) = 0` and `gravity^2-U(1) = 0` force

```text
n Y_Q = Y_H     Y_L = -Y_H     n Y_u = Y_H (n+1)     n Y_d = Y_H (1-n)     Y_e = -2 Y_H
```

Stated in this division-free form the lemma needs no `n != 0` hypothesis. This
is the content of the informal claim "the assignment is unique": two conditions
plus Yukawa gauge invariance leave a one-dimensional ray, and `Y_H` fixes the
point on it.

**Lemma 5 (A05).** At that assignment the cubic coefficient vanishes for every
`n`: the `(1+n)^3 + (1-n)^3 = 2 + 6n^2` collapse cancels the `-2n^3` from `Y_L`
against the `+8n^3` from `Y_e`. So `U(1)^3` is implied, not imposed — the
interesting part of the statement, since the cubic is the only nonlinear
condition.

**Lemma 6 (A06, A10).** Specialising to `n = 3`, `Y_H = 1/2` gives
`(1/6, 2/3, -1/3, -1/2, -1)`, electric charges `2/3, -1/3, -1, 0` under
`Q = T3 + Y`, and composite charges proton `= 1`, neutron `= 0`.

**Lemma 7 (A07).** The perturbation `Y_u = 7/10` audited by
`scripts/run_anomaly_forge.py --y-u 7/10 --require-pass` fails `SU(3)^2-U(1)`
(the coefficient is `-1/30`), so the audit is not trivially satisfiable.

**Lemma 8 (A08, the boundary).** Admit a Dirac right-handed neutrino,
`Y_nu = Y_L + Y_H`. Then all four coefficients vanish **identically in `Y_Q`**:
the gravitational condition cancels against the new `-Y_nu` term, and in the
cubic the `(nY_Q + Y_H)^3 + (nY_Q - Y_H)^3` pair cancels the rest. Uniqueness is
gone; a one-parameter family (a hypercharge / `B-L` admixture) remains, matching
`status = "underdetermined_family"` in `src/gaugegap/hypercharge_solver.py`.

**Lemmas 11-14 (A14-A17): what that family is.** Saying uniqueness fails is only
half a statement; these say what replaces it. Cleared of denominators, write

```text
Y_SM(n) = (1, 1+n, 1-n, -n, -2n, 0)        the hypercharge direction
Y_BL(n) = (1, 1, 1, -n, -n, -n)            the B - L direction
```

`Y_SM(3)` is six times the Standard Model assignment `(1/6, 2/3, -1/3, -1/2, -1, 0)`,
and `Y_BL(3)` is three times `B - L = (1/3, 1/3, 1/3, -1, -1, -1)`.

- **A14** — every family member satisfies
  `n * Y(x, h) = h * Y_SM(n) + (n*x - h) * Y_BL(n)`. Cleared of denominators, so
  no hypothesis on `n` is needed.
- **A15** — `Y_BL(n)` is anomaly free on its own. This is *why* the family
  exists: with a right-handed neutrino, `B - L` becomes gaugeable, so any
  multiple of it can be added to a solution and it stays a solution.
- **A16** — `Y_SM(n)` is anomaly free, with the right-handed neutrino
  hypercharge vanishing, recovering Lemma 9.
- **A17** — the two directions are independent for `n != 0`, so A14 exhibits a
  genuine plane rather than a disguised line.

Together: the anomaly-free assignments for this inventory are exactly the span
of hypercharge and `B - L`, a two-dimensional space. A15 and A16 are derived
from A08 rather than reproved, which is what the two DAG edges record.

Boundary: this is the solution space *for the declared inventory with generation-
universal charges and the stated Yukawa terms*. It says nothing about which
member nature chose, and nothing about theories outside this inventory.

**Lemma 9 (A09).** That family meets the neutrino-free Standard Model exactly
where `Y_nu = -n Y_Q + Y_H = 0`, i.e. at `Y_H = n Y_Q` — the Lemma 4 point.

**Lemma 10 (A11).** Witten global `SU(2)` parity: `n` coloured quark doublets
plus one lepton doublet per generation gives `N_g (n + 1)` left-handed doublets;
`3 x 4 = 12` is even and admissible, `3 x 3 = 9` is odd and is not.

**Theorem (A13).** Combining Lemma 4 and Lemma 5: the Yukawa relations plus
`SU(2)^2-U(1) = 0` and `gravity^2-U(1) = 0` pin the assignment and leave the
other two coefficients cancelling on their own.

## Node table

| Node | Statement | Depends on | Content |
|---|---|---|---|
| A01 | `Stmt_A01_SU3Automatic` | — | Lemma 1 |
| A02 | `Stmt_A02_SU2FixesLepton` | — | Lemma 2 |
| A03 | `Stmt_A03_GravReduces` | — | Lemma 3 |
| A04 | `Stmt_A04_Uniqueness` | — | Lemma 4 |
| A05 | `Stmt_A05_U1CubedAutomatic` | — | Lemma 5 |
| A06 | `Stmt_A06_StandardModelPoint` | — | Lemma 6 |
| A07 | `Stmt_A07_PerturbationRejected` | — | Lemma 7 |
| A08 | `Stmt_A08_RightNeutrinoFamily` | — | Lemma 8 |
| A09 | `Stmt_A09_FamilyMeetsStandardModel` | — | Lemma 9 |
| A10 | `Stmt_A10_ChargeQuantisation` | — | Lemma 6 |
| A11 | `Stmt_A11_WittenParity` | — | Lemma 10 |
| A12 | `Stmt_A12_GenerationScaling` | — | generation factor |
| A13 | `Stmt_A13_MainTheorem` | A04, A05 | Theorem |
| A14 | `Stmt_A14_FamilySpannedByHyperchargeAndBL` | — | Lemma 11 |
| A15 | `Stmt_A15_BLDirectionAnomalyFree` | A08 | Lemma 12 |
| A16 | `Stmt_A16_HyperchargeDirectionAnomalyFree` | A08 | Lemma 13 |
| A17 | `Stmt_A17_DirectionsIndependent` | — | Lemma 14 |

`scripts/run_lean_forge.py` checks the dependency column against the proof terms
actually referenced: a declared edge that the proof does not use, or a use that
is not declared, fails the gate. This target is a
finite equational problem, so its DAG is wide and shallow. It is not comparable
in scale to a formalisation like the recent Fermat's Last Theorem effort, and
the DAG here earns its place as a consistency check, not as a scheduling
device for many agents.

## What is checked, and by what

| Layer | Tool | What it establishes |
|---|---|---|
| Structure | `scripts/run_lean_forge.py` | every node has a statement, a proof, honest dependencies, no `sorry`/`axiom`/`native_decide` |
| Mirror | `src/gaugegap/anomaly_theorem.py` | the same statements restated over `Fraction` and checked on a 100-point grid — catches a wrong statement, replaces nothing |
| Kernel | `lake build` | Lean accepts the proofs |

Only the third layer is a machine check of the mathematics. Until it runs, the
report records `toolchain_missing` and every node stays unverified; there is no
code path that reports a verified node without a successful `lake build`.

CI commits the regenerated report and figure on the default branch once that
build passes, so `main` carries the kernel's own output. A test fails if the
committed report's source hashes stop matching the files, so the checked-in
evidence can be honest or absent but never stale.

## Reproduce

```bash
foundry run lean-forge          # structure + mirror, plus lake build if available
foundry run lean-dag-figure     # figures/anomaly-forge/lean-dag.svg
```

With a Lean toolchain installed:

```bash
cd formal/lean && lake exe cache get && lake build
python scripts/run_lean_forge.py --require-verified
```

CI runs the same gate in the `compile-lean` job of
`.github/workflows/verify-proofs.yml`.
