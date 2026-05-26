# GaugeGap Foundry Agent Instructions

## Claim boundary

Never describe this repository as solving, proving, or experimentally resolving
any Millennium Prize problem. Current work is finite-system benchmarking and
verification infrastructure across three tracks.

### GaugeGap (Yang-Mills mass gap)

Use precise language:

- finite-system mass-gap benchmark
- Z2 dual-chain sanity benchmark
- U(1) compact lattice gauge benchmark
- exact diagonalization baseline
- simulator or backend comparison
- hypothesis pruning

Avoid:

- proof of Yang-Mills
- AI discovered the mass gap
- quantum computer proves the theorem

### FlowGap (Navier-Stokes)

Use precise language:

- finite reduced-model benchmark
- viscous Burgers surrogate
- pressure-Poisson subroutine benchmark
- hybrid quantum-classical PDE comparison

Avoid:

- proof of Navier-Stokes regularity
- AI resolved the blow-up question
- quantum solver for turbulence

### CurveRank (Riemann hypothesis)

Use precise language:

- spectral screening of toy operators
- truncated Hilbert-Polya candidate
- spacing statistics comparison
- finite-truncation spectral mismatch

Avoid:

- proof of the Riemann Hypothesis
- AI found the Hilbert-Polya operator
- quantum computer verifies RH

## Development flow

- Keep provider credentials out of source.
- Keep exact classical baselines runnable without paid quantum access.
- Add hardware/provider integrations behind optional dependencies and clear
  failure messages.
- Record backend metadata in outputs before comparing providers.
- Retain negative results when they disprove a registered hypothesis.

## Verification

Before committing code changes, run:

```bash
python -m unittest discover -s tests
python scripts/run_gap_sweep.py --sizes 4,6 --field-points 3 --output-dir /tmp/gaugegap-smoke
```

For FlowGap changes:

```bash
python scripts/run_flowgap_burgers.py --sizes 16,32 --nu-points 3 --n-steps 20 --output-dir /tmp/flowgap-smoke
```

For CurveRank changes:

```bash
python scripts/run_curverank_screen.py --family xp --n-basis 10,20 --k-zeros 10 --output-dir /tmp/curverank-smoke
```

For U(1) gauge changes:

```bash
python scripts/run_gaugegap_u1.py --n-links 2 --truncation 1,2 --g-mag-points 3 --output-dir /tmp/u1-smoke
```

For Braket changes:

```bash
python scripts/run_hardware.py --provider braket-local --n-sites 4 --times 0,0.5 --shots 128 --output-dir /tmp/braket-smoke
```

For OriginQ changes:

```bash
python scripts/run_hardware.py --provider originq-local --n-sites 4 --times 0,0.5 --shots 128 --output-dir /tmp/originq-smoke
```

For cross-platform validation:

```bash
python scripts/validate_cross_platform.py --n-sites 4 --shots 512 --output-dir /tmp/xplatform
```

For Qiskit changes, also run:

```bash
python scripts/run_dynamics.py --backend statevector --n-sites 4 --times 0,0.5 --output-dir /tmp/gaugegap-statevector-smoke
python scripts/run_dynamics.py --backend aer-sampler --n-sites 4 --times 0,0.5 --shots 128 --output-dir /tmp/gaugegap-aer-smoke
python scripts/run_dynamics.py --backend aer-sampler --noise depolarizing --n-sites 4 --times 0,0.5 --shots 128 --output-dir /tmp/gaugegap-aer-depol-smoke
python scripts/analyze_dynamics.py --input-dir results/dynamics --output-dir /tmp/gaugegap-analysis-smoke
python scripts/quantum_status.py --output-dir /tmp/gaugegap-quantum-status
```

For hardware runs (requires provider credentials):

```bash
python scripts/run_hardware.py --provider ibm --n-sites 4 --times 0,0.5 --shots 1024 --output-dir /tmp/ibm-hardware
python scripts/run_hardware.py --provider braket-cloud --device-name sv1 --n-sites 4 --times 0,0.5 --shots 1024 --output-dir /tmp/braket-cloud
```

If dependencies are not installed, use:

```bash
python -m pip install -e '.[all]'
```
