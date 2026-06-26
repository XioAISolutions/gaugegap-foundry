"""Repository inventory and reachability audit for GaugeGap Foundry.

The audit distinguishes hard failures from review candidates. Unregistered runnable
scripts fail the audit; modules that appear unreferenced are reported for human review
because dynamic imports are common in scientific software.
"""
from __future__ import annotations

import ast
from dataclasses import asdict, dataclass
import hashlib
from pathlib import Path
from typing import Iterable

from gaugegap.cli import all_units, load_config


@dataclass(frozen=True)
class ModuleRecord:
    module: str
    path: str
    sha256: str
    imported: bool
    mentioned_by_test: bool
    entrypoint: bool
    review_candidate: bool


@dataclass(frozen=True)
class RepositoryInventory:
    passed: bool
    module_count: int
    test_count: int
    configured_unit_count: int
    discovered_unit_count: int
    unregistered_run_scripts: tuple[str, ...]
    review_candidates: tuple[str, ...]
    modules: tuple[ModuleRecord, ...]

    def summary(self) -> dict[str, object]:
        return {
            "schema": "gaugegap.repository_inventory.v1",
            "passed": self.passed,
            "module_count": self.module_count,
            "test_count": self.test_count,
            "configured_unit_count": self.configured_unit_count,
            "discovered_unit_count": self.discovered_unit_count,
            "unregistered_run_scripts": list(self.unregistered_run_scripts),
            "review_candidates": list(self.review_candidates),
            "modules": [asdict(item) for item in self.modules],
            "claim_boundary": (
                "static repository reachability audit only; review candidates are not "
                "proof that code is unused because dynamic imports may exist"
            ),
        }


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _module_name(path: Path, source_root: Path) -> str:
    relative = path.relative_to(source_root).with_suffix("")
    parts = list(relative.parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _imports(paths: Iterable[Path]) -> set[str]:
    imported: set[str] = set()
    for path in paths:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
    return imported


def build_inventory(root: Path | str) -> RepositoryInventory:
    root_path = Path(root).resolve()
    source_root = root_path / "src"
    package_root = source_root / "gaugegap"
    module_paths = sorted(package_root.rglob("*.py"))
    test_paths = sorted((root_path / "tests").glob("test*.py"))
    script_paths = sorted((root_path / "scripts").glob("*.py"))
    imported_names = _imports((*module_paths, *test_paths, *script_paths))
    test_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace") for path in test_paths
    )

    config = load_config(root_path / "config" / "foundry.yaml")
    units = all_units(config, root_path)
    configured_scripts = {
        token
        for unit in config.units.values()
        for token in unit.command
        if token.startswith("scripts/") and token.endswith(".py")
    }
    run_scripts = {
        path.relative_to(root_path).as_posix()
        for path in (root_path / "scripts").glob("run_*.py")
    }
    unregistered = tuple(sorted(run_scripts - configured_scripts))

    entrypoints = {"gaugegap.cli", "gaugegap.certify"}
    records: list[ModuleRecord] = []
    for path in module_paths:
        module = _module_name(path, source_root)
        if not module:
            continue
        imported = any(
            name == module or name.startswith(module + ".") or module.startswith(name + ".")
            for name in imported_names
        )
        mentioned = module in test_text or path.stem in test_text
        entrypoint = module in entrypoints or path.name == "__init__.py"
        review_candidate = not imported and not mentioned and not entrypoint
        records.append(
            ModuleRecord(
                module=module,
                path=path.relative_to(root_path).as_posix(),
                sha256=_digest(path),
                imported=imported,
                mentioned_by_test=mentioned,
                entrypoint=entrypoint,
                review_candidate=review_candidate,
            )
        )

    review_candidates = tuple(sorted(item.module for item in records if item.review_candidate))
    discovered_count = sum(1 for unit in units.values() if unit.status == "unclassified")
    return RepositoryInventory(
        passed=not unregistered,
        module_count=len(records),
        test_count=len(test_paths),
        configured_unit_count=len(config.units),
        discovered_unit_count=discovered_count,
        unregistered_run_scripts=unregistered,
        review_candidates=review_candidates,
        modules=tuple(records),
    )
