#!/usr/bin/env python3
"""Assemble a self-contained reviewer packet for outside experts (issue #12 A7).

Collects the artifacts an external reviewer needs to assess this repository
without reading the whole tree, into a single directory with a generated
``INDEX.md``: the claim boundary, provenance (commit, Python, dependency
versions), the claim-boundary and research-maturity audit reports, the curated
review docs, a test inventory, and a reviewer checklist with reproduction
commands.

Deterministic: honors SOURCE_DATE_EPOCH so the packet (apart from the live audit
reports) regenerates identically from the same commit.

CLAIM BOUNDARY: this packet documents finite-system, numerical, and prototype
work. Nothing in it claims a continuum proof or a Millennium Prize solution; it
exists precisely so outside experts can verify that boundary.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CLAIM_BOUNDARY = (
    "Finite-system benchmarks, numerical certificates, and an explicitly labeled "
    "SU(3) prototype scaffold. No continuum Yang-Mills / Navier-Stokes / Riemann "
    "proof, and no Millennium Prize solution claim. Hardware results, where "
    "present, are noisy experimental artifacts, not theorem evidence."
)

# (source path, packet filename, one-line description for the index).
CURATED_DOCS = [
    ("docs/reviewer-outreach.md", "00-reviewer-outreach.md",
     "Outreach note: what to review and what feedback is sought"),
    ("docs/independent-review-packet.md", "01-independent-review-packet.md",
     "Trust chain + verification obligations for the certified CurveRank result"),
    ("docs/preprint-curverank-certified-screening.md", "02-preprint-curverank.md",
     "Preprint draft: certified finite-truncation spectral screening"),
    ("docs/eightfold-certified.md", "03-eightfold-certified.md",
     "Certified SU(3)-flavor (Eightfold-Way / Gell-Mann-Okubo) relations"),
    ("docs/anharmonic-certified.md", "04-anharmonic-certified.md",
     "Certified variational bounds for the quartic anharmonic oscillator"),
    ("docs/preprint-gaugegap-infrastructure.md", "05-preprint-infrastructure.md",
     "Preprint draft: verification-first infrastructure overview"),
    ("docs/solution-gap-audit.md", "06-solution-gap-audit.md",
     "Honest readiness scorecard and claim-boundary discipline"),
    ("docs/agent-work-orders.md", "07-agent-work-orders.md",
     "Execution-ready work queue (issue #12)"),
    ("AGENTS.md", "08-AGENTS.md", "Repository claim-boundary policy"),
]


def _utc_now() -> datetime:
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch:
        try:
            return datetime.fromtimestamp(int(epoch), tz=timezone.utc)
        except (ValueError, OverflowError, OSError):
            pass
    return datetime.now(timezone.utc)


def _git(*args: str) -> str | None:
    proc = subprocess.run(["git", "-C", str(ROOT), *args], text=True,
                          capture_output=True, check=False)
    return (proc.stdout.strip() or None) if proc.returncode == 0 else None


def _run_audit(script: str, out_dir: Path, strict: bool) -> dict:
    cmd = [sys.executable, f"scripts/{script}", "--output-dir", str(out_dir)]
    if strict:
        cmd.append("--strict")
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
    # The audit scripts print a single (possibly multi-line) JSON object.
    try:
        payload = json.loads(proc.stdout.strip())
    except json.JSONDecodeError:
        payload = {"status": "error", "stdout": proc.stdout, "stderr": proc.stderr}
    payload["returncode"] = proc.returncode
    return payload


def _dependency_versions() -> dict[str, str | None]:
    import importlib.metadata
    out: dict[str, str | None] = {}
    for pkg in ("numpy", "scipy", "mpmath", "PyYAML", "pytest", "python-flint", "qiskit"):
        try:
            out[pkg] = importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            out[pkg] = None
    return out


def _test_count() -> int | None:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    for line in reversed(proc.stdout.splitlines()):
        if "test" in line and "collected" in line:
            try:
                return int(line.split()[0])
            except (ValueError, IndexError):
                return None
    return None


def _index(packet: Path, claim_audit: dict, maturity_audit: dict,
           test_count: int | None) -> str:
    deps = _dependency_versions()
    dep_rows = "\n".join(f"| {k} | {v or 'not installed'} |" for k, v in deps.items())
    doc_rows = "\n".join(
        f"| [`{fname}`]({fname}) | {desc} |" for _src, fname, desc in CURATED_DOCS
    )
    return f"""# GaugeGap Foundry — Reviewer Packet

