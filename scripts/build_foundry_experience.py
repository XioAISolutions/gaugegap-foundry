#!/usr/bin/env python3
"""Build the offline Foundry Experience/Experiment interface from result artifacts."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.experience import build_experience  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "site" / "foundry-experience" / "index.html",
    )
    parser.add_argument("--title", default="GaugeGap Foundry")
    parser.add_argument("--strict", action="store_true", help="fail if no supported artifacts exist")
    args = parser.parse_args()

    manifest = build_experience(
        args.results_dir,
        args.output,
        title=args.title,
        strict=args.strict,
    )
    print(
        f"built {args.output} with {manifest['artifact_count']} artifacts "
        f"across {len(manifest['tracks'])} tracks; manifest={manifest['manifest_sha256']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
