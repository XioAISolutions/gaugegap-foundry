#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_INCLUDE = (
    "README.md",
    "DEPLOYMENT.md",
    "docs",
    "hypotheses",
    "scripts",
    "src",
    "tests",
)
DEFAULT_EXCLUDE_PARTS = (
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "node_modules",
    "results",
)

# The audit scripts define the very patterns they scan for; scanning them
# reports their own pattern tables as findings.
EXCLUDE_FILES = ("research_maturity_audit.py", "claim_boundary_audit.py")

MATURITY_PATTERNS = [
    ("placeholder", re.compile(r"\bplaceholder\b", re.I)),
    ("future_implementation", re.compile(r"\bfuture implementation\b", re.I)),
    ("not_implemented", re.compile(r"\bnot implemented\b|\bnot_implemented\b", re.I)),
    ("todo", re.compile(r"\bTODO\b", re.I)),
    ("pass_statement", re.compile(r"^\s*pass\s*(#.*)?$", re.I)),
    ("simplified", re.compile(r"\bsimplified\b", re.I)),
    ("approximate", re.compile(r"\bapproximate\b|\bapproximation\b", re.I)),
]

BOUNDING_PATTERNS = [
    re.compile(r"\bprototype\b", re.I),
    re.compile(r"\bscaffold\b", re.I),
    re.compile(r"\btoy\b", re.I),
    re.compile(r"\bexplicitly not implemented\b", re.I),
    re.compile(r"\bknown limitation\b", re.I),
    re.compile(r"\broadmap\b", re.I),
    re.compile(r"\bwork order\b", re.I),
    re.compile(r"\bdefinition of done\b", re.I),
]

SCIENTIFIC_CORE_HINTS = (
    "gaugegap_su3",
    "gaugegap_su2",
    "gaugegap_u1",
    "curverank",
    "flowgap",
    "hamiltonian",
    "operator",
)

TEXT_SUFFIXES = {".py", ".md", ".txt", ".json", ".jsonl", ".csv", ".yaml", ".yml", ".toml"}


@dataclass(frozen=True)
class MaturityFinding:
    path: str
    line: int
    kind: str
    severity: str
    text: str
    bounded: bool


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan research code/docs for maturity and placeholder risk.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--include", action="append", default=None, help="File or directory to scan; repeatable")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "research-maturity-audit")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero on unbounded high-severity findings")
    args = parser.parse_args()

    include = tuple(args.include) if args.include else DEFAULT_INCLUDE
    findings = scan(args.root, include)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "research_maturity_audit.json", findings)
    write_markdown(args.output_dir / "research_maturity_audit.md", findings)

    high_unbounded = [item for item in findings if item.severity == "high" and not item.bounded]
    status = "fail" if high_unbounded else "pass"
    payload = {
        "status": status,
        "findings": len(findings),
        "high_unbounded": len(high_unbounded),
        "output_dir": str(args.output_dir),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    if args.strict and high_unbounded:
        return 2
    return 0


def scan(root: Path, include: tuple[str, ...]) -> list[MaturityFinding]:
    findings: list[MaturityFinding] = []
    for item in include:
        path = root / item
        if not path.exists():
            continue
        if path.is_dir():
            paths = sorted(p for p in path.rglob("*") if p.is_file() and _is_text_path(p))
        else:
            paths = [path] if _is_text_path(path) else []
        for file_path in paths:
            if any(part in DEFAULT_EXCLUDE_PARTS for part in file_path.parts):
                continue
            if file_path.name in EXCLUDE_FILES:
                continue
            findings.extend(scan_file(root, file_path))
    return findings


def scan_file(root: Path, file_path: Path) -> list[MaturityFinding]:
    try:
        text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []

    relative = str(file_path.relative_to(root))
    lines = text.splitlines()
    findings: list[MaturityFinding] = []
    for idx, line in enumerate(lines, start=1):
        context = _context(lines, idx - 1)
        bounded = any(pattern.search(context) for pattern in BOUNDING_PATTERNS)
        for kind, pattern in MATURITY_PATTERNS:
            if not pattern.search(line):
                continue
            severity = classify(relative, kind, bounded)
            findings.append(
                MaturityFinding(
                    path=relative,
                    line=idx,
                    kind=kind,
                    severity=severity,
                    text=line.strip(),
                    bounded=bounded,
                )
            )
    return findings


def classify(path: str, kind: str, bounded: bool) -> str:
    suffix = Path(path).suffix.lower()
    is_source = suffix == ".py"
    # Tests that assert prototype/not-implemented status are the enforcement
    # mechanism for the claim boundary, not unbounded research claims.
    if path.startswith("tests/"):
        return "low"
    in_core = is_source and any(hint in path.lower() for hint in SCIENTIFIC_CORE_HINTS)

    if kind == "pass_statement" and in_core:
        return "medium" if bounded else "high"
    if in_core and kind in {"placeholder", "future_implementation", "not_implemented", "simplified", "approximate"}:
        return "medium" if bounded else "high"
    if is_source and kind in {"placeholder", "future_implementation", "not_implemented"}:
        return "medium" if bounded else "high"
    if suffix == ".md":
        return "low" if bounded else "medium"
    return "low" if bounded else "medium"


def write_json(path: Path, findings: list[MaturityFinding]) -> None:
    path.write_text(json.dumps([asdict(item) for item in findings], indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: Path, findings: list[MaturityFinding]) -> None:
    high_unbounded = [item for item in findings if item.severity == "high" and not item.bounded]
    lines = [
        "# Research Maturity Audit",
        "",
        f"Status: {'FAIL' if high_unbounded else 'PASS'}",
        "",
        f"Total findings: {len(findings)}",
        f"High unbounded findings: {len(high_unbounded)}",
        "",
        "A finding is acceptable when a prototype, toy, roadmap, or known-limitation boundary is stated near it.",
        "Unbounded high-severity findings should be rewritten, implemented, or marked as prototype before public claims are made.",
        "",
        "| severity | bounded | kind | path | line | text |",
        "|---|---:|---|---|---:|---|",
    ]
    for item in findings:
        clean = item.text.replace("|", "/")
        lines.append(f"| {item.severity} | {str(item.bounded).lower()} | {item.kind} | `{item.path}` | {item.line} | {clean} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _context(lines: list[str], index: int) -> str:
    start = max(0, index - 3)
    stop = min(len(lines), index + 4)
    return "\n".join(lines[start:stop])


def _is_text_path(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES or path.name in {"README.md", "DEPLOYMENT.md", "Makefile"}


if __name__ == "__main__":
    raise SystemExit(main())
