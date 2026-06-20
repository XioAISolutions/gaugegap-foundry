.PHONY: install-dev smoke audit audit-strict proofpack proofpack-verify reviewer-packet \
	curverank curverank-formal curverank-ibm curverank-hardware curverank-signal \
	curverank-noise-study cudaq-benchmark unified quantum-validate error-budget \
	certify-scaling geometry-figures certified-bracket certified-shadows qsvt temple-bracket open-system certified-quantum

# Pin the proofpack clock to the HEAD commit date so the same commit produces a
# byte-for-byte identical proofpack from a fresh clone (reproducible builds).
SOURCE_DATE_EPOCH := $(shell git -C . log -1 --format=%ct 2>/dev/null || echo 1700000000)
export SOURCE_DATE_EPOCH

install-dev:
	python -m pip install --upgrade pip
	python -m pip install -e '.[dev]'

smoke:
	python -m pytest
	python scripts/run_gap_sweep.py --sizes 4,6 --field-points 3 --output-dir /tmp/gaugegap-smoke
	python scripts/run_curverank_screen.py --family xp --n-basis 10,20 --k-zeros 10 --output-dir /tmp/curverank-smoke
	python scripts/run_gaugegap_su3_pure.py --lattice-sizes 2x2 --g-coupling-points 2 --output-dir /tmp/su3-prototype-smoke
	python scripts/run_su3_link.py --cutoff 2 --output-dir /tmp/su3-link-smoke

# claim-boundary is the hard gate (matches CI); the maturity audit runs in
# report mode because driving its high_unbounded count to zero is the open
# work tracked in issue #12 (A2/A3/A6). Use audit-strict to gate on it too.
audit:
	python scripts/claim_boundary_audit.py --strict
	python scripts/research_maturity_audit.py

audit-strict: audit
	python scripts/research_maturity_audit.py --strict

proofpack: audit smoke
	python scripts/generate_reproducibility_proofpack.py \
		--output-dir results/proofpack \
		--include-search \
		--include-validation

# Assert the proofpack is deterministic: two fresh builds under the same
# SOURCE_DATE_EPOCH must produce an identical reproducible_digest (issue #12 A4).
proofpack-verify:
	python scripts/verify_proofpack.py

# Self-contained packet for outside experts (issue #12 A7): runs the audits,
# curates the review docs, and writes an INDEX.md with provenance, audit status,
# reproduction commands, and a reviewer checklist.
reviewer-packet:
	python scripts/build_reviewer_packet.py --output-dir results/reviewer-packet

# --- CurveRank (Hilbert-Polya / Riemann spectral screening) reproduction -------
# One-command regeneration of the CurveRank result bundles. Honest scope: these
# produce a certified finite-truncation NEGATIVE result plus a quantum benchmark;
# they are not a proof of the Riemann Hypothesis (see docs/curverank-formal-proof.md
# and docs/riemann-operator-landscape.md).

# Machine-checkable formal proof of the finite-truncation separation theorem:
# verified interval certificate exported to Lean 4 / Coq / Isabelle, plus the
# discharged (no-`sorry`) Lean/Coq proofs for all three operator families.
curverank-formal:
	python scripts/run_curverank_formal_proof.py \
		--n-panel 10,15,20,25,30 --k-zeros 20 \
		--output-dir results/curverank-formal

# Windowed QPE eigenvalue recovery on the local IBM/Aer emulator (no credentials,
# no cost). The real-hardware path stays staged behind a credential check; see
# docs/curverank-ibm-runbook.md.
curverank-ibm:
	python scripts/run_curverank_ibm.py --emulator \
		--n-basis 4,8,16 --n-precision 6 --shots 4096 --yes \
		--output-dir results/curverank-ibm

# Hardware-feasibility report: dense vs Trotter vs iterative circuit cost
# (width/depth/CX), evidence rather than assertion.
curverank-hardware:
	python scripts/run_curverank_hardware_report.py \
		--output-dir results/curverank-hardware

# Quantum signal extraction: recover eigenvalues from the correlation signal
# g(t)=<psi|exp(-iHt)|psi> (Hadamard test -> Prony/ESPRIT) and validate them
# against the certified enclosures. Exact statevector mode, no credentials.
curverank-signal:
	python scripts/run_curverank_signal.py --n-basis 8 --method esprit \
		--output-dir results/curverank-signal

