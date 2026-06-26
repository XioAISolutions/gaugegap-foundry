#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DEFAULT_INCLUDE = ("README.md", "DEPLOYMENT.md", "docs", "hypotheses", "results")
DEFAULT_EXCLUDE_PARTS = (".git", ".venv", "__pycache__", ".pytest_cache", "node_modules")

RISK_PATTERNS = [
    ("millennium_solution", re.compile(r"\b(solved|solution to|proof of)\s+(a\s+|the\s+)?(millennium|yang[- ]mills|navier[- ]stokes|riemann)\b", re.I)),
    ("named_problem_proof", re.compile(r"\b((yang[- ]mills|navier[- ]stokes|riemann)\s+.*proof|proof\s+.*(yang[- ]mills|navier[- ]stokes|riemann))\b", re.I)),
    ("prize_claim", re.compile(r"\b(clay prize|million[- ]dollar prize|\$1m|\$1 million)\b", re.I)),
    ("proof_complete", re.compile(r"\b(proof complete|complete proof|fully proven|rigorous proof complete)\b", re.I)),
    ("publication_ready", re.compile(r"\b(ready for publication|publication ready|publishable proof)\b", re.I)),
    ("certainty_overclaim", re.compile(r"\b(proven|proved|guaranteed|cannot fail|definitive)\b", re.I)),
    # Ported from the former inline CI check so the workflow and this script
    # enforce one shared rule set.
    ("ai_discovery_claim", re.compile(r"\bai (discovered|proved|solved)\b", re.I)),
    ("quantum_proof_claim", re.compile(r"\bquantum computer proves\b", re.I)),
]

SAFE_CONTEXT_PATTERNS = [
    re.compile(r"\bnot\s+claiming\b", re.I),
    re.compile(r"\bdoes\s+not\s+claim\b", re.I),
    re.compile(r"\bnot\s+a\s+.*proof\b", re.I),
    re.compile(r"\bno\s+continuum\s+.*claim\b", re.I),
    re.compile(r"\bfinite[- ]system\b", re.I),
    re.compile(r"\btoy\s+benchmark\b", re.I),
    re.compile(r"\bclaim boundary\b", re.I),
    re.compile(r"\bavoid\s+.*claim\b", re.I),
    # Explicit deny-list headings enumerate wording the project rejects.  This
    # phrase appears in the README immediately before examples of claims the
    # finite-system evidence does not earn.
    re.compile(r"\blanguage\s+this\s+project\s+does\s+not\s+earn\b", re.I),
    # "Avoided language:" lists enumerate phrases the project deliberately does
    # NOT use; the quoted phrases are negative examples, not claims.
    re.compile(r"\bavoided\s+language\b", re.I),
    re.compile(r"\bdo not use\b", re.I),
    re.compile(r"\brisky phrases\b", re.I),
    re.compile(r"\bnegative[- ]result\b", re.I),
    re.compile(r"\brequires? independent.*review\b", re.I),
    # Deny-list sections that *quote* risky phrases in order to ban them.
    re.compile(r"\bforbidden\s+language\b", re.I),
]

# Generated output directories must never be scanned: their reports/packets
# quote the risky phrases they flag (and re-copy deny-list docs), so scanning
# them makes the audit poison itself. These are build artifacts, not sources.
AUDIT_OUTPUT_PARTS = (
    "claim-boundary-audit",
    "research-maturity-audit",
    "reviewer-packet",
    "proofpack",
)


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    kind: str
    severity: str
    text: str


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan repo docs/results for scientific claim-boundary risk.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--include", action="append", default=None, help="File or directory to scan; repeatable")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "claim-boundary-audit")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero on high-severity findings")
    args = parser.parse_args()

    include = tuple(args.include) if args.include else DEFAULT_INCLUDE
    findings = scan(args.root, include)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_json(args.output_dir / "claim_boundary_audit.json", findings)
    write_markdown(args.output_dir / "claim_boundary_audit.md", findings)

    high = [finding for finding in findings if finding.severity == "high"]
    status = "fail" if high else "pass"
    print(json.dumps({"status": status, "findings": len(findings), "high": len(high), "output_dir": str(args.output_dir)}, indent=2))
    if args.strict and high:
        return 2
    return 0


def scan(root: Path, include: tuple[str, ...]) -> list[Finding]:
    findings: list[Finding] = []
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
            if any(part in AUDIT_OUTPUT_PARTS for part in file_path.parts):
                continue
            findings.extend(scan_file(root, file_path))
    return findings


def scan_file(root: Path, file_path: Path) -> list[Finding]:
    try:
        text = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    relative = str(file_path.relative_to(root))
    findings: list[Finding] = []
    lines = text.splitlines()
    for idx, line in enumerate(lines, start=1):
        context = _context(lines, idx - 1)
        safe = any(pattern.search(context) for pattern in SAFE_CONTEXT_PATTERNS)
        for kind, pattern in RISK_PATTERNS:
            if pattern.search(line):
                severity = "low" if safe else "high"
                findings.append(Finding(path=relative, line=idx, kind=kind, severity=severity, text=line.strip()))
    return findings


def write_json(path: Path, findings: list[Finding]) -> None:
    path.write_text(json.dumps([asdict(item) for item in findings], indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: Path, findings: list[Finding]) -> None:
    high = [item for item in findings if item.severity == "high"]
    lines = [
        "# Claim Boundary Audit",
        "",
        f"Status: {'FAIL' if high else 'PASS'}",
        "",
        f"Total findings: {len(findings)}",
        f"High severity: {len(high)}",
        "",
        "High severity findings should be rewritten or explicitly bounded as finite-system, toy, conjectural, or negative-result claims.",
        "",
        "| severity | kind | path | line | text |",
        "|---|---|---|---:|---|",
    ]
    for item in findings:
        lines.append(f"| {item.severity} | {item.kind} | `{item.path}` | {item.line} | {item.text.replace('|', '/')} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _context(lines: list[str], index: int) -> str:
    start = max(0, index - 2)
    stop = min(len(lines), index + 3)
    return "\n".join(lines[start:stop])


def _is_text_path(path: Path) -> bool:
    return path.suffix.lower() in {".md", ".txt", ".json", ".jsonl", ".csv", ".yaml", ".yml"} or path.name in {"README.md", "DEPLOYMENT.md"}


if __name__ == "__main__":
    raise SystemExit(main())
