# gaugegap-0003: Finite Spectral-Gap Candidate Search

`gaugegap-0003` turns the finite Z2 plaquette benchmark into a small candidate-mining loop.

Boundary: **Finite Z2 lattice gauge toy benchmark only; no continuum Yang-Mills mass-gap claim.**

## Purpose

The goal is to search finite Z2 plaquette families for gap profiles that are worth deeper validation. A candidate is not a theorem. It is a reproducible finite-system artifact that survives the current checks:

1. exact dense diagonalization;
2. Pauli dense replica agreement;
3. low residual norms;
4. perturbation checks over transverse field;
5. finite-size checks across plaquette counts;
6. explicit claim-boundary preservation.

## Search space

The default search evaluates:

```text
n_plaquettes = 1,2,3
plaquette_coupling J = 0.5,1.0,1.5
transverse_field h = linspace(0.05,2.0,6)
```

Each fixed `J` becomes one candidate family evaluated over the finite sizes and fields. Optional seeded random local perturbations can be added with `--random-samples`.

## Scoring

The candidate score rewards:

- larger mean finite gaps;
- larger minimum finite gap;
- stable behavior under nearby `h` perturbations;
- survival as finite size increases;
- clean Pauli/dense agreement;
- low exact-diagonalization residuals.

It penalizes:

- gap collapse with size;
- high variance over perturbations;
- Pauli replica mismatch;
- high residuals;
- unnecessary parameter complexity;
- missing claim-boundary language.

## Run

```bash
python scripts/search_gap_candidates.py --output-dir /tmp/gaugegap-0003 --max-candidates 10
```

A small smoke run:

```bash
python scripts/search_gap_candidates.py \
  --output-dir /tmp/gaugegap-0003-smoke \
  --n-plaquettes 1 \
  --plaquette-couplings 1.0 \
  --field-points 2 \
  --max-candidates 1
```

## Outputs

The search writes:

- `gaugegap-0003-candidates.jsonl`
- `gaugegap-0003-candidates.json`
- `gaugegap-0003-ranking.csv`
- `gaugegap-0003-ranking.md`
- `dossiers/*.json`
- `dossiers/*.md`

## Dossiers

Each dossier includes:

- candidate id;
- finite model details;
- parameter grid;
- gap profile;
- exact residuals;
- Pauli replica status;
- score components;
- why the candidate is interesting;
- why it is not a Yang-Mills proof;
- next validation step.

## Next step

`gaugegap-0004` should take the top finite candidates and run them through:

1. noiseless statevector simulation;
2. shot-based Aer simulation;
3. noisy Aer simulation;
4. hardware-readiness reporting;
5. optional tiny IBM Runtime execution only after local checks pass.
