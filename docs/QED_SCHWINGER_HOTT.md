# LoopForge, GaugeMatter, and Cohesive Gauge Foundations

This package adds three connected but deliberately separated scientific layers.

## `qed-loop-0001`

The QED benchmark evaluates finite Feynman-parameter integrals in Euclidean
momentum space. It provides:

- the renormalized spacelike vacuum-polarization scalar with `Pi_R(0)=0`;
- the explicitly transverse tensor `(Q² delta_mu_nu - q_mu q_nu) Pi_R(Q²)`;
- finite momentum-subtracted fermion dressing functions;
- the longitudinal Ball--Chiu vertex reconstructed from those dressings;
- a numerical Ward--Takahashi residual;
- the one-loop Pauli form factor and the `F2(0)=alpha/(2 pi)` benchmark;
- deterministic CSV, JSON, Markdown, and hash manifests.

The Ball--Chiu vertex is used because it exposes the gauge-symmetry contract
cleanly. It is not presented as the complete transverse one-loop vertex.

## `schwinger-matter-0001`

The Schwinger benchmark is a finite open-chain Hamiltonian system. Each site
holds a staggered fermion occupation and each link holds an integer electric
flux in `[-L_max, L_max]`. The local charge is normal ordered against the
staggered background:

```text
q_n = occupation_n - (1 - (-1)^n)/2
```

Physical basis states satisfy

```text
G_n = L_n - L_(n-1) - q_n = 0
```

including declared boundary fluxes. The implementation enumerates that sector
first and constructs the Hamiltonian only inside it. It reports:

- physical-sector dimension;
- maximum Gauss residual;
- transition leakage count;
- hard-wall clipping count;
- Hermiticity residual;
- exact finite spectrum and gap;
- ground-state charge density;
- electric-flux profile;
- staggered condensate;
- mass scan and deterministic bundle hashes.

The clipping count is diagnostic evidence about truncation pressure; it is not
silently discarded.

## `cohesive-gauge-0001`

The executable finite groupoid model treats configurations as objects, site
phases as gauge paths, path addition as composition, negation as inverse, and
an endpoint matter/Wilson-line correlator as a transported observable. The
certificate checks identity, inverse, associativity, and observable transport.

`formal/hott/GaugeCoherence.agda` is an interface scaffold. It is intentionally
not registered as a compiled theorem. A future proof-bearing layer must pin a
Cubical Agda toolchain and library version, encode the finite U(1) groupoid,
and prove the transport theorem rather than postulate it.

## Commands

```bash
foundry run qed-loop-0001
foundry run schwinger-matter-0001
foundry run cohesive-gauge-0001
foundry run qed-schwinger-hott
```

## Scientific boundary

These tracks join perturbative continuum calculations, finite Hamiltonian
matter dynamics, and gauge-coherence contracts. They do not establish
nonperturbative four-dimensional QED, continuum Yang--Mills existence, or a
positive Yang--Mills mass gap.
