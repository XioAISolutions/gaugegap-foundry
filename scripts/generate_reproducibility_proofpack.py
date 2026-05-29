#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
CLAIM_BOUNDARY = "Finite-system benchmark proofpack only; no Millennium Prize problem solution claim."

DEFAULT_COMMANDS = [
    [sys.executable, "scripts/claim_boundary_audit.py", "--output-dir", "{output_dir}/claim-boundary-audit"],
    [sys.executable, "scripts/run_gap_sweep.py", "--sizes", "4", "--field-points", "2", "--output-dir", "{output_dir}/gaugegap-0001"],
    [sys.executable, "scripts/run_z2_plaquette.py", "--output-dir", "{output_dir}/gaugegap-0002-exact"],
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a reproducibility proofpack manifest for local finite benchmarks.")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "proofpack")
    parser.add_argument("--strict-claims", action="store_true", help="Run claim-boundary audit in strict mode")
    parser.add_argument("--skip-commands", action="store_true", help="Only hash existing outputs and write manifest")
    parser.add_argument("--command", action="append", default=None, help="Extra command to run; repeatable; simple whitespace splitting only")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    commands = _commands(args)
    run_records: list[dict[str, object]] = []
    if not args.skip_commands:
        for command in commands:
            run_records.append(_run_command(command, args.output_dir))

    files = list(_collect_files(args.output_dir))
    manifest = {
        "schema": "gaugegap.reproducibility_proofpack.v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": CLAIM_BOUNDARY,
        "repo": _git("rev-parse", "--show-toplevel"),
        "git": {
            "commit": _git("rev-parse", "HEAD"),
            "dirty": bool(_git("status", "--porcelain")),
        },
        "python": sys.version,
        "commands": run_records,
        "files": [_file_record(path, args.output_dir) for path in files],
    }
    manifest_path = args.output_dir / "proofpack_manifest.json"
    summary_path = args.output_dir / "PROOFPACK.md"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    summary_path.write_text(_markdown(manifest), encoding="utf-8")

    failed = [item for item in run_records if item["returncode"] != 0]
    print(json.dumps({"status": "fail" if failed else "pass", "failed_commands": len(failed), "files": len(files), "output_dir": str(args.output_dir)}, indent=2))
    return 1 if failed else 0


def _commands(args: argparse.Namespace) -> list[list[str]]:
    commands = [[part.format(output_dir=str(args.output_dir)) for part in command] for command in DEFAULT_COMMANDS]
    if args.strict_claims:
        commands[0].append("--strict")
    if args.command:
        commands.extend(_split_command(item.format(output_dir=str(args.output_dir))) for item in args.command)
    return commands


def _run_command(command: list[str], output_dir: Path) -> dict[str, object]:
    started = datetime.now(timezone.utc)
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    ended = datetime.now(timezone.utc)
    command_hash = hashlib.sha256("\0".join(command).encode("utf-8")).hexdigest()
    command_dir = output_dir / "commands"
    command_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = command_dir / f"{command_hash}.stdout.txt"
    stderr_path = command_dir / f"{command_hash}.stderr.txt"
    stdout_path.write_text(proc.stdout, encoding="utf-8")
    stderr_path.write_text(proc.stderr, encoding="utf-8")
    return {
        "command": command,
        "returncode": proc.returncode,
        "started_at_utc": started.isoformat(),
        "ended_at_utc": ended.isoformat(),
        "stdout_path": str(stdout_path.relative_to(output_dir)),
        "stderr_path": str(stderr_path.relative_to(output_dir)),
        "stdout_sha256": hashlib.sha256(proc.stdout.encode("utf-8")).hexdigest(),
        "stderr_sha256": hashlib.sha256(proc.stderr.encode("utf-8")).hexdigest(),
    }


def _collect_files(output_dir: Path) -> Iterable[Path]:
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name not in {"proofpack_manifest.json", "PROOFPACK.md"}:
            yield path


def _file_record(path: Path, base: Path) -> dict[str, object]:
    payload = path.read_bytes()
    return {"path": str(path.relative_to(base)), "bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}


def _markdown(manifest: dict[str, object]) -> str:
    lines = [
        "# Reproducibility Proofpack",
        "",
        f"> {manifest['claim_boundary']}",
        "",
        f"Created: `{manifest['created_at_utc']}`",
        f"Git commit: `{manifest['git']['commit']}`",
        f"Dirty tree: `{manifest['git']['dirty']}`",
        "",
        "## Commands",
        "",
        "| status | command | stdout | stderr |",
        "|---|---|---|---|",
    ]
    for item in manifest.get("commands", []):
        assert isinstance(item, dict)
        status = "PASS" if item.get("returncode") == 0 else "FAIL"
        command = " ".join(str(part) for part in item.get("command", []))
        lines.append(f"| {status} | `{command}` | `{item.get('stdout_path')}` | `{item.get('stderr_path')}` |")
    lines.extend(["", "## Files", "", "| path | bytes | sha256 |", "|---|---:|---|"])
    for item in manifest.get("files", []):
        assert isinstance(item, dict)
        lines.append(f"| `{item['path']}` | {item['bytes']} | `{item['sha256']}` |")
    lines.append("")
    return "\n".join(lines)


def _git(*args: str) -> str | None:
    proc = subprocess.run(["git", "-C", str(ROOT), *args], text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def _split_command(command: str) -> list[str]:
    return command.split()


if __name__ == "__main__":
    raise SystemExit(main())
