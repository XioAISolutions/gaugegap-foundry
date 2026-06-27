# Search Forge

Search Forge adds deterministic finite-graph search to GaugeGap Foundry. It supports exact Dijkstra search, A* with a declared heuristic contract, finite scientific search spaces, and a controlled symbolic-pattern laboratory.

## Generate the bundle

```bash
foundry run search-forge
```

Focused symbolic alias:

```bash
foundry run symbolic-search-lab
```

Direct invocation:

```bash
python scripts/run_search_forge.py \
  --output-dir site/search-forge \
  --preview figures/search-forge/search-forge.svg
```

Open `site/search-forge/index.html`.

## What ships

- Dijkstra for finite graphs with non-negative edge costs;
- A* with declared admissibility and a consistency check over every edge;
- deterministic certificates containing the path, cost, expansion order, graph hash, and result hash;
- exact rational hypercharge repair tied to Anomaly Forge;
- a research-maturity route from idea to reviewer packet;
- Hebrew standard and English ordinal cipher examples;
- deterministic null controls showing how easily target matches can appear;
- an offline HTML interface and SVG preview.

## Scientific boundaries

Dijkstra certifies the minimum only on the declared finite graph. A* carries that claim only when its heuristic contract is valid. A finite search space does not establish uniqueness across all physical models or proof strategies.

The symbolic layer records numerical associations only. Equal values do not establish causality, prediction, historical intent, or a physical mechanism. Null controls are included to expose post-hoc target selection and multiple comparisons.

## Tests

```bash
python -m pytest -q tests/test_search_forge.py
```

The suite covers known shortest paths, negative-edge rejection, A*/Dijkstra agreement, heuristic consistency, anomaly repair, research-path selection, exact historical examples, deterministic null controls, and complete offline generation.
