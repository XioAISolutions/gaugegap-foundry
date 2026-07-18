#!/usr/bin/env python3
"""Fail closed when the Fractal Reality Lab release surface is incomplete."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_SITE_MARKERS = {
    "index.html": (
        "Fractal Reality Lab",
        "mandelbrotCanvas",
        "juliaCanvas",
        "brainCanvas",
        "analogueSelect",
    ),
    "app.js": (
        "orbitFor",
        "extractFeatures",
        "renderEscape",
        "drawBrain",
        "sonifyOrbit",
    ),
    "styles.css": (
        ":root",
        ".instrument-grid",
        ".evidence-grid",
    ),
}


def _require_text_markers(path: Path, markers: tuple[str, ...]) -> None:
    if not path.is_file() or path.stat().st_size == 0:
        raise SystemExit(f"missing or empty release file: {path}")
    text = path.read_text(encoding="utf-8")
    missing = [marker for marker in markers if marker not in text]
    if missing:
        raise SystemExit(f"{path} is missing release markers: {', '.join(missing)}")


def _read_json(path: Path) -> dict[str, object]:
    if not path.is_file() or path.stat().st_size == 0:
        raise SystemExit(f"missing or empty generated artifact: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"expected JSON object in {path}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-dir", type=Path, default=Path("site/fractal-reality-lab"))
    parser.add_argument("--artifact-dir", type=Path, default=Path("/tmp/fractal-reality-smoke"))
    args = parser.parse_args()

    for name, markers in REQUIRED_SITE_MARKERS.items():
        _require_text_markers(args.site_dir / name, markers)

    manifest = _read_json(args.artifact_dir / "manifest.json")
    featured = _read_json(args.artifact_dir / "featured-experiment.json")

    if manifest.get("schema") != "gaugegap.fractal_reality.v1":
        raise SystemExit("unexpected Fractal Reality manifest schema")
    if not manifest.get("content_sha256"):
        raise SystemExit("Fractal Reality manifest is missing its content hash")
    if not manifest.get("experiments") or not manifest.get("analogues"):
        raise SystemExit("Fractal Reality manifest must contain experiments and analogues")

    if featured.get("schema") != "gaugegap.fractal_reality.compact.v1":
        raise SystemExit("unexpected featured-experiment schema")
    if featured.get("manifest_sha256") != manifest.get("content_sha256"):
        raise SystemExit("featured experiment is not tied to the generated manifest hash")
    if not featured.get("brainsnn") or not featured.get("comparisons"):
        raise SystemExit("featured experiment must include BrainSNN encoding and comparisons")

    print(
        json.dumps(
            {
                "site": str(args.site_dir),
                "artifact_dir": str(args.artifact_dir),
                "schema": manifest["schema"],
                "sha256": manifest["content_sha256"],
                "status": "release-ready",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
