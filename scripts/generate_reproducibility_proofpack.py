#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
CLAIM_BOUNDARY = "Finite-system benchmark proofpack only; no Millennium Prize problem solution claim."


def _utc_now() -> datetime:
    """UTC now, honoring SOURCE_DATE_EPOCH so proofpacks are reproducible."""
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch:
        try:
            return datetime.fromtimestamp(int(epoch), tz=timezone.utc)
        except (ValueError, OverflowError, OSError):
            pass
    return datetime.now(timezone.utc)

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
    parser.add_argument("--include-search", action="store_true", help="Include gaugegap-search-0001 candidate-search smoke")
    parser.add_argument("--include-validation", action="store_true", help="Include gaugegap-0004 hardware-readiness smoke")
    parser.add_argument("--include-qiskit", action="store_true", help="Include optional Qiskit/Aer/QPY validation smoke")
    parser.add_argument("--allow-qiskit-skip", action="store_true", help="Allow --include-qiskit to write a skipped report when Qiskit is missing")
    parser.add_argument("--command", action="append", default=None, help="Extra command to run; repeatable; simple whitespace splitting only")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.include_qiskit and not _module_available("qiskit") and not args.allow_qiskit_skip:
        print(json.dumps({"status": "fail", "reason": "Qiskit is not installed; use --allow-qiskit-skip to record a skipped optional validation"}, indent=2))
        return 2
    commands = _commands(args)
    run_records: list[dict[str, object]] = []
    if not args.skip_commands:
        for command in commands:
            run_records.append(_run_command(command, args.output_dir))

    files = list(_collect_files(args.output_dir))
    file_records = [_file_record(path, args.output_dir) for path in files]
    manifest = {
        "schema": "gaugegap.reproducibility_proofpack.v1",
        "created_at_utc": _utc_now().isoformat(),
        "claim_boundary": CLAIM_BOUNDARY,
        "repo": _git("rev-parse", "--show-toplevel"),
        "git": {
            "commit": _git("rev-parse", "HEAD"),
            "dirty": bool(_git("status", "--porcelain")),
        },
        "python": sys.version,
        "dependencies": _dependency_versions(),
        "commands": run_records,
        "files": file_records,
        "reproducible_digest": _reproducible_digest(file_records),
    }
    manifest_path = args.output_dir / "proofpack_manifest.json"
    summary_path = args.output_dir / "PROOFPACK.md"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    summary_path.write_text(_markdown(manifest), encoding="utf-8")

    failed = [item for item in run_records if item["returncode"] != 0]
    print(json.dumps({
        "status": "fail" if failed else "pass",
        "failed_commands": len(failed),
        "files": len(files),
        "reproducible_digest": manifest["reproducible_digest"],
        "output_dir": str(args.output_dir),
    }, indent=2))
    return 1 if failed else 0


def _commands(args: argparse.Namespace) -> list[list[str]]:
    commands = [[part.format(output_dir=str(args.output_dir)) for part in command] for command in DEFAULT_COMMANDS]
    if args.strict_claims:
        commands[0].append("--strict")
    if args.include_search:
        commands.append(
            [
                sys.executable,
                "scripts/search_gap_candidates.py",
                "--output-dir",
                "{output_dir}/gaugegap-search-0001",
                "--n-plaquettes",
                "1",
                "--plaquette-couplings",
                "1.0",
                "--field-points",
                "2",
                "--max-candidates",
                "1",
            ]
        )
    if args.include_validation:
        commands.append(
            [
                sys.executable,
                "scripts/run_candidate_validation.py",
                "--output-dir",
                "{output_dir}/gaugegap-0004",
                "--n-plaquettes",
                "1",
                "--disable-qiskit-probe",
            ]
        )
    if args.include_qiskit:
        commands.append(
            [
                sys.executable,
                "scripts/run_qiskit_candidate_validation.py",
                "--output-dir",
                "{output_dir}/gaugegap-qiskit",
                "--n-plaquettes",
                "1",
                "--shots",
                "128",
            ]
        )
    if args.command:
        commands.extend(_split_command(item.format(output_dir=str(args.output_dir))) for item in args.command)
    commands = [[part.format(output_dir=str(args.output_dir)) for part in command] for command in commands]
    return commands


def _run_command(command: list[str], output_dir: Path) -> dict[str, object]:
    started = _utc_now()
    proc = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    ended = _utc_now()
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


def _reproducible_digest(file_records: list[dict[str, object]]) -> str:
    """Content digest over the scientific payload, invariant to run metadata.

    Hashes the sorted ``path:sha256`` pairs of the benchmark output files. The
    per-command stdout/stderr logs are excluded because they embed the absolute
    output directory; everything else is byte-stable across runs once
    SOURCE_DATE_EPOCH is fixed, so this digest pins the reproducible science.
    """
    digest = hashlib.sha256()
    for record in sorted(file_records, key=lambda item: str(item["path"])):
        path = str(record["path"])
        if path.startswith("commands/") or path.startswith("commands\\"):
            continue
        digest.update(f"{path}:{record['sha256']}\n".encode("utf-8"))
    return digest.hexdigest()


def _markdown(manifest: dict[str, object]) -> str:
    lines = [
        "# Reproducibility Proofpack",
        "",
        f"> {manifest['claim_boundary']}",
        "",
        f"Created: `{manifest['created_at_utc']}`",
        f"Git commit: `{manifest['git']['commit']}`",
        f"Dirty tree: `{manifest['git']['dirty']}`",
        f"Python: `{manifest['python'].split()[0]}`",
        f"Reproducible digest: `{manifest.get('reproducible_digest')}`",
        "",
        "The reproducible digest is a content hash of the benchmark outputs that "
        "is invariant to run timestamps. Regenerating this proofpack from a fresh "
        "clone with the same `SOURCE_DATE_EPOCH` reproduces it byte-for-byte.",
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


def _dependency_versions() -> dict[str, str | None]:
    packages = [
        "numpy",
        "scipy",
        "mpmath",
        "PyYAML",
        "pytest",
        "qiskit",
        "qiskit-aer",
        "qiskit-ibm-runtime",
    ]
    versions: dict[str, str | None] = {}
    for package in packages:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return versions


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def _git(*args: str) -> str | None:
    proc = subprocess.run(["git", "-C", str(ROOT), *args], text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def _split_command(command: str) -> list[str]:
    return command.split()


if __name__ == "__main__":
    raise SystemExit(main())
