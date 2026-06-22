# Temporal double-slit (time diffraction)

The temporal twin of Young's double slit, and a new face of the
[physical-limits web](physical-limits.md): the **time ↔ frequency** currency.

Two **time slits** — short windows in time, separation `Δt` — make a probe interfere
in the **frequency** spectrum (not in space), with fringe spacing

```
Δω = 2π / Δt.
```

This is exact time-frequency Fourier duality: the field from two slits at `±Δt/2` is
`E(ω) = 2 E_slit(ω) cos(ω Δt/2)`, so the intensity carries a `cos²(ω Δt/2)` fringe
pattern of period `2π/Δt`. A single time slit of width `σ_t` sets the spectral
envelope, obeying the time-bandwidth uncertainty `σ_t σ_ω ≥ 1/2` — the Fourier-dual
sibling of the Mandelstam–Tamm quantum speed limit.

`gaugegap.quantum.temporal_double_slit`:
- `time_slits`, `spectrum` — build the two-slit probe and its power spectrum (FFT).
- `recover_separation` — read `Δt` back off the fringes (FFT of the spectrum peaks at
  the conjugate "time" `Δt`, the temporal analog of reading slit separation off
  spatial fringes); reproduces `Δt` to `< 10⁻²` relative error across a sweep.
- `temporal_std`, `spectral_std`, `time_bandwidth_product`.
- `analyze_time_diffraction(...)` — emits a discharged Lean 4 / Coq certificate of the
  time-bandwidth bound `σ_t σ_ω ≥ 1/2` (`nlinarith` / `nra`, no holes); a Gaussian
  slit saturates it exactly.

```bash
make temporal-double-slit
python scripts/run_temporal_double_slit.py --dt 8 --tau 0.6
```

## Claim boundary

A finite, exact classical-field / Fourier simulation of the time-diffraction
**principle**. It is **not** a reproduction of the ITO thin-film experiment (Tirole,
Vezzoli et al., *Nat. Phys.* **19** (2023) 999), its material response, or its
specific numbers; the time-bandwidth inequality is an exact theorem of Fourier
analysis. Dependency-light (numpy). Not a continuum/Millennium claim.

References: Tirole, Vezzoli et al., *Nat. Phys.* **19** (2023) 999 ("Double-slit time
diffraction at optical frequencies"); Gabor (1946).
