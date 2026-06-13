# The operator / spectral / quantum landscape around the Riemann Hypothesis

A cited reference for this project: what the operator-based and quantum routes to
the Riemann Hypothesis (RH) actually establish, where they stop, and what this
repository's certified-screening + QPE + formal-certification work can honestly
contribute.

> **Claim boundary (binding).** This document is a critical survey. Everything
> here is consistent with the central fact that **RH is unproven** and that this
> repository produces a **finite-truncation negative result**, never a proof of
> RH. Each mention of a "proof of RH" below refers to attempts that are **not**
> accepted proofs.

**Sourcing caveat.** Direct page fetches were blocked (HTTP 403) when this was
compiled, so claims were assembled from search summaries of the primary sources
listed. They are cross-consistent and match the established literature, but exact
constants should be checked against the PDFs before any external publication.
Labels: **[THEOREM]** established · **[CONJECTURE]** believed, unproven ·
**[HEURISTIC]** semiclassical/asserted · **[CRITICISM]** · **[RULE]** prize rule.

## Bottom line

There is **no** credible near-term path from operator-based or quantum methods to
a proof of RH, and therefore none to the Clay Millennium Prize. Every operator
program either (a) reproduces only the *average* zero-counting function rather
than the actual zeros, (b) reformulates RH into an equivalent **unproven**
statement, or (c) asserts a self-adjointness that is not established. Computation
— classical or quantum — yields finite evidence, never a proof of an infinite
statement. The honest, defensible niche for this repository is **ruling out
specific candidate operators with certified negative (separation) results.**

## 1. Hilbert–Pólya & Berry–Keating xp

