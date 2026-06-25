from __future__ import annotations

import csv
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from check_curverank_reproduction import mismatch_values


def _write(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_reads_current_ledger_style_rows(tmp_path):
    path = tmp_path / "screen.csv"
    _write(
        path,
        ["observable", "value"],
        [
            {"observable": "spectral_mismatch", "value": "28.5"},
            {"observable": "other", "value": "1.0"},
        ],
    )
    assert mismatch_values(path) == [28.5]


def test_reads_legacy_mismatch_column(tmp_path):
    path = tmp_path / "screen.csv"
    _write(path, ["mismatch"], [{"mismatch": "27.25"}])
    assert mismatch_values(path) == [27.25]
