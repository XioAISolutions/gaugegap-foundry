# GaugeGap Foundry Agent Instructions

## Claim boundary

Never describe this repository as solving, proving, or experimentally resolving
the Yang-Mills mass gap problem. Current work is finite-system benchmarking and
verification infrastructure.

Use precise language:

- finite-system mass-gap benchmark
- Z2 dual-chain sanity benchmark
- exact diagonalization baseline
- simulator or backend comparison
- hypothesis pruning

Avoid:

- proof of Yang-Mills
- AI discovered the mass gap
- quantum computer proves the theorem

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

If dependencies are not installed, use:

```bash
python -m pip install -e .
```
