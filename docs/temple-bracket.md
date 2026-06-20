# Temple-Kato certified ground-energy bracket

A rigorous two-sided bracket on the ground energy E0, built entirely from a quantum
trial state — complementing the interval-kernel bracket (`docs/certified-bracket.md`).

For any normalized trial state with mean `<H>` and variance `Var(H)`, and any
rigorous lower bound `mu` on the first excited energy E1, the **Temple inequality**
gives, whenever `<H> < mu`:

    E0 >= <H> - Var(H) / (mu - <H>).

With the variational upper bound `<H> >= E0`, this brackets E0 from the trial state
alone: `E0 in [temple_lower, <H>]`. We take `mu` from the certified interval
enclosure of E1, prepare the trial state by imaginary-time evolution, and emit a
discharged Lean 4 / Coq certificate of `lower <= E0 <= upper`.

```bash
make temple-bracket
python scripts/run_temple_bracket.py --operator z2 --n-basis 3
```

```python
from gaugegap.quantum.temple_kato import certified_temple_bracket
b = certified_temple_bracket(H)   # b.lower <= E0 <= b.upper, b.contains_exact
```

**Optional** SDP cross-check (`gaugegap.quantum.dual_vqe`, cvxpy-gated via the
`[sdp]` extra): `E0 = max{t : H - tI >= 0}`. For finite matrices the interval kernel
is tighter and rigorous; the SDP is the dual-VQE-style cross-check.

**Claim boundary:** rigorous finite-matrix bracket from a simulation-level trial
state. Dependency-light (numpy). Not a continuum/Millennium claim.
