# Decoherence and branching

The honest, rigorous core of the "web of possibilities / branching realities" idea —
**without** any metaphysical claim. A quantum superposition is a single coherent
state (a web of weighted possibilities, the Born weights). When it entangles with an
environment that records which pointer state it occupies, the off-diagonal coherences
decay (**decoherence**) and the system behaves like a set of effectively-classical
**branches** (Zurek's einselection; the mechanism behind Everett branching).

Continues the entanglement arc directly: decoherence *is* system–environment
entanglement.

## What it computes

For a `d`-level pointer in an equal superposition, each of `n_env` environment
registers records the pointer value with per-register overlap `o`, giving the exact
reduced system state

```
rho[k,k] = 1/d,   rho[j,k] = (1/d) o^n_env   (j != k)
```

`gaugegap.quantum.decoherence_branching`:
- `branch_density_matrix(d, n_env, overlap)` — the exact reduced state.
- `coherence_l1`, `purity`, `born_weights`, `effective_branches` (`= 1/Tr(rho^2)`).
- `decoherence_sweep(...)` — coherence and branch count vs environment size.
- `verify_reduced_state(...)` — validates the analytic state against the partial
  trace of the literal statevector (agreement to ~1e-16).
- `analyze_branching(...)` — emits a discharged Lean 4 / Coq certificate that
  `1 <= N_eff <= d` (trust inputs: the participation-ratio bounds; discharged by
  `linarith` / `lra`).

```bash
make decoherence-branching
python scripts/run_decoherence_branching.py --d 4 --overlap 0.6
```

As `n_env` grows, the l1 coherence falls to ~0 and `N_eff` rises from **1** (one
coherent quantum state) to **d** (d decohered classical branches). The Born weights
always sum to 1 (probability conserved).

## Claim boundary

A **finite, exact model of a physical mechanism** (decoherence / einselection). It
demonstrates *how* classical branch structure emerges from entanglement with an
environment and makes **no metaphysical claim** — nothing here speaks to the
existence or nature of any creator, deity, or "the universe as a whole." That is
philosophy, not a result this (or any) physics computation delivers. Dependency-light
(numpy). Not a continuum/Millennium claim.

References: Zurek, *Rev. Mod. Phys.* **75** (2003) 715; Joos & Zeh, *Z. Phys. B*
**59** (1985) 223; Everett, *Rev. Mod. Phys.* **29** (1957) 454.
