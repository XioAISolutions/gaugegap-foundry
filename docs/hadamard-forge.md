# Hadamard Forge

Hadamard Forge verifies finite existence witnesses over the exact integers. A
Hadamard matrix of order `n` is an `n x n` matrix over `{+1, -1}` whose rows are
pairwise orthogonal:

```text
H @ H.T == n * I
```

That identity is a finite statement about integers, so the verifier never
touches floating point. Rows are stored as arbitrary-precision bitmasks and each
inner product is evaluated as

```text
<row_i, row_j> = n - 2 * popcount(row_i XOR row_j)
```

which is exactly the textbook sum of products over the `+-1` alphabet. The
identity behind that rewrite is machine-checked in
[`formal/hadamard/gram_identity.v`](../formal/hadamard/gram_identity.v).

## Three separated concerns

The track deliberately splits what the literature usually bundles:

| Concern | What it does | What it is trusted for |
| --- | --- | --- |
| Construction | emits a witness from a classical family | nothing — its output is verified like any other |
| Ingestion | decodes an external witness file | nothing — every entry is re-checked |
| Verification | discharges exact integer gates | this is the only thing that certifies |

Because construction and verification never share a code path's conclusions, a
bug in a constructor cannot manufacture a passing certificate — it produces a
matrix that fails the Gram gate.

## Exact gates

Every gate is recorded with an independent pass/fail state, and a single failing
gate suppresses the certificate:

- `admissible_order` — `n` is 1, 2, or a multiple of 4 (a necessary condition);
- `expected_order` — the ingested order is the one that was requested;
- `square_pm1_alphabet` — the decoded witness is square, with every entry
  exactly `+1` or `-1`; a `0`, a float, or a ragged row is rejected at ingestion;
- `gram_diagonal_equals_order` — every diagonal entry of `H @ H.T` equals `n`;
- `row_orthogonality` — every off-diagonal entry of `H @ H.T` is exactly `0`;
- `column_orthogonality` — an independent recomputation on the transpose
  confirms `H.T @ H == n * I`;
- `expected_rows_digest` — when a digest is supplied, the packed rows must hash
  to it.

Flipping one sign in an order-20 witness moves the largest off-diagonal Gram
entry from `0` to `2`, and the run emits no proofpack.

## Compressed representation

The packed form is the transport format *and* the exact representation: bit `j`
of row `i` is set exactly when `H[i][j] == -1`. Decoding is total and lossless,
so verification never depends on how the witness travelled. An order-668 witness
is 55,778 bytes of packed rows, or 111,556 hex characters — a compact string
that decodes to 446,224 exact signs.

Every run writes two files:

- `hadamard-<order>.witness.json` — the packed witness, re-verifiable on its own;
- `hadamard-<order>.proofpack.json` — the content-hashed certificate, carrying
  the gate results, the SHA-256 of the packed rows, and the claim boundary.

Rows are embedded inline in the proofpack for orders up to 64 and referenced by
hash above that, so the proofpack stays small while remaining bound to exactly
one matrix. The row digest is independent of the witness name and provenance:
the same matrix ingested from a file and rebuilt from a constructor produces the
same `rows_sha256`, and different `witness_digest` values that record where each
copy came from.

## Constructor coverage, honestly labelled

This repository implements Sylvester, Paley type I (prime `q = 3 mod 4`), Paley
type II (prime `q = 1 mod 4`), and Kronecker products of those. The survey lane
records which admissible orders that set covers:

```bash
foundry run hadamard-forge-0001-survey
```

Up to 2000 it covers 350 orders by construction, marks 6 more as reachable by
the Williamson search below, and leaves 146 that this repository cannot settle
at all, beginning `184, 188, 232, ...`.

Reachable means the enumeration fits the candidate budget — an invitation to run
the search, not a prediction of its outcome.

**An uncovered order is a gap in this repository, not a claim about the
literature.** Order 92 has been constructible since Baumert, Golomb and Hall
(1962) by methods this repository did not implement; before the search lane
existed it sat in the uncovered list, and it must not have been read as an open
problem. The survey states this in its own `claim_boundary` field so the JSON
cannot be quoted out of context.

## Searching instead of constructing

The constructor set only reproduces closed-form families, so everything it emits
is `REPRODUCED`. The Williamson lane earns the next label on the ladder: it is
handed the order and nothing else, and reports what it examined.

For odd `n`, four symmetric circulant `±1` matrices with

```text
A² + B² + C² + D² = 4n · I
```

assemble into a Hadamard matrix of order `4n`. Because the blocks are circulant
and symmetric, that identity reduces to an integer condition on the periodic
autocorrelations of their first rows — `R_a(s) + R_b(s) + R_c(s) + R_d(s) = 0`
for every shift — which is what the search actually solves.

```bash
foundry run hadamard-forge-0003-search-0052   # order 52
foundry run hadamard-forge-0003-search-0092   # order 92
```

The search enumerates symmetric rows with a leading `+1` (negating a row changes
neither `A²` nor its autocorrelation, so the other half of the space is
redundant), prunes by two necessary conditions, and meets in the middle:

