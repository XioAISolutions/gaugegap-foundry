from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
from typing import Iterable


def utc_now() -> datetime:
    """Current UTC time, honoring SOURCE_DATE_EPOCH for reproducible builds.

    When the ``SOURCE_DATE_EPOCH`` environment variable is set (the
    reproducible-builds standard), it is used as a fixed wall-clock so that
    proofpacks and certificates regenerate byte-for-byte identically. Otherwise
    the real current time is used.
    """
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch:
        try:
            return datetime.fromtimestamp(int(epoch), tz=timezone.utc)
        except (ValueError, OverflowError, OSError):
            pass
    return datetime.now(timezone.utc)


def utc_run_id() -> str:
    return utc_now().strftime("%Y%m%dT%H%M%SZ")


def object_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def git_state(path: Path) -> dict[str, object]:
    return {
        "commit": _git(path, "rev-parse", "HEAD"),
        "dirty": bool(_git(path, "status", "--porcelain")),
    }


def write_jsonl(path: Path, records: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")))
            handle.write("\n")


def _git(path: Path, *args: str) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(path), *args],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    output = proc.stdout.strip()
    return output or None
