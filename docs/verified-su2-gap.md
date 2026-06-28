# Verified finite SU(2) gap benchmark

This benchmark is the first GaugeGap result designed around a fully controlled chain:

```text
gauge-invariant basis
→ exact Hamiltonian construction
→ independent reconstruction from SU(2) fusion
→ floating-point diagonalization
→ exact-rational Sturm eigenvalue enclosures
→ positive finite gap certificate
→ sweep artifacts and visual report
```

## Model

The system is a single SU(2) plaquette reduced to the gauge-invariant class-function basis

```text
|j> = chi_j,   j = 0, 1/2, 1, ... , j_max.
```

Haar orthogonality makes the characters orthonormal. The electric term is diagonal,

```text
H_E |j> = electric · j(j+1) |j>,
```

and multiplication by the fundamental Wilson character uses the exact representation-ring identity

```text
chi_(1/2) chi_j = chi_(j+1/2) + chi_(j-1/2).
```

With a finite cutoff this gives a real symmetric tridiagonal matrix. The boundary at `j_max` is the explicit representation truncation.

## Exact known answer

For

```text
j_max = 1/2
electric = 1
magnetic = 1/2
```

the matrix is

```text
[ 0    -1/2 ]
[ -1/2  3/4 ]
```

with exact energies

```text
E0 = -1/4
E1 = 1
gap = 5/4.
```

The known-answer case is stored in `benchmarks/su2_one_plaquette_known_answers.json` and tested in `tests/test_verified_su2_gap.py`.

## Certification method

The code constructs the matrix twice:

1. directly as a tridiagonal finite Hamiltonian;
2. independently from the SU(2) fundamental fusion rule.

The two exact rational matrices must agree entry by entry. Their floating-point spectra must also agree.

For the final bound, the code does not trust the floating-point eigenvalues. It uses the Sturm sequence of the rational symmetric tridiagonal matrix to count eigenvalues below a rational trial point. Exact bisection isolates the first two ordered eigenvalues:

```text
E0 ∈ [E0_lower, E0_upper]
E1 ∈ [E1_lower, E1_upper]
```

and therefore

```text
gap ∈ [E1_lower - E0_upper, E1_upper - E0_lower].
```

A positive lower endpoint is the finite certified statement.

## Run

```bash
foundry run su2-gap-known-answer
foundry run su2-gap-certified
foundry run su2-gap-sweep
foundry run gap-forge

# all registered gap tasks
foundry run verified-su2-gap
```

Direct command:

```bash
python scripts/run_verified_su2_gap.py \
  --max-two-j 4 \
  --electric 1 \
  --magnetic 1/2 \
  --sturm-bits 112 \
  --require-positive \
  --output-dir results/verified-su2-gap/custom
```

## Artifacts

Each run emits:

```text
verified_gap.json   exact intervals, independent paths, digest, and boundary
gap_sweep.csv       cutoff/coupling sweep with certified lower and upper bounds
gap_forge.svg       visual comparison of certified lower bounds
report.md           human-readable finite-result summary
```

## Formal finite theorem

`proofs/su2_finite_gap/VerifiedSU2Gap.v` verifies the exact analytic `2 × 2` case in Coq:

- `-1/4` is a characteristic root;
- `1` is a characteristic root;
- their separation is exactly `5/4`;
- that separation is strictly positive.

The same source is emitted through `gaugegap.verified_su2_proof` for the repository's compiled-certificate lane.

## What this establishes

For the declared finite character basis, cutoff, and rational couplings, the benchmark establishes:

- gauge invariance of the chosen basis by construction;
- exact agreement of two Hamiltonian constructions;
- exact rational eigenvalue enclosures;
- a strictly positive first finite spectral gap;
- reproducible cutoff and coupling sweeps.

## Claim boundary

This is a one-plaquette finite SU(2) class-function truncation. It does not establish a thermodynamic limit, a continuum limit, existence of four-dimensional continuum Yang-Mills theory, or the Yang-Mills Millennium Prize mass gap. The purpose is to create a rigorous benchmark that later lattice models must reproduce and extend without weakening the evidence chain.
