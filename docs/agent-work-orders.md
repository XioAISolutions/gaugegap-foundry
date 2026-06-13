# Agent Work Orders

These are execution-ready work orders for Codex/agent runs. Each task has a concrete definition of done and a claim-boundary rule.

---

## A0 — Do not overclaim

**Goal:** Keep every generated result inside a finite-system/reproducibility boundary.

**Definition of done:**
- `python scripts/claim_boundary_audit.py --strict` passes.
- No docs imply a continuum proof.
- Placeholder/prototype components are clearly labeled.

**Claim rule:** If the result is finite, say finite. If it is numerical, say numerical. If it is prototype, say prototype.

---

## A1 — Placeholder maturity audit

**Goal:** Add an automated audit that scans source/docs for placeholder phrases and emits a maturity report.

**Implementation target:**
- Add `scripts/research_maturity_audit.py`.
- Scan `src`, `scripts`, `docs`, `hypotheses`, `README.md`, and `results`.
- Detect phrases such as `placeholder`, `pass`, `future implementation`, `simplified`, `approximate`, `TODO`, `not implemented`.
- Classify severity:
  - high: source placeholder in scientific core path;
  - medium: docs/results overstate a prototype component;
  - low: explicit limitation or roadmap item.
- Write JSON and Markdown reports under `results/research-maturity-audit/`.
- Add CI step.

**Definition of done:**
- `python scripts/research_maturity_audit.py --strict` fails when high-severity placeholder code is found unless the component is explicitly marked prototype.
- `make proofpack` includes the maturity report.

---

## A2 — SU(3) truth hardening

**Goal:** Stop treating the current SU(3) lane as a completed SU(3) gauge-theory implementation.

**Implementation target:**
- Rename status language from `SU(3) implemented` to `SU(3) prototype scaffold` where appropriate.
- Add `implementation_status` metadata to SU(3) records.
- Add tests that verify placeholder observables return explicit `not_implemented` status, not silent `None`.
- Make `run_gaugegap_su3_pure.py` print a prototype warning and write it into JSONL/CSV.

**Definition of done:**
- Docs no longer imply production-grade SU(3).
- Result files distinguish prototype scaffold from verified model.
- CI covers the prototype boundary.

---

## A3 — Real SU(3) toy truncation path

**Goal:** Replace the diagonal plaquette placeholder with a defensible toy truncation or documented mathematical model.

**Implementation target:**
- Implement a minimal gauge-invariant SU(3)-inspired plaquette model or explicitly rename it `su3_inspired_toy`.
- Add Gauss-law constraint operator or document why the toy model does not enforce it.
- Add Wilson loop observable for the toy system.
- Add known-answer tests for the smallest lattice.

**Definition of done:**
- The code has a clearly documented Hamiltonian that matches the implementation.
- Tests validate Hermiticity, symmetry, dimensionality, and at least one known small-system result.

---

## A4 — One-command proofpack

**Goal:** Give reviewers one command to reproduce the repo's bounded claims.

**Implementation target:**
- Add `Makefile` with:
  - `make install-dev`
  - `make smoke`
  - `make proofpack`
  - `make audit`
- `make proofpack` should run:
  - unit tests;
  - claim-boundary audit;
  - research-maturity audit;
  - core small benchmarks;
  - proofpack generator.

**Definition of done:**
- A fresh clone can run `make proofpack` and produce a deterministic reviewer bundle.

---

## A5 — Known-answer regression tests

**Goal:** Replace confidence-by-output with confidence-by-known-reference.

**Implementation target:**
- Add analytic or brute-force reference tests for:
  - small Z2 dual chain;
  - Z2 plaquette one-plaquette model;
  - U(1) smallest truncation sanity checks;
  - CurveRank certified mismatch monotonic sanity checks.

**Definition of done:**
- Tests fail if core Hamiltonians change unexpectedly.
- Results include baseline hashes.

---

## A6 — Error budget hardening

**Goal:** Make uncertainty claims scientifically useful.

**Implementation target:**
- Split error sources into finite-size, truncation, discretization, sampling, optimizer, backend noise, and numerical precision.
- Add repeated-seed runs where stochastic methods appear.
- Write confidence intervals and explain what they do and do not imply.

**Definition of done:**
- Error report makes no continuum implication.
- Each uncertainty value maps to a reproducible computation.

---

## A7 — Reviewer packet

**Goal:** Make it easy for a lattice gauge theorist or mathematical physicist to review the work.

**Implementation target:**
- Add `scripts/generate_reviewer_packet.py`.
- Output:
  - project summary;
  - claim boundaries;
  - methods overview;
  - exact commands;
  - result hashes;
  - maturity audit;
  - known limitations;
  - reviewer questions.

**Definition of done:**
- `make reviewer-packet` creates a clean folder suitable to send to an outside expert.

---

## A8 — Paper skeleton

**Goal:** Create a preprint draft that sells the real achievement without poisoning credibility.

**Implementation target:**
- Add `paper/gaugegap_foundry_preprint.md`.
- Suggested title:
  - `GaugeGap Foundry: Reproducible Finite-System Benchmarks for Mass-Gap-Adjacent Gauge-Theory Experiments`
- Sections:
  - Abstract;
  - Claim boundary;
  - Benchmark ladder;
  - Methods;
  - Reproducibility;
  - Negative results;
  - Limitations;
  - Future work.

**Definition of done:**
- No prize claim.
- Every headline claim has a script/result citation.
