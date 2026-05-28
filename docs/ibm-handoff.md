# IBM Quantum Integration Handoff

**Purpose**: invite an IBM Quantum / Qiskit Runtime expert to review the integration in this repo and recommend improvements before we start spending QPU credits.

**Audience**: someone familiar with `qiskit-ibm-runtime` 0.34+, SamplerV2/EstimatorV2 primitives, ISA circuits, dynamical decoupling, ZNE, and the current state of IBM Heron processors.

**Scope**: only the IBM integration. The repo also has Braket and OriginQ runners, but they are out of scope here.

## What is implemented

The IBM integration consists of one library module and one CLI script that target Heron/Eagle backends through Qiskit Runtime.

### Library: `src/gaugegap/ibm_runtime_runner.py`

Public functions:

| Function | Purpose |
|---|---|
| `list_backends(simulator, min_qubits)` | Wraps `service.backends(operational=True, ...)` |
| `backend_metadata(name)` | Returns name, num_qubits, operation_names |
| `run_sampler(circuit, backend_name, shots, resilience_level, dynamical_decoupling)` | Submits a SamplerV2 job |
| `run_estimator(circuit, observables, ...)` | Submits an EstimatorV2 job |

Key choices made:
- `QiskitRuntimeService()` reads credentials from saved-account or env (`QISKIT_IBM_TOKEN`, `QISKIT_IBM_INSTANCE`)
- Auto-select backend via `service.least_busy(operational=True, simulator=False, min_num_qubits=circuit.num_qubits)` if `backend_name` is not given
- Transpilation: `generate_preset_pass_manager(optimization_level=2, backend=backend)`, then `pm.run(circuit)`
- Estimator: observables go through `obs.apply_layout(isa_circuit.layout)` so they align with the routed circuit
- Sampler counts read from `pub_result.data.meas.get_counts()` with a fallback to `pub_result.data.c.get_counts()`
- Default sampler options: `resilience_level=1`, `dynamical_decoupling.enable=True`, `dynamical_decoupling.sequence_type="XpXm"`
- Default estimator options: `resilience_level=2` plus the same DD

### CLI: `scripts/run_hardware.py --provider ibm`

This is the entry point. It builds a TFIM Trotter circuit (`build_tfim_trotter_circuit` from `qiskit_dynamics.py`), submits it via `run_sampler`, then converts counts into Z and ZZ expectation values via `counts_z_observables`. Every record in the JSONL ledger includes `provider`, `backend_name`, `job_id`, `shots`, `resilience_level`, `dynamical_decoupling`, `isa_circuit_depth`, `isa_circuit_size`, and the git commit.

### Circuit being submitted

A transverse-field Ising Trotter circuit, n_sites=4 by default:

```text
initial_state in {zeros, ones, domain_wall}
for _ in range(steps):
    for site in range(n_sites - 1):
        circuit.rzz(-2 * J * dt, site, site+1)
    for site in range(n_sites):
        circuit.rx(-2 * h * dt, site)
circuit.measure_all()
```

Reference (statevector) results for this circuit are committed at `results/analysis/cross-platform-validation.json`. They are the agreement target for any IBM hardware run.

## How to reproduce

```bash
python -m pip install -e '.[quantum]'
export QISKIT_IBM_TOKEN="..."             # or QiskitRuntimeService.save_account(...)
export QISKIT_IBM_INSTANCE="..."

python scripts/quantum_status.py --probe-ibm --output-dir /tmp/ibm-probe
python scripts/run_hardware.py \
    --provider ibm \
    --n-sites 4 --times 0,0.25,0.5,1.0 --shots 1024 \
    --output-dir results/hardware
```

The ledger lands at `results/hardware/gaugegap-0001-ibm-hardware.{jsonl,csv}`.

## Specific things to review and improve

Tagged so they're easy to answer one-by-one.

### IBM-1. Channel and instance configuration

Currently `QiskitRuntimeService()` is called with no arguments and relies on environment / saved-account. Should we explicitly pass `channel="ibm_quantum"` vs `channel="ibm_cloud"`? The two have different instance string formats and the silent default surprised us in testing.

### IBM-2. Transpilation level

`optimization_level=2` was chosen as a compromise. For depth-4 Trotter on Heron, is `optimization_level=3` worth the longer compile time? Are there backend-specific pass managers that work better for nearest-neighbor TFIM circuits?

### IBM-3. Dynamical decoupling sequence

We set `dynamical_decoupling.sequence_type="XpXm"`. Is that the right default for Heron's median T1/T2? Should it be `XX` or `XY4` instead for these circuits? Should DD be off for idle qubits when the entire circuit is short?

