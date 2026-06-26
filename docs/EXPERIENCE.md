# Foundry Experience / Experiment

GaugeGap Foundry now exposes one deterministic, offline interface over its result artifacts.
The interface uses two complementary modes over the **same evidence manifest**:

- **Experience** — an auto-sequenced, full-screen presentation of figures, formal files,
  tables, JSON summaries, hashes, and claim boundaries.
- **Experiment** — a searchable workbench for inspecting the exact source artifacts behind
  each scene.

The conceptual reference is the distinction between “experience” and “experiment” in
Ryoji Ikeda's *supersymmetry* project. The Foundry implementation is original: it does not
copy the installation, its media, or its code. It translates the useful systems idea into a
verification-first scientific interface.

## Build

```bash
foundry run foundry-experience
```

or directly:

```bash
python scripts/build_foundry_experience.py \
  --results-dir results \
  --output results/foundry-experience/index.html
```

Open `results/foundry-experience/index.html` in a browser. It is self-contained and does
not require a server, external JavaScript, fonts, analytics, or network access.

Use `--strict` when building a release artifact. Strict mode fails when no supported result
artifacts exist:

```bash
python scripts/build_foundry_experience.py --strict
```

## Controls

| Key / control | Action |
|---|---|
| `E` | Switch to Experience mode |
| `X` | Switch to Experiment mode |
| `Space` | Pause or resume the sequence |
| `←` / `→` | Move between evidence scenes |
| Search field | Filter by path, track, or artifact kind |

## Evidence contract

The renderer is downstream of scientific execution. It does not recompute spectra,
trajectories, gaps, certificates, or proofs. It only scans supported textual artifacts under
`results/`, computes SHA-256 digests, extracts explicit claim-boundary language where
available, and embeds previews in a deterministic manifest.

Supported artifacts include:

- JSON, JSONL, YAML, and CSV data;
- SVG figures;
- Lean, Coq, and Isabelle sources;
- Markdown and plain-text reports.

Every scene exposes:

1. repository-relative result path;
2. inferred track and artifact kind;
3. byte size;
4. SHA-256 digest;
5. explicit claim boundary, or a conservative fallback statement.

The generated companion file `index.manifest.json` is the canonical machine-readable input
to the interface. Its `manifest_sha256` is computed before that field is added, so identical
result trees produce byte-identical manifests and HTML.

## Design rules

1. **One evidence source, two modes.** Presentation and inspection never drift.
2. **No spectacle without provenance.** Every visual scene carries its hash and claim boundary.
3. **Offline by construction.** The output cannot silently depend on a CDN or third-party API.
4. **Finite means finite.** Numerical visualizations do not become proofs by being immersive.
5. **Formal means exact scope.** Proof files are shown beside, not above, their stated theorem.

## Extension points

Add new artifact support in `src/gaugegap/experience.py` by extending `TEXT_EXTENSIONS` and
`_kind`. Keep preview parsing deterministic and bounded. Binary media should be represented by
small, reproducible derivatives plus a hash of the original rather than embedded unbounded data.

The next planned interface layer is a scene manifest that lets each scientific track declare
preferred ordering, captions, and comparisons while retaining the same global evidence
contract.
