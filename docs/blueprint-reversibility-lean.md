# Blueprint: logical reversibility, and what Landauer's bound is applied to

Formalisation target for the `landauer-reversibility` track of `formal/lean`.

## Why this track exists, and what it refuses to claim

Landauer's principle says that erasing information dissipates at least
`k_B T ln 2` per bit. `src/gaugegap/quantum/landauer.py` already computes that
bound. What it takes as given is the *entropy* — how much information a given
operation actually destroys — and that is not a thermodynamic question at all.
It is a counting question about a finite function, and it can be settled exactly.

This track settles it for the three gates the argument is usually told with, and
then stops. Specifically, it does **not** claim any of the following, all of
which have been proposed as extensions and none of which follow:

- **"Gauge invariance is information preservation."** Gauge invariance is a
  redundancy of description; a gauge orbit is one physical state written many
  ways. Quotienting by it destroys no information because there was none there.
  That is not the same statement as unitarity, and calling them the same is a
  pun on "preserves".
- **"The mass gap is a Landauer gap."** A spectral gap of a Hamiltonian and a
  thermodynamic cost per erased bit share the word "gap" and nothing else. They
  do not have the same units.
- **"Truncating a lattice Hilbert space erases information, so it costs
  `k_B T ln 2` per mode."** A truncation is an approximation *in a model*. No
  physical degree of freedom is reset when a simulation drops a basis element.
  There is no heat.

The claim boundary for the whole track is therefore narrow and stated in every
file: exact combinatorics and integer linear algebra for named finite Boolean
functions, plus the Shannon entropy those counts determine. The physics stays in
`gaugegap.quantum.landauer`, where it already was.

## The mathematics

`AND` is irreversible because it is not injective: `(false, false)`,
`(false, true)` and `(true, false)` all map to `false`. Reversibility is not a
property one can add to `AND` — the map itself has no inverse — so Bennett's
construction changes the map. `Toffoli` takes three bits to three bits, keeps the
first two, and XORs the third with their conjunction:

```
toffoli (a, b, c) = (a, b, c ⊕ (a ∧ b))
```

Setting `c = false` makes the third output `a ∧ b`, so `Toffoli` computes `AND`;
and it is an involution, so it is a bijection and destroys nothing. Both facts
hold, and the second one is not free. The reason `Toffoli` is reversible is
visible in its own definition: it *carries its inputs forward*. `E06` states
that as a node rather than leaving it as commentary, because it is the whole
economics of reversible computing. Reversible computation does not avoid the
cost of erasure. It defers it to whenever those retained bits are cleared.

## The entropy, exactly

With uniform inputs, `AND` has output distribution `(3/4, 1/4)`. It is a
function, so `H(X, Y) = H(X) = 2` bits exactly, and the chain rule gives

```
H(X | Y) = H(X) - H(Y) = 2 - (2 - (3/4) log₂ 3) = (3/4) log₂ 3
```

which is about `1.1887218755408671` bits. That number is irrational, so any
assertion that it *equals* `1.1887` is false — by about `2.2e-5` bits. It is also
not `0.5`; averaging the two fibres by hand gives that, and it is the wrong
average.

`src/gaugegap/reversibility_theorem.py` therefore does not store entropies as
floats. It stores them as exact rational combinations of `log₂ p` over primes:
`{3: 3/4}` is `(3/4) log₂ 3`. Keying on primes puts the representation in
canonical form — `log₂ 4` reduces to `2 log₂ 2` — and because the logarithms of
distinct primes are rationally independent, two entropies are equal exactly when
their combinations are. `==` is then a real test rather than a tolerance. The
single `math.log2` call in the module is confined to `combo_to_float`, and the
Landauer floor itself is delegated to `landauer_bound`, not reimplemented.

## The permutation matrices

Reversibility is often certified by exhibiting a matrix `P` with `Pᵀ P = I`. A
theorem of the form "for any `P` with `Pᵀ P = I`, `Pᵀ P = I`" is true, vacuous,
and says nothing about `Toffoli`. `permutation_matrix` instead *builds* the 8×8
matrix of the specific gate — `P[i][j] = 1` exactly when the gate sends basis
state `j` to `i` — raising if the gate turns out not to be a permutation, so the
construction is itself part of the check. `Pᵀ P = I` is then verified over the
integers, with no tolerance anywhere, and `tests/test_reversibility_theorem.py`
checks that the matrix reproduces the gate, that it is not the identity, that
the orthogonality test can fail on a matrix that is not orthogonal, and that a
non-injective gate has no such matrix at all.

## Node table

| Node | Statement | Depends on |
|---|---|---|
| E01 | `Stmt_E01_AndNotInjective` | — |
| E02 | `Stmt_E02_AndFibreSizes` | — |
| E03 | `Stmt_E03_ToffoliInvolutive` | — |
| E04 | `Stmt_E04_ToffoliBijective` | E03 |
| E05 | `Stmt_E05_ToffoliComputesAnd` | — |
| E06 | `Stmt_E06_ReversibilityKeepsTheInputs` | — |
| E07 | `Stmt_E07_FredkinInvolutive` | — |

`E02` counts fibres inside an explicitly listed `inputs2`, and its first
conjunct is that the list misses no input — otherwise the counts would be counts
over a sample. Every gate is written as a pattern match on `Bool`, so the ground
goals close by `rfl` after splitting on the input bits; the only decision
procedure used is for two disequalities. No `sorry`, no `axiom`, no
`native_decide`.

## The mirror

`src/gaugegap/reversibility_theorem.py` restates all seven nodes and checks them
by exhaustion over the whole domain — four inputs for `AND`, eight for `Toffoli`
and `Fredkin`. That is not a sample, and the test suite asserts the enumeration
sizes so it cannot silently become one.

## What this does not do

It does not prove Landauer's principle; that is physics, and it is cited, not
derived. It does not compute a heat for any real device. It says which finite
functions destroy information, exactly how much, and what carrying the inputs
forward buys — and it leaves the thermodynamic step to the module that already
had it.