### IBM-4. Resilience levels

Sampler defaults to `resilience_level=1`. Estimator defaults to `resilience_level=2`. Are those the levels you'd recommend for a published cross-platform benchmark, or would you push Estimator to 3 (PEC) given the small circuit?

### IBM-5. SamplerV2 vs EstimatorV2 for Z/ZZ

The current pipeline submits the Sampler, gets counts, then computes `<Z_i>` and `<Z_i Z_{i+1}>` classically from bitstrings. An Estimator submission with explicit Pauli observables would let IBM apply error mitigation per observable. Is the Estimator route the better default for this benchmark, and if so what's the right operator construction (commuting groups, twirling, ZNE noise factors)?

### IBM-6. Layout selection

We let the preset pass manager choose the initial layout. For a TFIM ring/chain on Heron's heavy-hex, is there a known-good qubit subset we should pin via `initial_layout`? Are there backend properties (gate errors, T1, readout assignment) we should query and rank against?

### IBM-7. Twirling

`twirling.enable_gates` and `twirling.enable_measure` are not configured (defaults). Should we enable Pauli twirling for the 2-qubit gates and measurement twirling for the readout? Cost in shots vs benefit?

### IBM-8. Calibration capture in the ledger

The ledger records `backend_name`, `job_id`, `shots`, ISA depth/size, but not the calibration snapshot (T1, T2, gate errors, readout errors at submission time). What's the canonical way to capture that — `backend.properties()` snapshot, `backend.target` dump, or the `job.metrics()` post-run? We want every hardware row reproducible against the calibration that was live at submission.

### IBM-9. Counts data access

We read counts via:
```python
if hasattr(pub_result.data, "meas"):
    counts = dict(pub_result.data.meas.get_counts())
elif hasattr(pub_result.data, "c"):
    counts = dict(pub_result.data.c.get_counts())
```
That's defensive but feels wrong. What's the right accessor across recent `qiskit-ibm-runtime` versions, and is there a canonical way to handle multiple classical registers?

### IBM-10. Failure modes

We have no retry logic for transient queue or service errors. What's the recommended retry pattern for SamplerV2 with idempotent observables? Should we use a session for repeated submissions or stay with batch mode?

### IBM-11. Fractional gates / dynamic circuits

Qiskit 1.4+ supports fractional gates and dynamic circuits on some Heron backends. Our Trotter circuit could be expressed with `RZZ` as a fractional gate natively. Worth enabling? What's the right way to detect backend support and feature-flag the codepath?

### IBM-12. SamplerV2 default_shots vs run() shots

Currently we set `sampler.options.default_shots = shots` AND pass shots via the circuit. Is one of those redundant or wrong? Which path does the primitive actually honor?

### IBM-13. Q-Ctrl Fire Opal / Qiskit Functions

For TFIM dynamics specifically, is QUICK-PDE or a Q-Ctrl-style premium function the right path on Premium/Flex/On-Prem plans? Or do we get most of the value from the open-source primitives once the resilience settings are right?

## What we explicitly do not do (yet)

- We do not call `Session` or `Batch`. Everything goes through `mode=backend`.
- We do not use the `noise_factors` / ZNE explicitly — we rely on the resilience-level abstraction.
- We do not submit Estimator from the CLI yet. `run_estimator` exists in the library but `run_hardware.py` only wires the Sampler path.
- We do not cache transpiled circuits. Each submission re-runs the pass manager.
- We do not record `job.metrics()` in the ledger.
- We do not pin a `optimization_level=2` reproducible seed for the pass manager.

## Cross-platform context

The local-simulator baseline already agrees on the same circuits across Qiskit statevector, Qiskit Aer, AWS Braket local, and OriginQ CPUQVM. Result: 168 comparisons, 167 pass, 1 shot-noise warning, 0 failures. See `results/analysis/cross-platform-validation.json`. Any IBM hardware result will be diffed against the Qiskit statevector reference; the agreement (or disagreement pattern) is what we want to characterize.

## Where to send feedback

Open issues or PR comments on this branch / PR. Tag findings with the IBM-N identifiers above so we can address them one at a time.

Files most relevant to a review:

- `src/gaugegap/ibm_runtime_runner.py`
- `scripts/run_hardware.py` (lines that handle `--provider ibm`)
- `src/gaugegap/qiskit_dynamics.py` (the circuit being submitted)
- `results/analysis/cross-platform-validation.json` (the simulator baseline)
- `tests/test_ibm_runtime_runner.py` (current coverage, intentionally minimal — no hardware calls in tests)
