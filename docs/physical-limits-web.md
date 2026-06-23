# The web of physical limits — a synthesis

> Five "mind-blowing physics" reels, each reduced to its rigorous, certifiable core,
> and shown to be **one structure**.

![The web of physical limits](../figures/physical-limits/web.svg)

This document is the reviewer-facing single source for the physical-limits work. It
adds no new physics — it narrates how the seven finite-system modules in this repo
fit together. Each was built by stripping a viral physics reel down to the one
genuine, finite, exactly computable statement it contains, and certifying that
statement with a discharged Lean 4 / Coq inequality. Run it all with
`make physical-limits` (consolidated report) and `make physical-limits-figures`
(these diagrams + a self-contained `index.html` gallery).

## The one idea

Every module is the same kind of object: a **trade-off inequality** among four
currencies —

- **Energy**, **Time**, **Information / entropy**, **Geometry**.

Plot the currencies as nodes and the phenomena as the edges (and one face) that
connect them, and the five reels stop being five curiosities and become a single
connected web. Two **keystones** supply the connective tissue:

- **Landauer's principle** welds *information* to *energy/thermodynamics*.
- **The Bekenstein bound** welds *information* and *energy* to *geometry*.

## The seven phenomena

Each row below is a member of the [consolidated capstone](physical-limits.md)
(`scripts/run_physical_limits.py`, 7/7 checks pass) with its own module, tests, and
machine-checked certificate.

![Certificate ladder](../figures/physical-limits/ladder.svg)

| # | Phenomenon | Reel it came from | Currencies | Certified inequality | Module |
|---|---|---|---|---|---|
| 1 | Quantum speed limit | attosecond entanglement | time ↔ energy | `t ≥ τ_QSL` | [`entanglement_speed_limit`](entanglement-speed-limit.md) |
| 2 | Temporal double slit | time diffraction (2023) | time ↔ frequency | `Δω = 2π/Δt`, `σ_t σ_ω ≥ ½` | [`temporal_double_slit`](temporal-double-slit.md) |
| 3 | Ergotropy / passivity | bismuth "free energy" | work ↔ entropy | `0 ≤ W ≤ ⟨H⟩−E₀` | [`ergotropy`](ergotropy.md) |
| 4 | Decoherence / branching | "no single Creator" | information | `1 ≤ N_eff ≤ d` | [`decoherence_branching`](decoherence-branching.md) |
| 5 | Landauer's principle | (keystone) | info ↔ energy | `W ≥ k_B T ln 2` | [`landauer`](physical-limits.md) |
| 6 | Bekenstein bound | (keystone) | info ↔ energy ↔ geometry | `S ≤ 2π R E` | [`bekenstein`](physical-limits.md) |
| 7 | Alcubierre energy cond. | warp drive | energy ↔ geometry | `ρ ≤ 0` | [`relativity.alcubierre`](alcubierre-warp.md) |
| 8 | Sonification / sampling | "hearing" data | time ↔ frequency | aliasing fold `0 < f_s − f < f_s/2` | [`sonification`](../src/gaugegap/quantum/sonification.py) |
| 9 | Cherenkov cone | faster-than-light-in-medium | velocity ↔ geometry | `cos θc = 1/(nβ)`, `β > 1/n` | [`cherenkov`](cherenkov.md) |
| 10 | Lieb–Robinson cone | "instant" entanglement | information ↔ time | `x(t) ≤ v_LR·t + ξ` | [`lieb_robinson`](lieb-robinson.md) |
| 11 | Compton–Schwarzschild | cosmic mass–radius diagram | mass ↔ geometry | `R² ≥ R_s·λ_C = 2 ℓ_P²` | [`relativity.compton_schwarzschild`](physical-limits.md) |

### How the edges connect

- **Time ↔ Energy** — the Fourier-dual pair. The quantum speed limit
  (`t ≥ ℏ·angle/ΔE`) and the temporal double slit (`Δω = 2π/Δt`) are the *same*
  duality seen as a dynamical floor and as an interference pattern.
- **Work ↔ Entropy / Info ↔ Energy** — ergotropy is the work you *can* extract from a
  state; Landauer is the work you *must* pay to erase the entropy that decoherence
  creates. They are two faces of the same energy↔information ledger, and together
  they are why "free energy" and "perpetual motion" are impossible.
- **Information** — decoherence turns a coherent superposition (one quantum state)
  into `N_eff` effectively-classical branches; the bracket `1 ≤ N_eff ≤ d` quantifies
  the "web of possibilities" without any metaphysics.
- **Info ↔ Energy ↔ Geometry** — the Bekenstein bound caps the information a region
  can hold given its energy and size: geometry limits information.
- **Energy ↔ Geometry** — the Alcubierre metric shows that bending spacetime into a
  warp bubble *requires* negative energy density (`ρ ≤ 0` everywhere in the wall).
- **Mass ↔ Geometry** — the cosmic mass–radius diagram: every object is hemmed in by
  the Schwarzschild radius (`R ≥ 2GM/c²`, or it is a black hole) and the Compton
  wavelength (`R ≥ ℏ/Mc`, or the vacuum pair-produces). The two cross at the Planck
  point, with the *mass-independent* identity `R_s·λ_C = 2 ℓ_P²` — so `R ≥ √2 ℓ_P` is a
  floor on the size of anything. This is the global map the other geometry members live
  inside.

![Cosmic mass–radius diagram](../figures/physical-limits/mass_radius.svg)

## What stayed honest

The point of the exercise was as much about **what we refused to claim** as what we
built:

- The "no single Creator" reel → we built decoherence/branching and stated plainly it
  says nothing about any deity. (Metaphysics is not a result.)
- The bismuth "free energy / anti-gravity" reel → we built the *refutation*
  (ergotropy), and noted bismuth diamagnetic levitation is real but stores no free
  energy.
- The Alcubierre reel → we certified the negative-energy requirement and the
  Ford–Roman obstruction; we did **not** claim a buildable warp drive or FTL travel.

Every certificate is a single discharged inequality with one labelled trust input and
no holes (`linarith` / `lra` / `nlinarith` / `nra`); every claim is bounded by a
`claim_boundary_audit --strict` gate at 0 high.

## Reproduce

```bash
make physical-limits          # the consolidated 7-member report (all checks pass)
make physical-limits-figures  # web.svg, ladder.svg, and a self-contained index.html
```

The gallery (`figures/physical-limits/index.html`) embeds the web diagram, the
certificate ladder, and every module's own result figure with captions.

## Claim boundary

Finite-system / semiclassical demonstrations of **established** physical bounds, each
bracketed or machine-checked. Not continuum / Yang–Mills / Millennium claims; not a
buildable warp drive or free-energy device; the Bekenstein bound is applied as an
info–energy–geometry consistency relation, not a derivation of holography.
Dependency-light (numpy); deterministic SVG.
