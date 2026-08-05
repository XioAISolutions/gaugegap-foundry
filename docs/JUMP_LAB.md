# GaugeGap Jump Lab v0.1 — The Elevator

Jump Lab adds an experimental **E → J → A → S** path beside GaugeGap's
verification-first infrastructure:

1. **Experience:** two black-box elevator worlds expose sensor readings and
   controllable interventions, while causal state remains hidden from the agent.
2. **Jump:** an auditable abductive executive preserves competing explanations
   and selects discriminating experiments.
3. **Axiom:** the winning explanation is compiled into an explicitly scoped,
   falsifiable machine-readable candidate.
4. **Systematic deduction:** GaugeGap sweeps masses and compositions, checks the
   local claim, and separately probes a scope boundary using an external frame.
5. **Salience:** a lightweight spiking controller ranks attention and learns
   which interventions were useful. It never determines truth.

## Run

```bash
python -m gaugegap.jump_lab --out artifacts/elevator-experiment.crumb.json
pytest -q tests/test_jump_lab.py
```

The generated artifact is compatible with the CrumbLLM EJA v1 validator.

## Honest claim boundary

This release is a deterministic Newtonian benchmark. It demonstrates a
replayable architecture for moving from observations to competing hypotheses,
interventions, a scoped candidate axiom, and verification. It does **not**
recreate Einstein's historical discovery, prove that LLMs can or cannot perform
abduction, or implement general relativity.
