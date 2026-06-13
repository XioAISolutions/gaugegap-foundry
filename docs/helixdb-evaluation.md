# HelixDB evaluation for gaugegap-foundry

An honest fit analysis of [HelixDB](https://github.com/helixdb/helix-db) for this
project. **No dependency is added by this document** — it is a decision artifact.

**Verdict up front:** HelixDB is a capable graph-vector database, but it is **not
a fit for the reproducible core** of this repo. It is worth considering only as an
**optional, out-of-core knowledge/demo layer** over candidate operators, certified
results, and the cited literature — and only if we actually want semantic search /
a queryable knowledge graph. For provenance and results storage, the current
file-based approach is better *for this project's goals*.

## What HelixDB is

- Graph **and** vector database (also KV/document/relational), written in Rust,
  Apache-2.0, actively developed (v3.0.5, June 2026).
- Aimed at **AI memory / RAG / knowledge graphs**; queries via Rust/TypeScript
  DSLs compiled to a JSON AST; runs as a **service** via the `helix` CLI.
- Official Python client **`helix-py`** (`pip install helix-py`): client
  interface, vector similarity search, embedders (OpenAI/Gemini/Voyage), LLM
  integration, data loaders (CSV/parquet/fvecs), and a ready-made **MCP server**
  exposing graph traversal + search as tools.

## How this repo stores things today

- **Results**: per-run bundles under `results/` (JSON/CSV/SVG) — e.g.
  `curverank-formal/`, `curverank-ibm/`, `curverank-hardware/`.
- **Provenance**: append-only **JSONL ledgers** (`src/gaugegap/ledger.py`).
- **Determinism is a hard design constraint**: `ledger.py` honors
  `SOURCE_DATE_EPOCH` so proofpacks and certificates regenerate **byte-for-byte
  identically**; `scripts/verify_proofpack.py` checks content hashes; the
  claim-boundary audit gates every doc. The whole pipeline is **stateless and
  file-based** by design.

This last point is the crux: the repo's value proposition is *verification-first
reproducibility*. A stateful external database is in direct tension with that.

## Where HelixDB could genuinely add value

Not provenance — that is already solved. The real opportunity is a **knowledge
graph + semantic search** layer that the file approach does *not* offer:

- A queryable map of the field: candidate **operators** → their **certified
  results** → **provenance** → the ~30 **cited papers** from
  `docs/riemann-operator-landscape.md`.
- **Vector search** over paper abstracts / result descriptions: "find operators
  related to Rindler," "results with certified separation > 30," "papers near
  this construction."
- An **MCP server** (helix-py ships one) exposing that graph to an agent — a
  genuinely demoable artifact with portfolio/credibility value.

### Sketch schema (if adopted)

Nodes
- `Operator` {family, name, source_ref} — xp, dirac_rindler, quantum_graph, …
- `CertifiedResult` {n_basis, k_zeros, M_lower, M_upper, threshold, separated}
- `Paper` {arxiv_id, title, year, status_label}  ← from the landscape doc
- `QPERun` {backend, n_qubits, depth, target, estimate, abs_error}

Edges
- `(Operator)-[:HAS_RESULT]->(CertifiedResult)`
- `(Operator)-[:STUDIED_IN]->(Paper)`
- `(CertifiedResult)-[:COMPARED_TO]->(Paper)`  (e.g. our negative result vs a claim)
- `(Operator)-[:BENCHMARKED_BY]->(QPERun)`

Vectors
- Embedding on `Paper.abstract` and `CertifiedResult.description` for similarity.

Loading would be a one-way **export** from the existing JSONL ledgers / results
bundles into HelixDB — the files stay the source of truth; the DB is a derived
index.

## Tradeoffs vs. the current approach

| Dimension | File-based (today) | + HelixDB layer |
|---|---|---|
| Reproducibility | Byte-identical (`SOURCE_DATE_EPOCH`, hashes) | DB state is **not** deterministic; must stay out of the proofpack path |
| Operational weight | None (pure Python, files) | Runs a Rust DB **service**; new infra to start/manage |
| Stack fit | Python throughout | Core DSL is Rust/TS; Python via `helix-py` (fine, but extra dep) |
| Data scale | Dozens of results — trivial | DB is overkill at this scale; pays off only with a large corpus |
| New capability | None for search | **Graph queries + vector/semantic search + MCP** (the actual win) |
| CI | Fast, hermetic | Would need a DB service or be excluded from CI (keep it optional) |

## Recommendation

1. **Do not** put HelixDB in the reproducible core (provenance/results stay
   file-based; this protects the proofpack/hash/determinism guarantees).
2. **Defer** adoption until there is a concrete need for semantic search or a
   queryable knowledge graph (e.g. the literature corpus grows, or we want an
   agent/MCP demo for funding conversations).
3. **If/when** we do it, build it as a **separate, optional module** behind an
   extra dependency (`helix-py`), that *exports* the existing ledgers/results into
   the schema above and exposes read-only graph/vector queries — never on the
   determinism-critical path, and excluded from (or mocked in) CI.

### Concrete "worth it" triggers
- We accumulate a real literature corpus (hundreds of papers/operators) worth searching.
- We want an **MCP-server demo** ("ask the knowledge graph about RH operator candidates and our certified results") as a portfolio/funding asset.
- A collaborator wants ad-hoc graph queries over results that JSONL + Python can't serve ergonomically.

Until one of those is true, the honest call is: **good tool, not needed yet.**

## Sources
- HelixDB: https://github.com/helixdb/helix-db
- helix-py (Python client + MCP server): https://github.com/helixdb/helix-py
