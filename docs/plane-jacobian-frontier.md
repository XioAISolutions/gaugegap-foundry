# Plane Jacobian Frontier: the `(72,108)` audit

The two-variable Jacobian conjecture remains open. Guccione, Guccione,
Horruitiner, and Valqui reduced the degree frontier below `125` to one exceptional
pair, `(72,108)` and its symmetric orientation, and described explicit reduced
Newton polygons in Proposition 4.3 of arXiv:2204.14178.

This track asks a narrower verification question:

> Can we independently reconstruct one reduced system and turn its low-degree
> proof-route obstructions into explicit, machine-checkable certificates?

The answer is now **yes at parameter degrees 1 and 2** inside the declared
H-restricted polynomial-covector route.

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
the top-order vector condition for lower operator `(1,0)`, and let `r` be the
corresponding exact right-hand side. A solution would require

```text
B_(1,0) u = r.
```

GaugeGap emits a ten-row integer covector `c`, indexed by Q-lattice points:

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
second says it does not annihilate the required target. Therefore
`B_(1,0)u=r` is inconsistent over the rationals.

This proves:

> No parameter-degree-1 polynomial covector exists in this declared
> H-restricted route.

The test suite changes one certificate entry and requires verification to fail.

## Exact parameter-degree-2 certificate

The next necessary subsystem uses lower-operator support

```text
{(0,1), (1,0), (3,5)}.
```

The complete declared subsystem contains

```text
1250 equations
1485 unknown coefficients
```

A prime-field elimination is used only to locate a compact contradictory row
set. The chosen subsystem contains

```text
875 selected rows
924 active coefficient columns
exact coefficient rank 874
```

GaugeGap then repeats the elimination over `Fraction`, tracks every row
operation, clears denominators, primitive-normalizes the dependency, and emits a
left-null certificate with `102` nonzero integer row weights.

The final certificate is checked against the original exact rational rows—not
against their modular images—and verifies

```text
c_2^T A_2 = 0
c_2^T b_2 = -621,160,607,786,489,971,200
```

Because the coefficient residual is identically zero while the target pairing is
nonzero, the degree-2 subsystem is inconsistent over `Q`.

This proves:

> No parameter-degree-2 polynomial covector can satisfy the full declared
> H-restricted route, because any full solution would restrict to this
> inconsistent necessary subsystem.

The exact certificate has digest

```text
18f96fbd550b2d48f3b4e4e035b7f8dbf05553a9f782743c30fc214a7d9904ad
```

and is regenerated from the source polygons in roughly seconds on a normal CPU.

## Why the exact lift matters

The prior two-prime computation was useful evidence but not, by itself, a proof
over `Q`. For example, `2x=1` is solvable over `Q` but inconsistent modulo `2`.
A rational solution may have a denominator divisible by a tested prime.

The new result removes that gap at parameter degree 2: modular arithmetic only
selects the row subsystem; the published contradiction is re-derived and
verified with exact rational arithmetic.

## What was learned

The run now establishes four things:

1. the GGHV polygon and row-pool transcription is independently executable;
2. parameter degree 1 is closed by a compact ten-row exact certificate;
3. parameter degree 2 is closed by a 102-row exact certificate;
4. neither finite result licenses extrapolation to every polynomial degree or to
   rational and chartwise certificate families.

This is meaningful progress on a proof program, not a solution of `(72,108)`.

## Remaining theorem gap

### 1. General polynomial degree

The next target is to identify a stable support, grading, recurrence, or transport
law explaining the degree-1 and degree-2 contradictions and proving obstruction
at every polynomial parameter degree. Testing degrees `3,4,...` one at a time is
useful reconnaissance but cannot establish the universal statement.

### 2. Rational and chartwise certificates

Polynomial truncation failure does not exclude covectors with parameter-dependent
denominators or a finite algebraic chart cover. Those routes require their own
exact argument.

### 3. Simultaneous interior coefficients

The source reduction allows multiple interior coefficients to vary together.
Axis-by-axis symbolic checks and dense sampling are insufficient; the final
closure needs one simultaneous certificate, a finite algebraic cover, or a
structural theorem.

### 4. Complete reduction-chain audit

Any floor-raising theorem inherits every hypothesis and convention in the
published reduction. A publication-ready result must recheck the relevant
normalizations, Newton-polygon conventions, and branch completeness from the
primary source.

## Run it

```bash
foundry run plane-frontier-0001-audit
foundry run plane-frontier-0002-degree2-exact
```

or directly:

```bash
python scripts/run_plane_frontier.py \
  --output-dir artifacts/plane-frontier-0001

python scripts/run_plane_frontier_degree2.py \
  --output-dir artifacts/plane-frontier-0002
```

The runners emit deterministic JSON records containing the polygon inventories,
base rank, exact certificates, explicit claim boundaries, and SHA-256 digests.

## Sources and attribution

- Guccione, Guccione, Horruitiner, Valqui, *Increasing the degree lower bound for
  the two-dimensional Jacobian Conjecture from 100 to 108*, arXiv:2204.14178.
- Felipe Santibañez-Leal, `CAOS_RESEARCH`, MIT-licensed experiment ledger and
  planar-program preprint, used as an external comparison target.

The GaugeGap implementation is an independent audit and exact reformulation. A
targeted search did not locate this particular 102-row integer certificate, but
absence from search does not establish historical priority. Its evidence label
is therefore `DERIVED_EXACT` with novelty status `UNESTABLISHED` pending expert
review.

## Claim boundary

The exact certificates exclude parameter-degree-1 and parameter-degree-2
polynomial covectors in the declared H-restricted route. They do not exclude
higher-degree, rational, or chartwise certificates; cover every simultaneous
interior coefficient; eliminate `(72,108)`; raise the global degree bound; or
solve the two-variable Jacobian conjecture.
