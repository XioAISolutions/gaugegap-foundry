# Plane Jacobian Frontier: the `(72,108)` audit

The two-variable Jacobian conjecture remains open. Guccione, Guccione,
Horruitiner, and Valqui reduced the degree frontier below `125` to one exceptional
pair, `(72,108)` and its symmetric orientation, and described explicit reduced
Newton polygons in Proposition 4.3 of arXiv:2204.14178.

This track asks a narrower verification question:

> Can we independently reconstruct one reduced system and turn its low-degree
> proof-route obstructions into explicit, machine-checkable certificates?

The first answer is **yes at parameter degree 1**, and **finite-field evidence at
parameter degree 2**.

## Source polygons

The registered polygons are

```text
P: (0,0), (1,0), (8,14), (8,16), (0,8)
Q: (0,0), (2,1), (12,21), (12,24), (0,12)
```

Their non-negative lattice inventories contain

```text
P lattice points: 61
Q lattice points: 125
lower P operators after the forced top edge: 51
```

The forced top edge is the coefficient expansion of

```text
y^8 (xy - 1)^8
```

with the additional `x` term used by the normalized `t=1` chart.

On the declared H-restricted row pool, the exact rational base matrix has

```text
shape: 125 x 289
rank: 124
kernel dimension: 165
```

These values are recomputed from the polygon data, not stored as assumed
constants.

## Exact parameter-degree-1 certificate

Let `B_(1,0)` denote the `125 x 165` matrix mapping the degree-1 gauge freedom to
the top-order vector condition for the lower operator `(1,0)`, and let `r` be the
corresponding exact right-hand side. A solution would require

```text
B_(1,0) u = r.
```

GaugeGap emits the following ten-row integer covector `c`, indexed by Q-lattice
points:

```text
(0,8)   ->     2,516,085
(1,9)   ->   -19,739,720
(2,1)   ->      -218,790
(2,10)  ->    67,474,836
(3,11)  ->  -130,876,200
(4,12)  ->   156,726,570
(5,13)  ->  -117,338,760
(6,14)  ->    52,072,020
(7,15)  ->   -11,143,704
(9,17)  ->       308,880
```

Exact rational substitution verifies

```text
c^T B_(1,0) = 0
c^T r       = -126,023,040
```

The first identity says `c` annihilates every possible gauge adjustment. The
second says it does not annihilate the required target. Therefore the equation
`B_(1,0)u=r` is inconsistent over the rationals.

This is an actual finite proof certificate for the statement:

> No parameter-degree-1 polynomial covector exists in this declared
> H-restricted route.

The test suite changes one certificate entry and requires the verification to
fail.

## Parameter-degree-2 evidence

The next registered support is

```text
{(0,1), (1,0), (3,5)}.
```

For each of two large primes, the runner constructs the full declared augmented
system:

```text
rows:    1250
columns: 1486
rank before the inconsistent tail: 882
```

It is infeasible over both fields:

```text
p = 2,147,483,629
p = 2,147,483,587
```

That independently reproduces the reported finite-field obstruction.

### Why this is not yet a rational proof

A common but invalid shortcut is to say that an integer linear system becoming
inconsistent modulo one or several primes is automatically inconsistent over
`Q`. For example, `2x=1` is solvable over `Q` but inconsistent modulo `2`.
A rational solution may have a denominator divisible by every tested prime.

Therefore GaugeGap labels the degree-2 result exactly as

```text
FINITE_FIELD_EVIDENCE_NOT_Q_CERTIFICATE
```

The correct upgrade is to produce and verify an exact rational left-null
certificate, or an integer certificate whose nonzero target pairing is checked
directly.

## What was learned

The run gives three useful results:

1. the GGHV polygon and row-pool transcription is independently executable;
2. parameter degree 1 is closed by a compact exact certificate;
3. parameter degree 2 has a stable two-prime obstruction, but the rational lift
   remains a real theorem gap rather than being silently assumed.

This is progress on a proof program, not a solution of `(72,108)`.

## Next theorem targets

The work now branches in this order:

### 1. Lift the degree-2 obstruction

Track the modular contradiction, identify a compact inconsistent subsystem, and
recover an exact rational covector `c` satisfying

```text
c^T A = 0,
c^T b != 0.
```

Only this upgrade closes parameter degree 2 over `Q`.

### 2. Search for a general-degree obstruction

If exact certificates at degrees 1, 2, and higher share a stable support or
factorization, state and prove a recurrence or grading lemma covering every
polynomial degree. Finite checks alone cannot justify this extrapolation.

### 3. Cover all simultaneous interior coefficients

The source reduction allows multiple interior coefficients to vary together.
Axis-by-axis symbolic checks and dense sampling are insufficient; the final
closure needs one simultaneous certificate, a finite algebraic chart cover, or a
structural theorem.

### 4. Audit the complete reduction chain

Any floor-raising theorem inherits every hypothesis and convention in the
published reduction. A publication-ready proof must recheck the relevant
normalizations, Newton-polygon conventions, and branch completeness from the
primary paper.

## Run it

```bash
foundry run plane-frontier-0001-audit
foundry run plane-frontier-0001-smoke
```

or directly:

```bash
python scripts/run_plane_frontier.py \
  --output-dir artifacts/plane-frontier-0001
```

The runner emits a deterministic JSON audit containing the polygon inventories,
base rank, exact ten-row certificate, two-prime degree-2 evidence, claim boundary,
and SHA-256 digest.

## Sources and attribution

- Guccione, Guccione, Horruitiner, Valqui, *Increasing the degree lower bound for
  the two-dimensional Jacobian Conjecture from 100 to 108*, arXiv:2204.14178.
- Felipe Santibañez-Leal, `CAOS_RESEARCH`, MIT-licensed experiment ledger and
  planar-program preprint, used as an external comparison target.

The implementation in GaugeGap is an independent audit and reformulation. No
historical-priority claim is made for the obstruction itself.

## Claim boundary

The exact degree-1 certificate closes one polynomial-covector route in the
declared H-restricted system. The degree-2 result is a two-prime modular
reproduction only. These results do not cover every interior coefficient,
eliminate `(72,108)`, raise the global degree bound, or solve the two-variable
Jacobian conjecture.
