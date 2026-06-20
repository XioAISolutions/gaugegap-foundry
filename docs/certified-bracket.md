# Certified energy/gap bracket

A two-sided, machine-checkable bracket on a finite-matrix eigenvalue: a **rigorous
lower bound** from the verified interval-arithmetic kernel combined with a
**rigorous upper bound** from a quantum subspace eigensolver.

## Why both bounds are rigorous

- **Lower bound.** `gaugegap.curverank_registry.build_certified_general(H)` returns
  directed-rounding interval enclosures that provably contain each eigenvalue; the
  lower endpoint bounds the eigenvalue from below.
- **Upper bound.** By the Courant–Fischer min–max principle, the k-th **Ritz value**
  of any subspace is an upper bound on the k-th eigenvalue. The quantum Krylov
  eigensolver (`quantum/quantum_subspace_methods.quantum_krylov_method`) supplies
  these Ritz values — the quantum method genuinely contributes the upper bound.

So `E_k ∈ [certified_lower_k, ritz_upper_k]`, and for the gap
`E1 − E0 ∈ [E1.lower − E0.upper, E1.upper − E0.lower]`.

## Use it

```python
from gaugegap.certified_bracket import certified_ground_bracket, certified_gap_bracket
from gaugegap.curverank_registry import get_operator
H = get_operator("berry_keating_xp").build(8)
b = certified_ground_bracket(H)      # b.lower <= E0 <= b.upper
g = certified_gap_bracket(H)         # g["gap_bracket"]
```

```bash
make certified-bracket
python scripts/run_certified_bracket.py --operator berry_keating_xp --n-basis 8
```

The CLI cross-checks that the exact eigenvalue lies inside the bracket and emits a
**discharged Lean 4 / Coq certificate** of `lower ≤ E0 ≤ upper`
(`gaugegap.rigorous.bracket_certificate.emit_bracket_certificate`): two labelled
trust inputs (the certified lower bound; the variational upper bound) and a
`linarith` / `lra` proof with no holes.

## Claim boundary

A rigorous bracket on a **finite** matrix's eigenvalue/gap, at **simulation** level.
It is not a continuum, Yang-Mills, or Millennium-Prize claim. The lower bound is
certified by the interval kernel; the upper bound is a variational (Ritz) value —
both standard, exact facts.
