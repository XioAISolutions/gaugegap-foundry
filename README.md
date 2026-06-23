# 🔬 GaugeGap Foundry

> **Verification-first AI-for-science infrastructure for Millennium Prize-adjacent finite-system benchmarks.**

<p align="center">
  <img src="figures/physical-limits/web.svg" alt="The web of physical limits — twelve certified phenomena" width="720"/>
  <br/>
  <em>Twelve fundamental bounds, each reduced to a single machine-checked inequality, shown to be one structure — trade-offs among <strong>energy · time · information · geometry · mass · measurement</strong>. <a href="#-the-web-of-physical-limits--gallery">Jump to the gallery ↓</a></em>
</p>

![Python](https://img.shields.io/badge/python-3.10%2B-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-Apache--2.0-green)
![Tests](https://img.shields.io/badge/tests-754%20passing-brightgreen?logo=pytest&logoColor=white)
![Claim-boundary audit](https://img.shields.io/badge/claim--boundary%20audit-0%20high-success)
![Maturity audit](https://img.shields.io/badge/maturity%20audit-0%20high--unbounded-success)
![Reproducible](https://img.shields.io/badge/builds-byte--reproducible-blueviolet)
![Quantum](https://img.shields.io/badge/quantum-Qiskit%202.4%20%7C%20IBM%20Runtime-6929c4?logo=qiskit&logoColor=white)

---

## 🎯 Current Status

> ⚠️ This repository is **not** claiming a solution to any Millennium Prize problem. It builds reproducible finite-system benchmarks, retains negative results, and creates verification infrastructure for theorem-adjacent progress.

The current CurveRank work includes a **computer-assisted spectral screening result** for Berry-Keating-style operator candidates. Treat this as a local, reproducible negative-result artifact that still needs independent expert review before any publication claim.

- 📄 Example certificate: `results/sprint-now/proof_certificate.json`
- 📊 Example summary: `results/sprint-now/PROOF_SUMMARY.md`

### 🛡️ Hardening status

The repo tracks a practical solution-gap scorecard and agent work orders:

| Artifact | Purpose |
|---|---|
| 📋 `docs/solution-gap-audit.md` | honest gap between current finite benchmarks and a true solution path |
| 🤖 `docs/agent-work-orders.md` | execution-ready tasks for Codex/agent runs |
| 🔎 `scripts/research_maturity_audit.py` | scans for unbounded placeholder/prototype risk |
| 🛠️ `Makefile` | one-command smoke, audit, proofpack, and reviewer-packet targets |

---

## 🗺️ The Foundry at a glance

```mermaid
flowchart TD
    F["🔬 GaugeGap Foundry"]
    F --> G["⚛️ GaugeGap<br/>finite gauge systems"]
    F --> FL["🌊 FlowGap<br/>Navier-Stokes-adjacent PDEs"]
    F --> C["📈 CurveRank<br/>Riemann-adjacent spectral screening"]
    F --> D["🧩 DSLs<br/>Spectra · Verdict"]

    G --> G1["Z₂ → U(1) → SU(2) → SU(3 scaffold)"]
    FL --> FL1["viscous Burgers surrogate"]
    C --> C1["certified negative result<br/>+ machine-checkable proof"]
    D --> D1["certification / evidence<br/>as a first-class semantic"]

    classDef boundary fill:#f6f0ff,stroke:#6929c4,color:#1a1a1a;
    class F,G,FL,C,D boundary;
```

> 🧭 **Boundary:** every track is **finite-system only**. No continuum Yang-Mills mass-gap claim, and no proof of the Riemann Hypothesis.

---

## 🌐 The web of physical limits — gallery

A set of finite-system modules, each built by stripping a viral "physics" reel down to
the one genuine, exactly computable statement it contains, and certifying it with a
discharged Lean 4 / Coq inequality (independently re-checked by z3). They turn out to be
**one structure**: trade-offs among four currencies — **energy, time, information, geometry**.

<p align="center">
  <img src="figures/physical-limits/web.svg" alt="The web of physical limits" width="640"/>
</p>

| Member | Currencies | Certified inequality |
|---|---|---|
| Quantum speed limit | time ↔ energy | `t ≥ τ_QSL` |
| Temporal double slit | time ↔ frequency | `Δω = 2π/Δt`, `σ_t σ_ω ≥ ½` |
| Sonification / sampling | time ↔ frequency | aliasing fold `0 < f_s − f < f_s/2` |
| Ergotropy / passivity | work ↔ entropy | `0 ≤ W ≤ ⟨H⟩ − E₀` (no free energy) |
| Decoherence / branching | information | `1 ≤ N_eff ≤ d` |
| Landauer's principle | info ↔ energy | `W ≥ k_B T ln 2` |
| Bekenstein bound | info ↔ energy ↔ geometry | `S ≤ 2π R E` |
| Alcubierre energy cond. | energy ↔ geometry | `ρ ≤ 0` (needs negative energy) |
| Cherenkov cone | velocity ↔ geometry | `cos θc = 1/(nβ)`, `β > 1/n` |
| Lieb–Robinson cone | information ↔ time | `x(t) ≤ v_LR·t + ξ` |
| Compton–Schwarzschild | mass ↔ geometry | `R² ≥ R_s·λ_C = 2 ℓ_P²` |
| Quantum Zeno effect | measurement ↔ time | survival `≥ 1 − (ΔE·T)²/N → 1` |

> 👁️ **"A watched quantum pot never boils."** The Zeno member is the rigorous *physical cousin* of the Hawthorne effect ("being observed changes behaviour"): frequent measurement provably freezes a quantum system's evolution. The sociological Hawthorne effect itself stays out (no exact core); only its certifiable physics counterpart earns a place — see [`gaugegap.quantum.quantum_zeno`](src/gaugegap/quantum/quantum_zeno.py).

These bounds also have a **global shape**. Plot every object — electron to
supermassive black hole — by mass and radius, and the lower-left is sealed off by two
of the web's own limits: the **Schwarzschild radius** (pack tighter → black hole) and
the **Compton wavelength** (localize tighter → the vacuum pair-produces). They cross at
the **Planck point**, where `R_s·λ_C = 2 ℓ_P²` — a machine-checked identity that holds
for *every* mass.

<p align="center">
  <img src="figures/physical-limits/mass_radius.svg" alt="The cosmic mass–radius diagram" width="640"/>
</p>

### 🪜 The certificate ladder

Every label above is a **discharged Lean 4 / Coq inequality** (single labelled trust input, no `Admitted`, no `sorry`) — re-checked independently by z3 and *compiled* by `coqc` in CI. Twelve of them, stacked:

<p align="center">
  <img src="figures/physical-limits/ladder.svg" alt="Certificate ladder — twelve machine-checked inequalities" width="720"/>
</p>

<details>
<summary>📜 <strong>What a machine-checked certificate actually looks like</strong> (the Compton–Schwarzschild Planck floor, emitted Coq)</summary>

```coq
Require Import Reals. Require Import Lra. Open Scope R_scope.
Section ComptonSchwarzschild_Planck.
Variable Rad Rs Lc : R.
Hypothesis Rs_pos : Rs > 0.            (* TRUST INPUT 1: positive Schwarzschild radius *)
Hypothesis Lc_pos : Lc > 0.            (* TRUST INPUT 2: positive Compton wavelength   *)
Hypothesis not_bh : Rad >= Rs.         (* TRUST INPUT 3: not inside its own horizon    *)
Hypothesis localizable : Rad >= Lc.    (* TRUST INPUT 4: not below its Compton length  *)
(* R^2 >= Rs * Lc  (= 2 l_P^2): the Planck-length floor on object size. *)
Theorem planck_floor : Rad * Rad >= Rs * Lc.
Proof. nra. Qed.
End ComptonSchwarzschild_Planck.
```
</details>

### 🖼️ The phenomena, one figure each

| | | |
|:---:|:---:|:---:|
| <img src="figures/physical-limits/entanglement-dynamics__entanglement_buildup.svg" width="240"/><br/>**Entanglement build-up** `S(t): 0→ln 2` | <img src="figures/physical-limits/entanglement-speed-limit__qsl_floor_vs_coupling.svg" width="240"/><br/>**Quantum speed-limit floor** ∝ 1/coupling | <img src="figures/physical-limits/temporal-double-slit__spectral_fringes.svg" width="240"/><br/>**Time diffraction** → spectral fringes |
| <img src="figures/physical-limits/decoherence-branching__decoherence_branching.svg" width="240"/><br/>**Decoherence** → `N_eff` branches | <img src="figures/physical-limits/ergotropy__extracted_work.svg" width="240"/><br/>**Ergotropy** saturates (no perpetual motion) | <img src="figures/physical-limits/alcubierre-warp__energy_density_profile.svg" width="240"/><br/>**Warp bubble** needs `ρ ≤ 0` |
| <img src="figures/physical-limits/cherenkov__cherenkov_cone.svg" width="240"/><br/>**Cherenkov cone** `cos θc = 1/(nβ)` | <img src="figures/physical-limits/lieb-robinson__light_cone.svg" width="240"/><br/>**Lieb–Robinson** linear light cone | <img src="figures/physical-limits/mass_radius.svg" width="240"/><br/>**Mass–radius** Planck-point floor |

📖 Full synthesis: [`docs/physical-limits-web.md`](docs/physical-limits-web.md) · 🧭 why we draw the line where we do: [`docs/epistemics-and-claim-boundaries.md`](docs/epistemics-and-claim-boundaries.md) · 🖼️ gallery + certificate ladder: [`figures/physical-limits/`](figures/physical-limits/) (open `index.html`) · ▶️ reproduce: `make physical-limits` · `make physical-limits-figures` · `make verify-certificates`

> 🧭 **Boundary:** finite-system / semiclassical demonstrations of *established* bounds, each bracketed or machine-checked — not continuum/Millennium claims, not a buildable warp drive or free-energy device.

---

## 🎲 The web of inference traps — decision theory, certified

The same move, applied to the *statistics* genre instead of physics: viral "mind-bender"
probability puzzles and classic inference traps, each reduced to an **exact, bounded,
certifiable core** (closed-form, not Monte-Carlo). These live in
[`gaugegap.decision`](src/gaugegap/decision/) and are deliberately **not** physical-limits members.

<p align="center">
  <img src="figures/inference-traps/web.svg" alt="The web of inference traps" width="720"/>
</p>

| Trap | Family | Exactly-computable core |
|---|---|---|
| St. Petersburg paradox | heavy tail | naive EV diverges (EVₙ = `n`); bounded-utility CE = `$4`; finite-bankroll EV = `N+1` |
| Power law | heavy tail | scale-free tail `P(X>cx)/P(X>x)=c^{−α}`; `E[Xᵐ]=∞ ⟺ m≥α` |
| Regression to the mean | conditioning | `E[Y\|X=x]=ρx`: selected extremes regress by `1−ρ` |
| Survivorship bias (Wald) | selection | survivor hit-rate `p(1−kill)`: "armor the holes" is exactly backwards |
| Berkson's paradox | collider | independent traits → corr `−1/2` once you condition on selection |
| Simpson's paradox | confounding | every subgroup favours A, the aggregate favours B |
| Bayes' theorem | the fix | base-rate fallacy: 99%-accurate test, 0.1% prevalence ⇒ `P(disease\|+) ≈ 1.9%` |

<details>
<summary>🎲 <strong>Worked example</strong> — run the traps yourself</summary>

```python
>>> from gaugegap.decision.bayes import analyze_bayes
>>> analyze_bayes().posterior_positive          # 99% test, 0.1% prevalence
0.0194...                                        # ~1.9% — not 99%! (base-rate fallacy)

>>> from gaugegap.decision.st_petersburg import analyze_st_petersburg
>>> r = analyze_st_petersburg()
>>> r.truncated_ev_sample[40], round(r.log_utility_certainty_equivalent, 6)
(40.0, 4.0)                                      # naive EV → ∞, but worth exactly $4

>>> from gaugegap.decision.berksons_paradox import selected_correlation
>>> selected_correlation(0.5, 0.5)               # two independent traits...
-0.5                                             # ...anti-correlate once you select
```
</details>

📖 Synthesis: [`docs/inference-traps.md`](docs/inference-traps.md) · 🧭 the discipline behind it: [`docs/epistemics-and-claim-boundaries.md`](docs/epistemics-and-claim-boundaries.md)

> 🧭 **Boundary:** exact decision-theory / statistics demonstrations; the divergences and resolutions are standard textbook results — not physical bounds, not financial/medical advice. *Excluded:* plain expected value (a building block); the **Hawthorne effect** keeps only its certifiable physics cousin — the [quantum Zeno effect](#-the-web-of-physical-limits--gallery) — while the sociological version stays out.

---

## ⚛️ GaugeGap Track — finite gauge-system benchmarks

**Natural progression:**

```mermaid
flowchart LR
    Z2["Z₂<br/>Ising / plaquette"] --> U1["U(1)<br/>compact gauge"]
    U1 --> SU2["SU(2)<br/>pure + matter"]
    SU2 --> SU3["SU(3)<br/>prototype scaffold"]
    SU3 --> R(["continuum<br/>research questions"])
    classDef done fill:#e7f7ec,stroke:#1a7f37,color:#0a0a0a;
    classDef proto fill:#fff4e5,stroke:#bc4c00,color:#0a0a0a;
    classDef open fill:#eef2ff,stroke:#4b5bd6,color:#0a0a0a;
    class Z2,U1,SU2 done;
    class SU3 proto;
    class R open;
```

| ID | Benchmark | Notes |
|---|---|---|
| `gaugegap-0001` | 🟢 Z₂ dual-chain / Ising sanity | finite transverse-field Ising chain; validates hypothesis registry + exact diagonalization |
| `gaugegap-0002` | 🟢 Z₂ plaquette chain | `H = -J Σ_p Π_{l∈p} Z_l - h Σ_l X_l`; Pauli/Qiskit-compatible export |
| `gaugegap-u1-0001` | 🟢 U(1) compact gauge | finite-lattice U(1) in 2+1D; truncated link Hilbert spaces |
| `gaugegap-0003` | 🟢 SU(2) pure gauge | first non-abelian finite benchmark in the series |
| `gaugegap-0004` | 🟢 SU(2) gauge-matter / hardware-readiness | string-breaking + meson spectrum; finite Z₂ hardware-readiness validator before any provider submission |
| `gaugegap-0005` | 🟧 SU(3) prototype scaffold | records `implementation_status=prototype_scaffold`; plaquette group multiplication, Gauss-law, Wilson loops, physical-subspace projection remain work-order items |
| `gaugegap-search-0001` | 🟢 Z₂ finite gap candidate search | ranks candidates by gap size, finite-size survival, perturbation stability, replica agreement, residuals |

> 🧭 **Boundary:** all GaugeGap items are finite-system benchmarks only; **no continuum Yang-Mills mass-gap claim.**

The SU(3) scaffold targets the standard `su(3)` weight structure (octet & decuplet), used here only as finite-system bookkeeping:

<p align="center">
  <img src="figures/octet_weight_diagram.svg" alt="SU(3) octet weight diagram" width="320"/>
  &nbsp;&nbsp;
  <img src="figures/decuplet_weight_diagram.svg" alt="SU(3) decuplet weight diagram" width="320"/>
</p>

---

## 🌊 FlowGap Track — Navier-Stokes-adjacent finite PDE systems

- **`flowgap-0001`**: viscous Burgers equation surrogate — a Navier-Stokes-adjacent proxy with pressure-Poisson subroutine benchmarks.

---

## 📈 CurveRank Track — Riemann-adjacent spectral screening

- **`curverank-0001`**: candidate operator screening against zeta-zero-inspired targets — a Berry-Keating-style **negative-result** artifact; the quantum phase-estimation path is exploratory.

```mermaid
flowchart LR
    OP["candidate operator<br/>xp · Dirac-Rindler · quantum-graph"] --> TR["finite truncation"]
    TR --> EIG["certified eigenvalue enclosures<br/>(interval arithmetic)"]
    Z["Arb-certified ζ zeros"] --> MM
    EIG --> MM["certified mismatch Mₙ"]
    MM --> SEP{"Mₙ ≥ threshold?"}
    SEP -->|yes| PROOF["discharged Lean / Coq certificate<br/>(separation theorem)"]
    SEP -->|no| FAIL["honest failure"]
    classDef neg fill:#fdeced,stroke:#c0392b,color:#0a0a0a;
    class PROOF,MM neg;
```

What this **does**: rigorously rules out a *specific finite-truncation operator* as a Hilbert–Pólya candidate (`Mₙ ≳ 27` for the `xp` panel, certified). What it does **not** do: it is **not a proof** of the Riemann Hypothesis, and makes no continuum claim. See:

- 📘 `docs/curverank-formal-proof.md` — the machine-checkable separation theorem (exported to Lean 4 / Coq / Isabelle, with discharged Lean `linarith` / Coq `lra` proofs for all three families).
- 📚 `docs/riemann-operator-landscape.md` — a cited survey of operator / quantum routes to RH and why none is a near-term proof.
- 🖥️ `docs/curverank-ibm-runbook.md` — windowed QPE on the IBM/Aer emulator (and how to stage a real-hardware run).

⚡ The certified screening kernel is **~14× faster** as of the latest revision (matrix→interval conversion reused across eigenpairs), with **bit-identical** results.

---

## 🧩 Honest-by-construction DSLs

Two tiny languages bake this repo's integrity rule into their semantics — a program that runs only states what it can back.

| DSL | First-class semantic | A claim is… | …backed by | Fails when |
|---|---|---|---|---|
| 🧮 **Spectra** (`docs/spectra-language.md`) | certification | `assert separated(M, …)` | a discharged Lean/Coq certificate | the interval kernel can't certify it |
| 🧪 **Verdict** (`docs/verdict-language.md`) | evidence | `assert score(E) >= t` | a logged, reproducible eval run | the eval doesn't meet the bar |

```bash
python scripts/run_spectra.py examples/curverank_screen.spectra   # certified spectral screening
python scripts/run_verdict.py examples/sentiment_eval.verdict      # eval-first model claims
```

> 🧭 **Boundary:** Spectra screens finite truncations (certified negative result, **not** a proof of RH); Verdict uses deterministic toy models to demonstrate eval-first semantics, **not** a production eval framework.

---

## ⚙️ Qiskit 2.4 / IBM Runtime findings applied

The hardware-readiness lane follows IBM's current Qiskit pattern:

```mermaid
flowchart LR
    A["map finite<br/>operator/circuit"] --> B["inspect /<br/>transpile resources"]
    B --> C["execute only after<br/>local checks pass"]
    C --> D["analyze deviations"]
```

The Qiskit 2.4 release strengthens Pauli-centric workflows, faster QPY serialization, transpilation infrastructure, and compiled-extension paths. For this repo that means:

- 🧱 keep Pauli terms as first-class artifacts;
- 📐 record resource estimates before any backend call;
- ✅ avoid hardware submission until exact and Pauli dense replicas agree;
- 🔐 serialize and hash validation outputs as proofpack material;
- 🔌 keep Qiskit/IBM Runtime optional — finite exact baselines must run without provider credentials.

The first implementation is `gaugegap-0004`, a local hardware-readiness validator for finite Z₂ candidates. It does not submit to hardware by default.

> ⚠️ Hardware results are noisy experimental artifacts and do not constitute mathematical proof.

---

## 🚀 Quick Start

### Reproduce the local spectral screening artifact

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[spectral]"

python scripts/run_curverank_screen.py \
    --family xp \
    --n-basis 10,15,20 \
    --k-zeros 20 \
    --output-dir results/verify

cat results/verify/curverank-0001-spectral-screen.csv
```

### Run core benchmarks

```bash
pip install -e '.[all]'

# ⚛️ GaugeGap
python scripts/run_gap_sweep.py
python scripts/run_z2_plaquette.py
python scripts/run_z2_plaquette_sweep.py
python scripts/run_gaugegap_u1.py
python scripts/run_gaugegap_su2_pure.py
python scripts/run_gaugegap_su3_pure.py
python scripts/search_gap_candidates.py --output-dir /tmp/gaugegap-search-0001 --max-candidates 10
python scripts/run_candidate_validation.py --output-dir /tmp/gaugegap-0004 --disable-qiskit-probe
python scripts/run_qiskit_candidate_validation.py --output-dir /tmp/gaugegap-qiskit-validation
python scripts/submit_ibm_runtime_candidate.py --dry-run --output-dir /tmp/gaugegap-runtime-dryrun

# 🌊 FlowGap
python scripts/run_flowgap_burgers.py

# 📈 CurveRank
python scripts/run_curverank_screen.py --family xp --n-basis 10,15,20,25,30

# ✅ Tests
python -m pytest
```

### One-command reviewer workflow

```bash
make audit            # claim-boundary (strict) + maturity audit
make smoke            # fast end-to-end checks
make proofpack        # hashed, reproducible proof bundle
make reviewer-packet  # self-contained packet for outside experts
```

### CurveRank reproduction (formal proof + IBM + hardware report)

```bash
make curverank-formal     # Lean/Coq/Isabelle certificates + discharged proofs
make curverank-ibm        # windowed QPE on the local IBM/Aer emulator (no creds)
make curverank-hardware   # dense vs Trotter vs iterative circuit-cost report
make curverank            # all three
```

### Claim-boundary audit and proofpack

```bash
python scripts/claim_boundary_audit.py --strict
python scripts/research_maturity_audit.py --strict
python scripts/generate_reproducibility_proofpack.py \
  --output-dir results/proofpack \
  --include-search \
  --include-validation
```

The proofpack writes a JSON manifest, a Markdown summary, command logs, output hashes, and the claim boundary used for the run. The maturity audit flags unbounded placeholder/prototype risk before public claims are made.

### Run SU(3) prototype scaffold

```bash
python scripts/run_gaugegap_su3_pure.py \
    --lattice-sizes 2x2 \
    --g-coupling-min 0.5 \
    --g-coupling-max 2.0 \
    --g-coupling-points 5 \
    --truncation 0.5 \
    --output-dir results/baselines

cat results/baselines/gaugegap-0005-su3-prototype-sweep.csv
```

Optional hardware submission commands require provider credentials and should be treated as exploratory finite-system runs, not proof artifacts. See also `docs/gaugegap-0004-hardware-readiness.md`, `docs/qiskit-2-4-validation.md`, `docs/ibm-runtime-submission.md`.

### 🐳 Docker deployment

```bash
docker-compose up
docker-compose --profile gaugegap up
docker-compose --profile flowgap up
docker-compose --profile curverank up
```

See `DEPLOYMENT.md` for the deployment guide.

---

## 🧭 Program Direction

The foundry is designed around a **verification ladder** — claims only climb after the rung below holds:

```mermaid
flowchart TD
    H["1 · register hypothesis<br/>with explicit kill criteria"] --> EX["2 · exact classical baseline"]
    EX --> CMP["3 · compare independent<br/>implementations"]
    CMP --> SIM["4 · noiseless + noisy simulators"]
    SIM --> HW["5 · hardware / analogue<br/>only after local checks pass"]
    HW --> PUB["6 · publish reproducible artifacts<br/>with finite-system scope stated"]
    classDef gate fill:#eef6ff,stroke:#0969da,color:#0a0a0a;
    class H,EX,CMP,SIM,HW,PUB gate;
```

**Backend order:**

```mermaid
flowchart LR
    A["local exact<br/>diagonalization"] --> B["local Pauli-operator<br/>validation"]
    B --> C["statevector +<br/>shot-based simulation"]
    C --> D["optional provider<br/>hardware submission"]
    D --> E["independent expert review<br/>before any strong claim"]
```

---

## 📂 Repository Layout

```text
docs/           roadmap and methods notes
hypotheses/     registered finite-system hypotheses
scripts/        reproducible experiment entrypoints
src/gaugegap/   package code (incl. spectra_lang, verdict_lang, rigorous/, relativity/)
examples/       Spectra (.spectra) and Verdict (.verdict) programs
figures/        weight diagrams, static figures, physical-limits web gallery
tests/          unit tests and smoke coverage (492)
results/        small checked-in baseline artifacts
```

---

## 🧱 Claim Boundary

✅ Use language like:

> finite-system benchmark · local screening artifact · candidate negative result requiring independent review · prototype scaffold

🚫 Avoid unbounded claim language such as:

> continuum Yang-Mills mass-gap proof · Millennium Prize resolution · theorem ready for a prize claim

That boundary is intentional. **The project earns credibility by making every small claim reproducible before expanding scope.** 🔁
