# Running on real quantum hardware (IBM) — runbook

Everything in this repo runs by default on the local Aer simulator. The hardware
path is **staged**: it is wired end-to-end but only becomes a hardware result once a
provider returns a job id. Without credentials, requesting a device is reported as
`staged` and the report keeps saying "maximum quantum level reached: simulation".
Nothing is ever labelled a hardware result without a real `job_id`
(`hardware_confirmed` gate in `scripts/run_curverank_ibm.run_one`).

## One-time setup

1. Create a free IBM Quantum account and copy your API token.
2. Save it:
   ```bash
   python -c "from qiskit_ibm_runtime import QiskitRuntimeService; \
     QiskitRuntimeService.save_account(channel='ibm_quantum', token='YOUR_TOKEN')"
   ```

## Run

```bash
# windowed QPE on a real device
python scripts/run_curverank_ibm.py --device ibm_brisbane --yes

# the unified pipeline / certified bracket can target a device too
python scripts/run_unified_pipeline.py --qpe-device ibm_brisbane
```

The result ledger then records `job_id`, `backend`, `shots`, and a calibration
snapshot, and only then is `hardware_confirmed` true. Expect queue time; the free
Open plan works for small circuits.

## Claim boundary

A run is a hardware result **only** when the ledger contains a provider job id. Until
then it is simulation, stated as such. This repo does not fabricate hardware results.
