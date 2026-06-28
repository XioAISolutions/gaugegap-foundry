# InfoGap 0001 — Quantum No-Hiding

The no-hiding theorem says that when a quantum channel removes every dependence on an unknown input state from one subsystem, the missing state cannot live only in correlations. In a unitary dilation, it must be recoverable from the complementary subsystem.

GaugeGap Foundry implements one exact finite realization:

```text
input:   |psi>_S |0>_A |0>_B
circuit: SWAP(S,B) -> H(S) -> CNOT(S,A)
output:  |Phi+>_SA |psi>_B
```

The system qubit `S` is maximally mixed, the environment qubit `B` contains the original state, and `S,A` form a fixed Bell pair independent of the input.

## Run

```bash
foundry run infogap-0001-no-hiding
```

Reduced smoke run:

```bash
foundry run infogap-smoke
```

The result directory contains:

- `summary.json` — circuit, parameters, audits, provider metadata, and claim boundary;
- `cases.csv` — canonical and fixed-seed Haar-state results;
- `no_hiding_flow.svg` — static information-flow diagram.

## Audits

The benchmark checks:

- system marginal distance from `I/2`;
- pairwise system-output dependence across input states;
- environment-only recovery fidelity;
- recovered-state trace distance and Bloch-vector error;
- Bell-pair fidelity on `S,A`;
- system, recovery, environment, and global purities and entropies;
- `I(S:E)` and `I(S:B)` mutual information;
- unitary residual;
- Kraus completeness for an independent depolarizing-channel check;
- deterministic local-provider sampling metadata;
- circuit matrix SHA-256 digest.

Canonical inputs are `|0>`, `|1>`, `|+>`, `|->`, `|+i>`, and `|-i>`, followed by fixed-seed Haar states.

## Experience / Experiment

Generate the complete ten-scene interface:

```bash
foundry run foundry-experience-v2
```

The **Information Cannot Disappear** scene provides four views:

| Selector | View |
|---|---|
| `x / y` | information flow from input through unitary to system and environment |
| `x / z` | input, bleached-system, and recovered Bloch spheres |
| `y / z` | entropy and mutual-information ledger |
| `rotating 3-D` | three-wire unitary circuit |

The `theta` and `phi` controls change the unknown input qubit. The system remains fixed at `I/2`, while the recovered environment Bloch vector tracks the input.

## Known-answer integration

`benchmarks/known_answers.json` contains a generic-qubit no-hiding case. The repository-wide scientific benchmark gate fails if bleaching, recovery, Bell-pair preparation, entropy, mutual information, unitarity, or channel completeness exceeds its configured numerical budget.

## Scientific boundary

This artifact is:

- an exact finite three-qubit construction;
- a deterministic numerical audit of that construction;
- a provider-portable finite benchmark;
- an interactive scientific communication scene.

It is not:

- a new proof of the general no-hiding theorem;
- a resolution of the black-hole information paradox;
- evidence that arbitrary macroscopic environmental recovery is practical;
- a continuum quantum-gravity calculation;
- a Millennium Prize result.

The implementation demonstrates the theorem's finite mechanism: information apparently removed from the selected system has moved into the environment and can be recovered there without acting on the bleached system.
