# CurveRank QPE on IBM — runbook

How to reproduce the CurveRank quantum-phase-estimation results on the IBM path,
on the local emulator now and on real IBM hardware when you have a (free) token.

> **Claim boundary.** This recovers eigenvalues of finite truncated toy operators
> and benchmarks the quantum pipeline. It is spectral screening, not a proof of
> the Riemann Hypothesis or the Hilbert–Pólya conjecture.

## Emulator now (no credentials, no cost)

The IBM emulator path runs locally through Aer:

```bash
python scripts/run_curverank_ibm.py --emulator --n-basis 4,8,16 \
    --n-precision 6 --shots 4096 --yes
```

Output bundle in `results/curverank-ibm/`: `curverank-ibm-results.{json,csv}`,
`curverank-ibm-error.svg`, and a `curverank-ibm-ledger.jsonl` provenance entry.

Representative result (windowed `--method dense`, recovers each targeted
eigenvalue to within the phase resolution):

| n_basis | target | estimate | abs error | resolution |
|---:|---:|---:|---:|---:|
| 4 | 1.21031 | 1.21094 | 0.00063 | 0.0195 |
| 8 | 0.99596 | 0.99609 | 0.00013 | 0.0195 |
| 16 | 0.83628 | 0.83984 | 0.00356 | 0.0195 |

## Real IBM hardware (free Open plan)

1. Create an IBM Quantum account and copy your API token.
2. Save the account once:
   ```bash
   python -c "from qiskit_ibm_runtime import QiskitRuntimeService; \
       QiskitRuntimeService.save_account(channel='ibm_quantum', token='YOUR_TOKEN')"
   ```
   (Requires `pip install -e '.[quantum]'` plus `qiskit-ibm-runtime`.)
3. Run on a device:
   ```bash
   python scripts/run_curverank_ibm.py --device ibm_brisbane --n-basis 4 \
       --n-precision 3 --shots 4096 --yes
   ```

Without saved credentials the script detects this and **stages** the run,
printing these exact steps rather than failing.

## Honest expectations on hardware

- **Use small `--n-precision` (2–3) on hardware.** QPE depth grows with precision;
  current devices have limited coherence, so expect low-precision estimates plus
  device noise — a methodology demonstration, not high-precision spectroscopy.
- **`--method dense` vs `--method trotter`.** Per `results/curverank-hardware/`,
  the dense controlled unitary is actually *cheaper in CX* than Trotter up to
  n_basis=16, and is more accurate; Trotter is provided for scaling studies and,
  at the large windowed `tau`, its approximation error can exceed the nominal
  resolution (reported honestly in `absolute_error`).
- **Queue and cost.** Open-plan devices queue; plan for wait time. Mitigation
  (resilience / dynamical decoupling / twirling) is available through the IBM
  adapter (`src/gaugegap/providers/ibm_adapter.py`).