| Stage | Order 92 (`n = 23`) |
| --- | --- |
| symmetric rows enumerated | 2,048 |
| surviving the density bound `PSD ≤ 4n` | 1,212 |
| admissible row-sum partitions | `{1,1,3,9}`, `{3,3,5,7}` |
| pair sums indexed | 64,009 |
| wall clock | under a second |

The row-sum partition is the sharp constraint. At frequency zero the density
identity reads `σa² + σb² + σc² + σd² = 4n` for the four row sums, and since row
sums of odd-length `±1` rows are odd, only a couple of magnitude multisets can
occur — each one fixing which groups a quadruple may draw from. Without it the
same search allocates tens of gigabytes; with it, order 116 lands in seconds.

**Neither prefilter is trusted.** They are necessary conditions used to prune, so
they can only discard candidates that cannot work. Whatever survives has its
autocorrelation identity re-checked in pure Python integers, and the assembled
matrix then goes through the same gates as any other witness. A search that
returned a bad quadruple would fail the Gram gate, not slip through.

### Three outcomes, three different meanings

| Outcome | What it certifies |
| --- | --- |
| `QUADRUPLE_FOUND` | exact existence of one Hadamard matrix of order `4n` |
| `FAMILY_EXHAUSTED_NO_QUADRUPLE` | the symmetric Williamson family is empty for that order — **not** that no Hadamard matrix of that order exists |
| `SEARCH_BUDGET_EXCEEDED` | nothing at all; part of the space was never examined |

The third is the one that matters for honesty. Order 140 (`n = 35`) needs a pair
index far past the configured budget, so the run stops and says so rather than
reporting an empty family — and an empty family would *still* not have been a
statement about order 140, which is constructible by other methods.

Of the eight orders below 200 that the constructor set misses, the search
settles four — 52, 92, 100, and 116 — each with a verified witness under
`results/hadamard-forge-0003/`. Orders 156 and 172 are reachable by enumeration
but stop on the pair budget (180,708 and 616,029 rows survive the density bound,
and indexing their pair sums would run to billions of keys), so they carry no
result. Orders 184 and 188 are outside the family entirely at this budget: `184 =
4·46` has even `n`, and `n = 47` needs 2²³ rows.

## Verifying an external witness

The uncovered orders — 668 among them — are reachable through the ingestion lane
without adding any trusted surface:

```bash
python scripts/run_hadamard_forge.py \
  --witness path/to/hadamard-0668.json \
  --expected-order 668 \
  --output-dir results/hadamard-forge-0002
```

Three transport forms are accepted, all decoded exactly: packed
`{"order": n, "rows_hex": [...]}`, explicit `{"signs": [[1, -1, ...], ...]}`, or
plain text with one `+`/`-` row per line. Supplying `--expected-rows-sha256`
binds the run to one specific matrix.

Until a witness file passes the gates, the lane emits nothing. `hadamard-forge-0002`
carries `status: awaiting_witness` and records no claim for order 668. That is
the intended resting state: an empty result is the correct output when no
witness exists locally.

Verification cost is dominated by the pairwise row products. An order-672
witness constructs and verifies in about 0.3 s total, so order 668 is not a
performance question — only a witness-availability question.

## Foundry Experience scene

The Experience page ships the order-168 witness in its packed form and
**re-verifies it in the browser**: the scene decodes the rows, recomputes all
14,028 row pairs as integers, and reports `max |off-diagonal| = 0` next to the
Python gate results. The page displays a matrix it has checked, not a picture of
one — `tests/test_experience_hadamard_scene.py` pins that the embedded rows
decode back to a witness that passes the same gates.

## Claim boundary

Verifying a witness of order `n` establishes the exact existence of one `n x n`
Hadamard matrix. It says nothing about the Hadamard conjecture, establishes no
equivalence-class or minimality statement, and records nothing at all about
orders for which no witness was verified. Reproducing a classical construction
is labelled `REPRODUCED` — the same label vocabulary as Counterexample Forge,
where `REDISCOVERED` and `DISCOVERED` require a search that was not handed its
answer.

## Formal artifact

[`formal/hadamard/gram_identity.v`](../formal/hadamard/gram_identity.v) is a
hole-free Coq file (checked with `coqc` 8.18; `Print Assumptions` reports
`Closed under the global context` for each theorem) proving, for finite `+-1`
vectors of equal length:

- `inner_eq_popcount_form` — the popcount form the verifier computes equals the
  sum-of-products definition;
- `inner_self_eq_length` — the diagonal case equals the length;
- `orthogonal_length_is_even` — two orthogonal rows force an even length.

It certifies the arithmetic the verifier executes and one elementary necessary
condition. The stronger classical statement — that an order `n >= 3` admitting a
Hadamard matrix satisfies `4 | n` — is not formalized here; the verifier applies
it as a declared gate rather than deriving it.

## Commands

```bash
foundry run hadamard-forge-smoke        # order 20, reduced CI gate
foundry run hadamard-forge-0001-verify  # order 168, full proofpack
foundry run hadamard-forge-0001-survey  # constructor coverage up to 2000
```
