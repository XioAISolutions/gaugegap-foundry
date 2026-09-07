#!/usr/bin/env python3
"""Gate the Lean Anomaly Forge: structure check, exact mirror, real ``lake build``.

Three checks, in increasing strength:

1. **Structure** -- every node of ``formal/lean/dag.json`` names a statement and a
   proof that exist in the Lean sources, declared dependencies match the proof
   terms actually referenced, and no source contains ``sorry``, ``admit``,
   ``axiom`` or ``native_decide``.
2. **Mirror** -- ``src/gaugegap/anomaly_theorem.py`` restates every node over
   exact rationals and checks it on a finite grid.
3. **Kernel** -- ``lake build`` in ``formal/lean``.  This is the only check that
   makes "machine-checked" literally true.

There is deliberately no simulated proof mode.  When ``lake`` is unavailable the
report says ``toolchain_missing``; it never says verified.  ``--require-verified``
exits non-zero unless Lean itself accepted the proofs.

CLAIM BOUNDARY: this verifies that the Lean statements compile and are proved
for a declared finite chiral field inventory.  It is not a claim about arbitrary
chiral gauge theories and not a Millennium Prize claim.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.lean_mirror import NODE_CHECKS, mirror_summary  # noqa: E402

LEAN_DIR = ROOT / "formal" / "lean"
DAG_PATH = LEAN_DIR / "dag.json"
HOLE_PATTERN = re.compile(
    r"^\s*(?:sorry|admit|axiom)\b|\bnative_decide\b", re.MULTILINE
)


@dataclass(frozen=True)
class StructureIssue:
    node_id: str
    problem: str


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# Dependency checkouts and build output live under the package directory but are
# not this project's sources; Mathlib's own test files carry `sorry` on purpose.
VENDORED_PARTS = {".lake", "lake-packages", "build"}


def _lean_sources() -> list[Path]:
    return sorted(
        path
        for path in LEAN_DIR.rglob("*.lean")
        if not VENDORED_PARTS & set(path.relative_to(LEAN_DIR).parts)
    )


def _strip_comments(text: str) -> str:
    """Remove Lean block and line comments so prose never looks like a hole."""
    without_blocks = re.sub(r"/-.*?-/", " ", text, flags=re.DOTALL)
    return re.sub(r"--.*", " ", without_blocks)


def _theorem_bodies(text: str) -> dict[str, str]:
    """Map theorem name -> body text, by splitting on top-level ``theorem``."""
    bodies: dict[str, str] = {}
    starts = [(m.start(), m.group(1)) for m in re.finditer(r"(?m)^theorem\s+(\w+)", text)]
    for index, (offset, name) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(text)
        bodies[name] = text[offset:end]
    return bodies


def check_structure(dag: dict) -> list[StructureIssue]:
    issues: list[StructureIssue] = []
    module_text: dict[str, str] = {}

    def text_of(module: str) -> str:
        if module not in module_text:
            module_text[module] = _strip_comments(
                (LEAN_DIR / module).read_text(encoding="utf-8")
            )
        return module_text[module]

    proof_by_node = {node["id"]: node["proof"] for node in dag["nodes"]}

    for source in _lean_sources():
        code = _strip_comments(source.read_text(encoding="utf-8"))
        holes = HOLE_PATTERN.findall(code)
        if holes:
            issues.append(
                StructureIssue("-", f"{source.relative_to(ROOT)} contains a proof hole")
            )

    for node in dag["nodes"]:
        node_id = node["id"]
        statements = text_of(node["statement_module"])
        bodies = _theorem_bodies(text_of(node["proof_module"]))
        if not re.search(rf"(?m)^def\s+{re.escape(node['statement'])}\b", statements):
            issues.append(StructureIssue(node_id, f"missing statement {node['statement']}"))
        body = bodies.get(node["proof"])
        if body is None:
            issues.append(StructureIssue(node_id, f"missing proof {node['proof']}"))
            continue
        if node["statement"] not in body.split(":=", 1)[0]:
            issues.append(
                StructureIssue(node_id, f"{node['proof']} does not prove {node['statement']}")
            )
        referenced = {
            other_id
            for other_id, proof_name in proof_by_node.items()
            if other_id != node_id and re.search(rf"\b{re.escape(proof_name)}\b", body)
        }
        declared = set(node["depends_on"])
        if referenced != declared:
            issues.append(
                StructureIssue(
                    node_id,
                    f"declared dependencies {sorted(declared)} "
                    f"but proof references {sorted(referenced)}",
                )
            )
        if node_id not in NODE_CHECKS:
            issues.append(StructureIssue(node_id, "no Python mirror in anomaly_theorem.py"))

    for node_id in sorted(set(NODE_CHECKS) - {node["id"] for node in dag["nodes"]}):
        issues.append(StructureIssue(node_id, "Python mirror has no DAG node"))
    return issues


def run_lake(lake: str | None, timeout: int) -> dict[str, object]:
    """Run the real proof check.  No simulation path exists."""
    executable = lake or shutil.which("lake")
    if executable is None:
        return {
            "status": "toolchain_missing",
            "detail": "lake not found on PATH; install elan and rerun, or use CI",
            "returncode": None,
        }
    try:
        completed = subprocess.run(
            [executable, "build"],
            cwd=LEAN_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "status": "failed",
            "detail": f"lake build timed out after {timeout}s",
            "returncode": None,
        }
    except OSError as exc:
        return {
            "status": "toolchain_missing",
            "detail": f"could not run {executable}: {exc}",
            "returncode": None,
        }
    if completed.returncode == 0:
        # Deterministic on success: the build log varies between a cold and a
        # warm cache, and this report is committed by CI, so a varying detail
        # would produce an endless stream of no-op commits. On failure the log
        # is the whole point, so it is kept.
        return {"status": "verified", "detail": "lake build exited 0", "returncode": 0}
    tail = "\n".join((completed.stdout + completed.stderr).splitlines()[-40:])
    return {"status": "failed", "detail": tail, "returncode": completed.returncode}


def build_report(lake: str | None, timeout: int, skip_lake: bool) -> dict[str, object]:
    dag = json.loads(DAG_PATH.read_text(encoding="utf-8"))
    issues = check_structure(dag)
    mirror = mirror_summary()
    kernel = (
        {"status": "skipped", "detail": "--skip-lake requested", "returncode": None}
        if skip_lake
        else run_lake(lake, timeout)
    )
    tracked = [*_lean_sources(), DAG_PATH]
    # The toolchain and dependency pins decide what "checked" means, so they are
    # part of the hashed evidence, not build scaffolding.
    tracked += [
        LEAN_DIR / name
        for name in ("lean-toolchain", "lakefile.toml", "lake-manifest.json")
        if (LEAN_DIR / name).exists()
    ]
    sources = {
        path.relative_to(ROOT).as_posix(): _sha256(path) for path in sorted(tracked)
    }
    content_hash = hashlib.sha256(
        json.dumps(sources, sort_keys=True).encode("utf-8")
    ).hexdigest()
    verified = kernel["status"] == "verified"
    return {
        "schema": "gaugegap.lean_forge.v2",
        "targets": dag["targets"],
        "node_count": len(dag["nodes"]),
        "nodes": [
            {
                "id": node["id"],
                "track": node["track"],
                "statement": node["statement"],
                "proof": node["proof"],
                "depends_on": node["depends_on"],
                "mirror_holds": mirror["nodes"].get(node["id"]),
                "lean_status": "verified" if verified else kernel["status"],
            }
            for node in dag["nodes"]
        ],
        "structure": {
            "ok": not issues,
            "issues": [asdict(issue) for issue in issues],
        },
        "mirror": mirror,
        "kernel_check": kernel,
        "sources": sources,
        "content_hash": content_hash,
        "claim_boundary": dag["claim_boundary"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "results" / "lean-forge")
    parser.add_argument("--lake", help="path to the lake executable")
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument(
        "--skip-lake", action="store_true", help="structure and mirror checks only"
    )
    parser.add_argument(
        "--require-verified",
        action="store_true",
        help="exit non-zero unless lake build actually verified the proofs",
    )
    args = parser.parse_args()

    report = build_report(args.lake, args.timeout, args.skip_lake)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "lean_forge_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))

    if not report["structure"]["ok"] or not report["mirror"]["all_hold"]:
        return 2
    if args.require_verified and report["kernel_check"]["status"] != "verified":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
