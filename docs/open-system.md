# Finite open-system (Lindbladian) steady states

Dependency-light (numpy) open-system support: vectorize the Lindblad master equation
into a Liouvillian superoperator, find the steady state from its null space, and
report the dissipative relaxation spectrum.

```python
from gaugegap.quantum.open_system import solve_open_system
res = solve_open_system(H, jumps)   # res.steady_state, res.relaxation_gap, ...
```

```bash
make open-system
python scripts/run_open_system.py --n-sites 2 --gamma 0.3
```

- `lindbladian_superoperator(H, jumps)` — vectorized Liouvillian (column-stacking).
- `steady_state(L)` — density matrix from the null space (Hermitian, PSD, trace 1).
- `relaxation_spectrum(L)` — eigenvalues (Re ≤ 0); the dissipative gap.
- Cross-validated against long-time `exp(Lt)` evolution and the analytic
  amplitude-damping case (steady state → |0⟩⟨0|).

Optional QuTiP cross-check via the `[open-quantum]` extra (the numpy path needs no
deps).

**Claim boundary:** exact finite-dimensional open-system computation, cross-
validated against the exact dynamics. The Liouvillian is non-Hermitian, so this is
not interval-certified like the Hermitian spectral kernel — it is an exact numpy
result with cross-checks. Not a continuum/Millennium claim.
