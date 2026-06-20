# The Certified-Quantum program

GaugeGap Foundry's quantum results are not just *logged* — they are **bracketed,
cross-validated, or machine-checkable against the verified interval kernel**. This is
the index to that program (Phases 1-5).

| Phase | Primitive | Doc / module |
|---|---|---|
| 1 | Certified energy/gap bracket (interval lower + Krylov-Ritz upper + Lean/Coq) | `docs/certified-bracket.md`, `certified_bracket.py` |
| 2 | Certified classical shadows (median-of-means CIs, cross-validated) | `docs/certified-shadows.md`, `quantum/certified_shadows.py` |
| 3 | Certified-quantum stack: Spectra `certify_quantum`, gauge ops in the registry, quantum error budget | `docs/spectra-language.md`, `quantum_validation.py` |
| 4 | QSVT eigenvalue transform (polynomial-of-spectrum, certified via interval arithmetic) | `docs/qsvt.md`, `quantum/qsvt.py` |
| 5 | Temple-Kato bracket (trial-state lower bound); Lindbladian open systems; staged hardware | `docs/temple-bracket.md`, `docs/open-system.md`, `docs/hardware-runbook.md` |

## One-shot capstone

`make certified-quantum` (`scripts/run_certified_quantum_report.py`) runs **every**
primitive on one operator and emits a single consolidated, claim-boundary-audited
report with an all-checks-pass summary:

```bash
python scripts/run_certified_quantum_report.py --operator berry_keating_xp --n-basis 8
```

On `berry_keating_xp` (n=8) all seven checks pass: both brackets contain the exact
E0, ESPRIT/Krylov estimates are certified, shadow CIs cover the exact observables,
the QSVT transform is certified, the error budget is source-separated, and the
open-system steady state is valid.

## Honest scope

Finite-system, simulation-level throughout. Rigorous bounds are the certified
interval enclosures and the variational/Temple bounds; statistical claims carry
confidence intervals; the Liouvillian path is exact-but-cross-validated (non-
Hermitian). Optional deps (cvxpy `[sdp]`, qutip `[open-quantum]`) are capability-
gated. Real-hardware runs stay staged behind the `hardware_confirmed` gate; nothing
is fabricated. No continuum / Yang-Mills / Millennium claims.