- **[THEOREM]** A self-adjoint operator has real spectrum, so if the zero-heights
  `tₙ` were its eigenvalues, all zeros would lie on Re(s)=½. That is the rigorous
  *half*; the existence of the operator is the open part.
  ([Hilbert–Pólya](https://en.wikipedia.org/wiki/Hilbert%E2%80%93P%C3%B3lya_conjecture))
- **[CONJECTURE]** No such operator has ever been constructed; Hilbert–Pólya is open.
- **[HEURISTIC]** Berry–Keating (1999): the quantized `H = xp` with a phase-space
  cutoff semiclassically reproduces the *smooth* counting term
  `N(E) ≈ (E/2π)(log(E/2π) − 1) + 7/8`. It reproduces only the **average** density
  — not the fluctuations, i.e. not the actual zero locations.
  ([Berry–Keating](https://empslocal.ex.ac.uk/people/staff/mrwatkin/zeta/berry-keating1.pdf),
  [Sierra review](https://arxiv.org/pdf/1601.01797))
- **[THEOREM — no-go]** Endres–Steiner: the Berry–Keating operator on `L²(ℝ₊)` has
  **purely continuous spectrum**, so this quantization cannot be the Hilbert–Pólya
  operator. They rigorously classify self-adjoint extensions on compact **quantum
  graphs** — which *mimic*, not *equal*, the zeros. ([arXiv:0912.3183](https://arxiv.org/abs/0912.3183))

## 2. Connes' noncommutative-geometry / trace-formula route

- **[THEOREM]** Connes (1999) **reduces** RH to the validity of a trace formula on
  the adele class space, equivalently to **Weil positivity** — a reformulation,
  **not a proof**. The zeros appear as an *absorption* (missing-line) spectrum,
  not a discrete eigenvalue spectrum.
  ([Selecta 1999](https://link.springer.com/article/10.1007/s000290050042),
  [essay](https://arxiv.org/abs/1509.05576))
- **[THEOREM]** Connes–Consani (2021) prove Weil positivity only at the single
  archimedean place (simplest case). ([arXiv:2006.13771](https://arxiv.org/abs/2006.13771))
- **[CONJECTURE]** The general semilocal case — the one that would give RH — is
  explicitly left open.
- **[HEURISTIC — current frontier]** Connes–Consani–Moscovici, *Zeta Spectral
  Triples* (Nov 2025): self-adjoint perturbations using only primes `p ≤ x` whose
  spectra match the lowest zeros to extreme numerical accuracy; framed by the
  authors as **"a strategy toward a proof,"** not a proof.
  ([arXiv:2511.22755](https://arxiv.org/abs/2511.22755),
  [PNAS 2022 precursor](https://www.pnas.org/doi/10.1073/pnas.2123174119))

## 3. Recent "spectral realization" claims & failure modes

- **[CRITICISM]** Bender–Brody–Müller (PRL 2017) is a strategy, not a proof.
  Bellissard's published Comment shows the half-line momentum operator has **no
  self-adjoint extension** and the eigenfunctions are **not square-integrable**;
  the reply only argued the gaps were "non-fatal."
  ([BBM 1608.03679](https://arxiv.org/abs/1608.03679),
  [Bellissard 1704.02644](https://arxiv.org/abs/1704.02644))
- **[UNVERIFIED-CLAIM]** **Majorana–Rindler (arXiv:2503.09644, 2025)** — the line
  most related to this repo's `dirac_rindler` family — claims an "exact spectral
  realization" with a self-adjointness proof. Red flags: filed in **math.GM**
  (arXiv's catch-all, *not* Number Theory), **no peer review**, no independent
  verification. Treat as unverified. ([2503.09644](https://arxiv.org/abs/2503.09644))
- **[CRITICISM]** The recurring four failure modes of operator-based RH attempts:
  **(1)** circularity (the boundary condition that yields the zeros assumes them);
  **(2)** counting-function ≠ spectrum (matching `N(E)` is not exhibiting
  eigenvalues); **(3)** self-adjointness asserted, not established; **(4)** finite
  numerical agreement passed off as a proof. Even Atiyah's 2018 claim failed
  review. ([Science](https://www.science.org/content/article/skepticism-surrounds-renowned-mathematician-s-attempted-proof-160-year-old-hypothesis))

## 4. Quantum computing / QPE for the zeros

- **[FACT]** RH is verified (certified interval arithmetic, Turing's method) for
  all zeros up to height ≈ 3×10¹² — the first ~1.2×10¹³ zeros (Platt–Trudgian);
  classical computation reaches >10¹³. ([arXiv:2004.09765](https://arxiv.org/abs/2004.09765))
- **[FACT]** A 2021 USTC trapped-ion experiment located only ~80 zeros — quantum
  hardware is many orders of magnitude *behind* classical here.
  ([Nature QI](https://www.nature.com/articles/s41534-021-00446-7))
- **[INFEASIBLE-NOW]** High-precision QPE needs `O(2⁻ⁿ)` resolution, `O(n²)` depth,
  and fault tolerance — beyond 2024–2026 NISQ hardware (matching this repo's own
  hardware-feasibility finding). ([2410.05369](https://arxiv.org/pdf/2410.05369))
- **[FACT]** No finite computation can prove RH (it concerns infinitely many
  zeros). A frequent overstatement conflates the **finite-field** RH
  (Weil/Deligne — already a theorem) with the classical RH; they are different
  objects. ([Farmer 2211.11671](https://arxiv.org/abs/2211.11671))

## 5. Certified numerics, formal proof, and the Clay bar

- **[RULE]** The Clay Millennium Prize requires a full solution **published in a
  refereed journal of worldwide repute**, then a **~2-year waiting period** *and*
  general community acceptance before the board even considers it.
  ([Clay rules](https://www.claymath.org/wp-content/uploads/2022/03/millennium_prize_rules_0.pdf))
- **[FACT]** Arb gives certified ball-arithmetic ζ evaluation; Rump/INTLAB and
  Gershgorin give verified eigenvalue enclosures of *finite* matrices — certifying
  finite computations, not asymptotic claims. ([Arb](https://arxiv.org/pdf/1611.02831))
- **[FACT]** Lean's mathlib contains a formal *statement* of RH and a formalized
  ζ/L-function theory, but **no proof**; the prime number theorem has been fully
  formalized. `sorry`/`Admitted` are proof holes.
  ([Lean ζ/L-functions](https://arxiv.org/abs/2503.00959),
  [PNT+](https://github.com/AlexKontorovich/PrimeNumberTheoremAnd))
- **[ASSESSMENT]** A finite-truncation spectrum provably *far* from the zeros is a
  legitimate **negative/separation result**: it can rigorously rule out a specific
  candidate operator (publishable) but cannot settle RH. Bellissard's comment is a
  published example of exactly this genre.

## 6. Testing the Dirac–Rindler claim with this repo's certified pipeline

This repository's three candidate families map directly onto the literature:

| Family (`curverank_certified`) | Literature line | Status of that line |
|---|---|---|
| `xp` | Berry–Keating | Half-line version **shown** to have continuous spectrum (no-go); reproduces only the average term |
| `dirac_rindler` | Sierra Dirac models / **Majorana–Rindler 2503.09644** | 2025 "exact realization" claim is **unverified** (math.GM, no peer review) |
| `quantum_graph` | Endres–Steiner quantum graphs | **Rigorous**, but graphs *mimic*, not *equal*, the zeros |

Running `certified_family_mismatch("dirac_rindler", n, 20)` — the certified L2
mismatch `M_n` between this Dirac–Rindler truncation's spectrum and the first 20
Arb-certified zeros:

| n | certified `M_n` (interval) |
|---:|---|
| 10 | [24.568349, 24.568349] |
| 15 | [21.183848, 21.183848] |
| 20 | [26.191066, 26.191066] |
| 25 | [21.400872, 21.400872] |
| 30 | [26.124139, 26.124139] |

The finite truncation is **certifiably far** from the zeros (`M_n ≳ 21`,
fluctuating rather than monotone — unlike `xp`, whose certified bound increases
with `n`). The discharged formal proof (`curverank_formal_emit`) closes
`M ≥ separationThreshold` for this family in Lean/Coq with the interval
certificate as the single axiom.

**What this does and does NOT show — read carefully.**

- It **does**: rigorously establish that *this repository's* Dirac–Rindler
  truncation is bounded away from the zeros at the tested sizes.
- It **does NOT**: refute arXiv:2503.09644. That paper's Hamiltonian (a
  Mellin–Barnes construction with delta potentials on square-free integers) is a
  *different, more elaborate* operator than this repo's `dirac_rindler_interval`,
  and its central claim is an *asymptotic/exact* spectral identity, not a
  finite-truncation statement. A faithful test would require reimplementing that
  exact operator (the paper was not fetchable here) and is still subject to the
  fundamental limit that no finite computation settles an asymptotic claim.

The honest contribution available here is the **negative-result genre** of
Bellissard's comment: a candidate finite-truncation operator can be certifiably
separated from the zeros, which rules out *that* operator as a Hilbert–Pólya
candidate at finite size — a real, publishable result short of proving RH.

## Sources

Primary sources cited inline above; the most load-bearing:
- Clay rules / Bombieri statement — claymath.org
- Endres–Steiner, quantum graphs — arXiv:0912.3183
- Connes 1999 (Selecta), Connes–Consani 2006.13771, Connes–Consani–Moscovici 2511.22755
- Bender–Brody–Müller 1608.03679; Bellissard 1704.02644
- Majorana–Rindler 2503.09644 (math.GM, unverified)
- Platt–Trudgian 2004.09765; Farmer 2211.11671
- Arb 1611.02831; Lean ζ/L-functions 2503.00959; PNT+ (Kontorovich/Tao)
