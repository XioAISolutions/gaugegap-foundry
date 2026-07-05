# Perception Forge

Perception Forge is a bounded finite simulation track inspired by Donald
Hoffman's interface theory of perception and fitness-beats-truth work.

## Core Model

The first unit, `perception-0001`, compares two strategies under the same finite
percept budget:

- `truth-coded`: bins hidden world states by their objective order.
- `fitness-interface`: bins hidden world states by action-relevant payoff.

The environments deliberately use non-monotone payoffs.  In that setting, equal
truth bins alias different action payoffs, while an interface can group distant
world states that require the same action.  Replicator dynamics then updates the
population share from the strategies' expected payoffs.

## Why This Fits Foundry

This track converts a provocative cognitive-science claim into a finite artifact:

- hidden states are explicit;
- payoffs are explicit;
- percept budgets are explicit;
- strategy encodings are explicit;
- extinction is a numerical threshold, not a slogan;
- controls report what happens when truth is no longer resource-limited.

That makes it suitable for GaugeGap's evidence-first posture.

## Claim Boundary

Allowed language:

- finite evolutionary-game toy model
- fitness-interface outcompetes truth-coded bins in registered worlds
- limited percept-budget assumption
- Hoffman-inspired simulation

Avoid:

- proof that human perception is false
- proof that space-time is non-fundamental
- neuroscience result
- quantum-foundation result
- proof of conscious realism
- spiritual or metaphysical conclusion

## Criticism And Control

The model includes a `rich_truth_control_payoff`: when truth has one percept per
state and an action payoff oracle, the resource limit is removed.  That control
prevents the artifact from implying that truth must always lose under all
possible assumptions.

## Run

```bash
python scripts/run_perception_forge.py --world-count 12 --output-dir /tmp/perception-0001
```

The script emits `summary.json`, `worlds.csv`, `strategy_ledger.jsonl`, and
`perception_forge.svg`.
