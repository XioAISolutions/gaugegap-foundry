.PHONY: install-dev smoke audit audit-strict proofpack proofpack-verify reviewer-packet

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

reviewer-packet: proofpack
	mkdir -p results/reviewer-packet
	cp README.md results/reviewer-packet/README.md
	cp docs/solution-gap-audit.md results/reviewer-packet/solution-gap-audit.md
	cp docs/agent-work-orders.md results/reviewer-packet/agent-work-orders.md
	cp results/claim-boundary-audit/claim_boundary_audit.md results/reviewer-packet/claim-boundary-audit.md || true
	cp results/research-maturity-audit/research_maturity_audit.md results/reviewer-packet/research-maturity-audit.md || true
