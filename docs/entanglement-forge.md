# Entanglement Forge

Entanglement Forge is a finite Bell-state benchmark.  It computes the CHSH value
for a two-qubit singlet state and pairs the violation with an explicit
no-signaling audit.

## Core Model

The unit `entangle-0001` uses the singlet state:

```text
|psi> = (|01> - |10>) / sqrt(2)
```

It evaluates:

```text
S = |E(A0,B0) + E(A0,B1) + E(A1,B0) - E(A1,B1)|
```

with the registered axes:

- `A0 = sigma_z`;
- `A1 = sigma_x`;
- `B0 = (z + x)/sqrt(2)`;
- `B1 = (z - x)/sqrt(2)`.

The expected finite result is the Tsirelson value `2*sqrt(2)`, above the
classical CHSH bound `2`.

## No-Signaling Gate

The runner also computes joint probabilities and checks local marginals:

```text
P(a | x, y=0) = P(a | x, y=1)
P(b | x=0, y) = P(b | x=1, y)
```

That residual is the guardrail against the common "instant communication"
mistake.  The Bluetooth analogy can help explain paired intuition, but in this
repo it is explicitly only an analogy.  The artifact demonstrates correlation
structure, not a communication channel.

The report records the local marginal range as well.  For the registered singlet
case, each side still sees random local outcomes even though the joint
correlations violate the classical CHSH bound.

## Technology Context

Entanglement matters for quantum cryptography, quantum computing, and quantum
teleportation protocols.  In this forge those are context labels only.  The
artifact does not implement a key exchange, an algorithm, a hardware experiment,
or teleportation of matter.

## Why This Fits Foundry

This track complements InfoGap/no-hiding and UQT:

- it gives a finite non-classical correlation signal;
- it adds a no-signaling boundary to prevent overclaiming;
- it provides a clean "classical bound vs quantum bound" term for the Quantum
  Gap Functional.

## Claim Boundary

Allowed language:

- finite two-qubit Bell-state calculation;
- CHSH value exceeds the classical bound for registered axes;
- no-signaling residual is below tolerance;
- local marginals remain random;
- Bluetooth is only a teaching analogy.

Avoid:

- faster-than-light communication;
- hardware Bell experiment claim;
- teleportation of matter;
- proof of an interpretation of quantum mechanics.

## Run

```bash
python scripts/run_entanglement_forge.py --output-dir /tmp/entangle-0001
```

The script emits `summary.json`, `correlations.csv`,
`joint_probabilities.csv`, `ledger.jsonl`, and `entanglement_forge.svg`.
