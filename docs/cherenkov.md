# Cherenkov radiation: a certified local speed limit

The honest core of the Cherenkov reel (the blue glow in reactor pools), and the
**velocity ↔ geometry** edge of the [physical-limits web](physical-limits-web.md).

In a medium of refractive index `n`, light travels at `c/n`, so a charged particle
with speed `βc` can exceed the *local* light speed when `β > 1/n`. It then outruns the
spherical wavefronts it emits, which pile into a coherent cone (the optical sonic boom)
with

```
cos(θ_c) = 1 / (n β),
```

real only at/above the threshold `β = 1/n` (`nβ ≥ 1`). This is a local speed limit
(`c/n`) whose breach has an exact geometric signature — sibling to the quantum speed
limit (time ↔ energy) and the Alcubierre energy condition (energy ↔ geometry).

`gaugegap.quantum.cherenkov`:
- `cherenkov_threshold(n)`, `emits(n, β)`, `cone_angle(n, β)` — the closed-form geometry.
- `wavefront_cone(n, β, ...)` — simulates the spherical wavefronts emitted along the
  track and **recovers the cone angle from the resulting point cloud** (the envelope
  tangent from the apex), independent of the closed form.
- `analyze_cherenkov(...)` — verifies the recovered `cos θ_c` matches `1/(nβ)` (to
  ~1e-2 or better) and emits a discharged Lean 4 / Coq certificate that the cone cosine
  is valid (`0 < cos θ_c ≤ 1`) at/above threshold; the schema is also added to the
  [z3 verifier](certificate-verification.md).

```bash
make cherenkov
python scripts/run_cherenkov.py --n 1.33 --beta 0.9
```

For water (`n ≈ 1.33`) at `β = 0.9`, the threshold is `β ≈ 0.752`, the particle emits,
and `θ_c ≈ 33°` — recovered from the wavefront pile-up to ~1e-6.

## Claim boundary

A finite, exact classical-electromagnetism / geometry demonstration of the Cherenkov
**principle**. It is **not** a reproduction of any detector (RICH, Super-Kamiokande,
atmospheric telescopes) or its numbers, and the spectral "why it's blue" weighting is
not modelled. The cone relation and threshold are exact theorems. Dependency-light
(numpy); nothing about simulateitnow.com beyond visual inspiration. Not a
continuum/Millennium claim.

References: Cherenkov (1934); Frank & Tamm (1937); Jackson, *Classical Electrodynamics*.
