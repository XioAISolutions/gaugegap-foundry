# Physical-limits capstone: the web of fundamental bounds

The unifying layer. Every reel-derived module turns out to be a **trade-off
inequality among the same four currencies — energy, time, information/entropy, and
geometry**. This capstone introduces the two keystones that connect them into one web
and runs the whole set on finite systems, emitting a single consolidated,
claim-boundary-audited report with all certificates.

| Member | Currencies | Certified statement |
|---|---|---|
| Quantum speed limit | time ↔ energy | build-up time ≥ Mandelstam–Tamm/Margolus–Levitin floor |
| Temporal double slit | time ↔ frequency | fringe spacing `= 2π/Δt`, `σ_t σ_ω ≥ 1/2` |
| Ergotropy / passivity | work ↔ entropy | `0 ≤ W ≤ ⟨H⟩−E₀` (no free energy) |
| Decoherence / branching | information | `1 ≤ N_eff ≤ d` |
| **Landauer's principle** | **info ↔ energy** | erasing a bit costs `≥ k_B T ln 2` |
| **Bekenstein bound** | **info ↔ energy ↔ geometry** | `S ≤ 2πRE` |
| Alcubierre energy condition | energy ↔ geometry | warp bubble needs negative energy (`ρ ≤ 0`) |
| **Compton–Schwarzschild** | **mass ↔ geometry** | object size floored at the Planck scale: `R² ≥ R_s·λ_C = 2 ℓ_P²` |

## The two new keystones

**Landauer's principle** (`gaugegap.quantum.landauer`) is the bridge from the
*information* modules to the *thermodynamics* module: decoherence raises a system's
entropy, and erasing it — resetting to a pure state in a bath at temperature `T` —
dissipates at least `k_B T · ΔS` (one bit = `k_B T ln 2`). Ergotropy is the work you
*can* extract; Landauer is the work you *must* pay to erase. Certificate:
`k_B T ΔS ≥ k_B T ln 2` when at least one bit is erased.

**The Bekenstein bound** (`gaugegap.relativity.bekenstein`) is the bridge from the
*quantum-information* side to the *relativity* side: the entropy in a region is capped
by `S ≤ 2πRE` — **geometry limits information**. Certificate: `S ≤ 2πRE` whenever the
region is at least the minimal radius `R ≥ S/(2πE)`.

**The mass–radius keystone** (`gaugegap.relativity.compton_schwarzschild`) is the
*global map* the other geometry members live inside. Plot every object by its mass and
radius and the lower-left of the plane is sealed off by two limits in the same
currencies the web already trades in:

- **Forbidden by gravity** — the Schwarzschild radius `R_s = 2GM/c²` (pack tighter and
  you are inside your own horizon). Same energy↔geometry currency as Bekenstein /
  Alcubierre.
- **Forbidden by quantum uncertainty** — the reduced Compton wavelength
  `λ_C = ℏ/(Mc)` (localize tighter and the vacuum pair-produces). Same mass↔quantum
  scale as the speed-limit members.

The two boundaries cross at the **Planck point**, and the product is *mass-independent*:
`R_s·λ_C = 2Gℏ/c³ = 2 ℓ_P²`. So any allowed object (`R ≥ R_s` and `R ≥ λ_C`) obeys
`R² ≥ R_s·λ_C = 2 ℓ_P²`, i.e. `R ≥ √2 ℓ_P` — **the Planck length is a floor on object
size**, reached exactly at the crossing. Certificate: `R·R ≥ R_s·λ_C` from the two
trust inputs `R ≥ R_s` and `R ≥ λ_C`. *Claim boundary:* the standard
order-of-magnitude Compton–Schwarzschild / minimal-length bound; NOT a quantum-gravity
derivation, NOT a claim that spacetime is discrete or that the Planck length is
operationally reachable.

```bash
make physical-limits
python scripts/run_physical_limits.py --d 3 --temperature 1 --radius 2
```

## Claim boundary

Finite-system / semiclassical demonstrations of **established** bounds, each
bracketed or machine-checked (Lean 4 / Coq). Not continuum/Yang–Mills/Millennium
claims; not a buildable warp drive or free-energy device; the Bekenstein bound is
applied as an info–energy–geometry consistency relation, not a derivation of
holography. Dependency-light (numpy).

References: Mandelstam & Tamm (1945); Margolus & Levitin (1998); Allahverdyan–Balian–
Nieuwenhuizen (2004); Zurek (2003); Landauer (1961); Bekenstein (1981); Alcubierre
(1994); Schwarzschild (1916); Compton (1923); Carr, Mureika & Nicolini (2015).
