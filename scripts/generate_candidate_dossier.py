#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.search.candidate_dossier import write_candidate_dossiers, write_markdown_summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate dossiers from gaugegap-0003 candidate output.")
    parser.add_argument("input", type=Path, help="Candidate JSON array or JSONL file")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "gaugegap-0003-dossiers")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    candidates = load_candidates(args.input)
    candidates.sort(key=lambda item: float(item.get("score", 0.0)), reverse=True)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_markdown_summary(args.output_dir / "candidate-ranking.md", candidates)
    paths = write_candidate_dossiers(args.output_dir, candidates, limit=args.limit)
    print(json.dumps({"status": "pass", "candidate_count": len(candidates), "files": [str(path) for path in paths]}, indent=2))
    return 0


def load_candidates(path: Path) -> list[dict[str, object]]:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    if text.startswith("["):
        payload = json.loads(text)
        if not isinstance(payload, list):
            raise ValueError("candidate JSON must be a list")
        return [item for item in payload if isinstance(item, dict)]
    candidates: list[dict[str, object]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            candidates.append(payload)
    return candidates


if __name__ == "__main__":
    raise SystemExit(main())