# Noise study: QCELS (dominant eigenvalue) vs ESPRIT (full spectrum) accuracy
# under modelled dephasing + shot noise. Exact statevector envelopes, no creds.
curverank-noise-study:
	python scripts/run_curverank_noise_study.py --output-dir results/curverank-noise

# Benchmark the simulation backends (numpy vs CUDA-Q) across qubit counts.
# CUDA-Q rows populate only where CUDA-Q + a GPU are present; numpy always runs.
cudaq-benchmark:
	python scripts/run_cudaq_benchmark.py --max-qubits 12 --output-dir results/cudaq-benchmark

# Regenerate all CurveRank bundles.
curverank: curverank-formal curverank-ibm curverank-hardware curverank-signal \
	curverank-noise-study

# Unified pipeline: one truncation threaded through every depth of the repo
# (classical -> certified -> QPE -> signal -> advanced quantum -> cross-validated
# -> formal Lean/Coq -> Spectra DSL -> claim-boundary-audited report). Honest
# scope: certified NEGATIVE result + method benchmark; not a proof of RH.
unified:
	python scripts/run_unified_pipeline.py --n-basis 8 --k-zeros 20 --deep \
		--output-dir results/unified-pipeline

# Quantum-validation harness: check each quantum method's eigenvalue estimates
# against the certified interval kernel (ESPRIT/QCELS/Krylov are pure-numpy; QPE
# uses the local Aer emulator). Honest scope: certified screening + benchmark.
quantum-validate:
	python scripts/run_quantum_validation.py --operator berry_keating_xp \
		--n-basis 8 --methods esprit,qcels,krylov \
		--output-dir results/quantum-validation

# Hardened error budget (A6): repeated-seed runs + confidence intervals +
# source-separated components (statistical / truncation / numerical). Honest
# scope: the CI is a fixed-truncation statistical interval, no continuum claim.
error-budget:
	python scripts/run_error_budget.py --n-basis 8 --n-runs 20 \
		--output-dir results/error-budget

# Scaling benchmark of the rigorous certified-eigenvalue kernel (~O(n^3) exact
# arithmetic): wall-time + max enclosure width vs truncation size.
certify-scaling:
	python scripts/run_certify_scaling.py --sizes 4,8,16,32 \
		--output-dir results/certify-scaling

# Certified energy/gap bracket: rigorous interval LOWER bound + quantum variational
# (Ritz) UPPER bound + discharged Lean/Coq certificate. Two-sided, machine-checked.
certified-bracket:
	python scripts/run_certified_bracket.py --operator berry_keating_xp \
		--n-basis 8 --output-dir results/certified-bracket

# Certified classical shadows: median-of-means observable estimates with confidence
# bands, cross-validated vs exact. Statistical band at a fixed shot budget.
certified-shadows:
	python scripts/run_certified_shadows.py --operator berry_keating_xp \
		--n-basis 8 --output-dir results/certified-shadows

# QSVT eigenvalue transform: apply a polynomial P to the spectrum and certify the
# transformed eigenvalues against P evaluated (interval arithmetic) over the
# certified enclosures.
qsvt:
	python scripts/run_qsvt.py --operator berry_keating_xp --coeffs 0,0,1 \
		--output-dir results/qsvt

# Temple-Kato certified ground-energy bracket from a quantum trial state (rigorous
# lower + variational upper + Lean/Coq), dependency-light.
temple-bracket:
	python scripts/run_temple_bracket.py --operator berry_keating_xp --n-basis 8 \
		--output-dir results/temple-bracket

# Finite Lindbladian open-system steady state (numpy), cross-validated.
open-system:
	python scripts/run_open_system.py --n-sites 2 --output-dir results/open-system

# Capstone: run every certified-quantum primitive on one operator and emit a single
# consolidated, claim-boundary-audited report (all checks pass).
certified-quantum:
	python scripts/run_certified_quantum_report.py --operator berry_keating_xp \
		--n-basis 8 --output-dir results/certified-quantum

# Geometry-of-GaugeGap figures: exact 2D projections of higher-dim structures
# (su(3) weight diagrams + root system, Calabi-Yau cross-section). Deterministic
# SVG. Add SACRED=1 for the decorative golden-ratio/Vesica overlay.
geometry-figures:
	python scripts/generate_geometry_figures.py $(if $(SACRED),--sacred-overlay,) \
		--output-dir figures/geometry
	python scripts/generate_geometry_html.py \
		--output figures/geometry/geometry_explorer.html
	python scripts/generate_geometry_extra.py --output-dir figures/geometry
