# SMT verification of the certificates

The repo emits certificates as discharged Lean 4 / Coq (a single labelled trust
input, no `sorry`/`Admitted`). CI greps those artifacts for holes, but it does not run
a proof assistant. This layer adds a second, **automated** witness: an SMT solver
(z3) independently proves each certified inequality valid over the reals — the negated
conclusion is unsatisfiable.

So each statement in the [physical-limits web](physical-limits-web.md) now has two
independent backings: the discharged proof-assistant text *and* an automated z3 proof.

## What is checked

Each schema is encoded in its **meaningful** mathematical form (not the axiomatised
restatement), so z3 verifies the real content of the theorem:

| Schema | Verified implication |
|---|---|
| eigenvalue bracket | `lo ≤ E0`, `E0 ≤ up` ⟹ `lo ≤ E0 ≤ up` |
| speed limit | `t ≥ τ_MT`, `t ≥ τ_ML` ⟹ `t ≥ max(τ_MT, τ_ML)` |
| time–bandwidth | `σ_t > 0`, `σ_ω ≥ 1/(2σ_t)` ⟹ `σ_t σ_ω ≥ 1/2` |
| ergotropy | `E0 ≤ E_passive ≤ ⟨H⟩`, `W = ⟨H⟩−E_passive` ⟹ `0 ≤ W ≤ ⟨H⟩−E0` |
| branching | `1/d ≤ purity ≤ 1`, `N·purity = 1` ⟹ `1 ≤ N ≤ d` |
| Landauer | `k_B,T>0`, `ΔS ≥ b`, `W = k_B T ΔS` ⟹ `W ≥ k_B T b` |
| Bekenstein | `E>0`, `R ≥ S/(2πE)` ⟹ `S ≤ 2πRE` |
| warp energy condition | `K,σ²≥0`, `π>0`, `ρ = −(1/8π)Kσ²` ⟹ `ρ ≤ 0` |

`π` is modelled as an abstract positive constant (only positivity is used). The
nonlinear schemas (Landauer, Bekenstein, warp, branching, time–bandwidth) use z3's
nonlinear real arithmetic.

```bash
pip install -e '.[smt]'        # or .[dev]
make verify-certificates       # python scripts/verify_certificates.py
```

The runner prints a pass/fail line per schema and exits non-zero if any schema fails
to verify; the CI `smt-verify` job runs it on every push.

## Claim boundary

z3 verifies the **real-arithmetic validity** of finite-system inequalities — an
automated cross-check of the certificates, not a new physical claim. It does not
re-derive the physics (that is what the modules and their tests do); it confirms that
each certified inequality is a valid theorem given its stated trust inputs.
