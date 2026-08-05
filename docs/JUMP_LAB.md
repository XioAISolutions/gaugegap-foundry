# GaugeGap Jump Lab v0.2 — The Elevator

Jump Lab adds an experimental **E → J → A → S** path beside GaugeGap's
verification-first infrastructure:

1. **Experience:** two black-box elevator worlds expose sensor readings and
   controllable interventions, while causal state remains hidden from the agent.
2. **Jump:** an auditable abductive executive preserves competing explanations
   and selects discriminating experiments.
3. **Axiom:** the winning explanation is compiled into an explicitly scoped,
   falsifiable machine-readable candidate only after configurable evidence gates
   are satisfied.
4. **Systematic deduction:** GaugeGap sweeps masses and compositions, checks the
   local claim, and separately probes a scope boundary using an external frame.
5. **Salience:** a lightweight spiking controller ranks attention and learns
   which interventions were useful. It never determines truth.

## What v0.2 adds

- configurable salience or fixed-order policies;
- evidence-aware early stopping;
- bounded runs that refuse to compile an axiom prematurely;
- run metrics for experiment count, local invariance tests and scope-boundary
  coverage;
- a paired salience-versus-baseline benchmark;
- portable five-panel HTML discovery reports;
- portable HTML benchmark reports.

## Run the discovery demonstration

```bash
python -m gaugegap.jump_lab \
  --out artifacts/elevator-experiment.crumb.json \
  --html artifacts/elevator-experiment.html

# Installed console command
gaugegap-jump-lab --out artifacts/run.json --html artifacts/run.html
```

Run the fixed baseline or disable early stopping:

```bash
gaugegap-jump-lab --no-salience
gaugegap-jump-lab --no-early-stop
gaugegap-jump-lab --max-interventions 1
```

A bounded run that does not meet the evidence threshold records
`discovery_complete: false` and leaves `candidate_axiom` unset.

## Benchmark the salience controller

```bash
python -m gaugegap.jump_lab.benchmark \
  --out artifacts/jump-lab-benchmark.json \
  --html artifacts/jump-lab-benchmark.html

# Installed console command
gaugegap-jump-benchmark
```

The paired benchmark gives both policies the same world, hypothesis updates,
stop conditions and verifier. Only intervention ordering changes. The benchmark
is deliberately narrow: it measures one hand-authored policy in one toy world,
not general superiority of spiking neural networks.

## CRUMB handoff

The generated artifact is compatible with the CrumbLLM EJA validator and pack
commands:

```bash
crumblm eja validate artifacts/elevator-experiment.crumb.json
crumblm eja validate-pack artifacts --html artifacts/eja-pack.html
```

## Honest claim boundary

This release is a deterministic Newtonian benchmark. It demonstrates a
replayable architecture for moving from observations to competing hypotheses,
interventions, a scoped candidate axiom, and verification. It does **not**
recreate Einstein's historical discovery, prove that LLMs can or cannot perform
abduction, establish that SNNs generally improve scientific search, or implement
general relativity.
