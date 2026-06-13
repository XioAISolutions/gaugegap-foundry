.PHONY: install-dev smoke audit audit-strict proofpack proofpack-verify reviewer-packet \
	curverank curverank-formal curverank-ibm curverank-hardware

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

# Regenerate all CurveRank bundles.
curverank: curverank-formal curverank-ibm curverank-hardware