Generated: `{_utc_now().isoformat()}`
Commit: `{_git('rev-parse', 'HEAD')}`
Python: `{sys.version.split()[0]}`

> **Claim boundary.** {CLAIM_BOUNDARY}

## How to read this packet

This packet is for an outside expert assessing whether the repository's claims
are honest, finite, and reproducible. Start with the claim boundary above, then
the audit status, then the certified-result trust chain (`01-…`), then the
specific results (`02-…`, `03-…`).

## Audit status (run at generation time)

| audit | status | high-severity |
|-------|--------|---------------|
| claim-boundary (`scripts/claim_boundary_audit.py --strict`) | **{claim_audit.get('status')}** | {claim_audit.get('high')} |
| research-maturity (`scripts/research_maturity_audit.py`) | {maturity_audit.get('status')} | {maturity_audit.get('high_unbounded')} unbounded |

The claim-boundary audit is a hard CI gate (must be `pass`, 0 high). The
research-maturity audit is a *report*: its remaining high_unbounded findings are
the openly-tracked work in issue #12 (real SU(3) implementation, etc.), not
hidden overclaims.

## Reproducibility

```bash
pip install -e ".[dev]"
make audit              # claim-boundary (strict) + maturity report
make proofpack          # finite-benchmark proofpack with a reproducible_digest
make proofpack-verify   # asserts two fresh builds produce the same digest
pytest -q               # full test suite ({test_count if test_count is not None else 'see CI'} tests)
```

The proofpack is deterministic from a fresh clone: `make` pins
`SOURCE_DATE_EPOCH` to the commit date, so the same commit yields a byte-for-byte
identical proofpack (`reproducible_digest`).

## Contents

| file | description |
|------|-------------|
{doc_rows}
| [`claim-boundary-audit.md`](claim-boundary-audit.md) | Full claim-boundary scan |
| [`research-maturity-audit.md`](research-maturity-audit.md) | Full maturity scan |

## Environment

| package | version |
|---------|---------|
{dep_rows}

## Reviewer checklist

- [ ] The claim boundary above is respected throughout (no continuum/prize claims).
- [ ] `make audit` passes the claim-boundary gate (0 high).
- [ ] `make proofpack-verify` reports `reproducible: true`.
- [ ] `pytest -q` is green; spot-check the known-answer tests (`tests/test_known_answers.py`).
- [ ] The certified CurveRank result's verification obligations (`01-…`) are acceptable.
- [ ] The SU(3) lane is labeled a prototype scaffold wherever it appears.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", type=Path, default=ROOT / "results" / "reviewer-packet")
    args = ap.parse_args()

    packet = args.output_dir
    if packet.exists():
        shutil.rmtree(packet)
    packet.mkdir(parents=True, exist_ok=True)

    # Live audits (their reports go into the packet).
    claim_audit = _run_audit("claim_boundary_audit.py",
                             packet / "_claim-boundary-audit", strict=True)
    maturity_audit = _run_audit("research_maturity_audit.py",
                                packet / "_research-maturity-audit", strict=False)
    for src_dir, dst in (("_claim-boundary-audit/claim_boundary_audit.md", "claim-boundary-audit.md"),
                         ("_research-maturity-audit/research_maturity_audit.md", "research-maturity-audit.md")):
        report = packet / src_dir
        if report.exists():
            shutil.copy(report, packet / dst)
    # Drop the intermediate audit output dirs; only the .md reports stay.
    for tmp in ("_claim-boundary-audit", "_research-maturity-audit"):
        shutil.rmtree(packet / tmp, ignore_errors=True)

    # Curated docs.
    missing = []
    for src, fname, _desc in CURATED_DOCS:
        src_path = ROOT / src
        if src_path.exists():
            shutil.copy(src_path, packet / fname)
        else:
            missing.append(src)

    (packet / "INDEX.md").write_text(
        _index(packet, claim_audit, maturity_audit, _test_count())
    )

    result = {
        "status": "pass" if claim_audit.get("status") == "pass" and not missing else "fail",
        "output_dir": str(packet),
        "claim_boundary_audit": claim_audit.get("status"),
        "missing_docs": missing,
    }
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
