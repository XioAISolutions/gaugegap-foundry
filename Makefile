.PHONY: install-dev smoke audit audit-strict proofpack proofpack-verify reviewer-packet \
	curverank curverank-formal curverank-ibm curverank-hardware curverank-signal \
	curverank-noise-study cudaq-benchmark unified quantum-validate error-budget \
	certify-scaling geometry-figures certified-bracket certified-shadows qsvt \
	temple-bracket open-system certified-quantum entanglement-dynamics \
	entanglement-speed-limit alcubierre-warp decoherence-branching ergotropy \
	landauer bekenstein physical-limits temporal-double-slit physical-limits-figures \
	verify-certificates compile-coq sonification cherenkov lieb-robinson

# Pin proof artifacts to the HEAD commit time so a fixed commit remains
# byte-reproducible. The orchestration parameters live only in config/foundry.yaml.
SOURCE_DATE_EPOCH := $(shell git -C . log -1 --format=%ct 2>/dev/null || echo 1700000000)
export SOURCE_DATE_EPOCH

FOUNDRY ?= foundry

install-dev:
	python -m pip install --upgrade pip
	python -m pip install -e '.[dev]'

smoke:
	$(FOUNDRY) run smoke

audit:
	$(FOUNDRY) audit

audit-strict: audit

proofpack:
	$(FOUNDRY) proofpack

proofpack-verify:
	$(FOUNDRY) run proofpack-verify

reviewer-packet:
	$(FOUNDRY) run reviewer-packet

curverank:
	$(FOUNDRY) run curverank

curverank-formal:
	$(FOUNDRY) run curverank-formal

curverank-ibm:
	$(FOUNDRY) run curverank-ibm

curverank-hardware:
	$(FOUNDRY) run curverank-hardware

curverank-signal:
	$(FOUNDRY) run curverank-signal

curverank-noise-study:
	$(FOUNDRY) run curverank-noise-study

cudaq-benchmark:
	$(FOUNDRY) run cudaq-benchmark

unified:
	$(FOUNDRY) run curverank-0001

quantum-validate:
	$(FOUNDRY) run quantum-validate

error-budget:
	$(FOUNDRY) run error-budget

certify-scaling:
	$(FOUNDRY) run certify-scaling

certified-bracket:
	$(FOUNDRY) run certified-bracket

certified-shadows:
	$(FOUNDRY) run certified-shadows

qsvt:
	$(FOUNDRY) run qsvt

temple-bracket:
	$(FOUNDRY) run temple-bracket

open-system:
	$(FOUNDRY) run open-system

certified-quantum:
	$(FOUNDRY) run certified-quantum

entanglement-dynamics:
	$(FOUNDRY) run entanglement-dynamics

entanglement-speed-limit:
	$(FOUNDRY) run entanglement-speed-limit

alcubierre-warp:
	$(FOUNDRY) run alcubierre-warp

decoherence-branching:
	$(FOUNDRY) run decoherence-branching

ergotropy:
	$(FOUNDRY) run ergotropy

landauer bekenstein physical-limits:
	$(FOUNDRY) run physical-limits

temporal-double-slit:
	$(FOUNDRY) run temporal-double-slit

physical-limits-figures:
	$(FOUNDRY) run physical-limits-figures

verify-certificates:
	$(FOUNDRY) run verify-certificates

compile-coq:
	$(FOUNDRY) run compile-coq

sonification:
	$(FOUNDRY) run sonification

cherenkov:
	$(FOUNDRY) run cherenkov

lieb-robinson:
	$(FOUNDRY) run lieb-robinson

geometry-figures:
	$(FOUNDRY) run geometry-figures
