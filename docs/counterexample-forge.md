# Counterexample Forge

Counterexample Forge converts a universal mathematical claim into a bounded search
for a small, executable falsifying witness.

The governing question is:

> What is the smallest explicit object that would make this statement false?

A language model may propose candidates, but model confidence never certifies a
result. Candidates advance only through exact, fail-closed verification gates.

## Release labels

Every public result must carry one of three labels:

- **REPRODUCED** — the Foundry checked a previously public witness;
- **REDISCOVERED** — a bounded search recovered an existing result without being
  given its final formula;
- **DISCOVERED** — a candidate believed to be new has been independently checked
  and released with a reproducible proofpack.

The labels are evidence states, not marketing language. Verification of a known
map must never be presented as an original mathematical discovery.

## `counterexample-forge-0001`

The first known-answer task is an exact polynomial map
`F : C^3 -> C^3`. The registered coordinates are built over rational
coefficients, its Jacobian determinant simplifies identically to `-2`, and the
following three pairwise-distinct points share the exact image `(-1/4, 0, 0)`:

```text
(0, 0, -1/4)
(1, -3/2, 13/2)
(-1, 3/2, 13/2)
```

The v1 implementation deliberately uses a small internal sparse-polynomial
engine and Python `Fraction` arithmetic. It does not depend on floating-point
sampling or an external computer-algebra service.

## Exact gates

The verifier records independent pass/fail gates for:

1. an identically constant nonzero Jacobian determinant;
2. the expected determinant when the benchmark declares one;
3. exact witness dimensions and scalar types;
4. pairwise distinct witness points;
5. one exact common image.

Changing a coefficient, duplicating a witness, supplying a floating-point value,
or changing a witness image must fail closed.

## Deterministic proofpack

A successful run emits schema
`gaugegap.counterexample_proofpack.v1`, containing:

- the canonical sparse polynomial map;
- exact rational coefficients and witnesses;
- candidate complexity and SHA-256 digest;
- every verification gate;
- determinant and common image;
- release label;
- proofpack digest;
- explicit claim boundary.

Run:

```bash
foundry run counterexample-forge-0001-verify
foundry run counterexample-forge-smoke
```

The direct runner is:

```bash
python scripts/run_counterexample_forge.py \
  --output-dir artifacts/counterexample-forge-0001 \
  --release-label REPRODUCED
```

## What v1 does not claim

V1 verifies a public exact witness. It does not yet claim independent
rediscovery, minimality, an autonomous theorem-discovery system, or resolution
of a separately open lower-dimensional Jacobian case.

## Next rungs

### Reconstruction mode

Define a constrained sparse polynomial ansatz and ask an exact solver to recover
coefficients satisfying both the constant-Jacobian and collision equations. The
final published coefficients must not appear in the reconstruction input.

### Blind bounded search

Add deterministic, seedable enumeration and mutation over declared grammars with
budgets for degree, coefficient size, candidate count, and runtime. Every search
must record negative results as honestly as positive ones.

### Adversarial critic

Reject rational functions, numerical-only identities, domain mismatches,
coordinate padding, trivial equivalences, and mismatches between the prose claim
and its executable falsification predicate.

### Formal bridge

Export the exact finite identities into Lean or Coq and distinguish generated
theorem skeletons from discharged checked certificates.
