# IBM Runtime Submission Guardrail

Boundary: **finite-system exploratory IBM Runtime plan only; no continuum Yang-Mills mass-gap claim and no proof claim.**

IBM Runtime is optional and never used by default. GaugeGap treats a QPU job as a noisy finite-system experiment, not theorem evidence.

## Dry run

```bash
python scripts/submit_ibm_runtime_candidate.py \
  --dry-run \
  --n-plaquettes 1 \
  --output-dir /tmp/gaugegap-runtime-dryrun
```

The dry run writes `runtime_submission_plan.json` and `RUNTIME_SUBMISSION_SUMMARY.md`. It records intended resources, import availability, backend intent, and warnings. It does not submit a job and does not inspect credentials unless `--allow-service-probe` is explicitly passed.

## Explicit live submission

```bash
python scripts/submit_ibm_runtime_candidate.py \
  --submit-runtime \
  --i-understand-this-is-finite-system-only \
  --backend <backend-name> \
  --n-plaquettes 1 \
  --output-dir /tmp/gaugegap-runtime-submit
```

Live submission requires both `--submit-runtime` and `--i-understand-this-is-finite-system-only`. Use `--backend <backend-name>` or `--least-busy` so backend selection is explicit.

## Credential policy

- Runtime credentials must be configured through Qiskit/IBM's secure local setup.
- Tokens are never printed.
- Tokens are never written to JSON, Markdown, logs, or proofpacks.
- Ordinary Qiskit validation does not check credentials.

## Required wording

Every Runtime plan must state:

- finite-system exploratory job;
- no continuum mass-gap claim;
- no proof claim;
- hardware data is noisy and not theorem evidence.

Hardware results are noisy experimental artifacts and do not constitute mathematical proof.
