"""Known-answer scientific benchmarks with explicit numerical error budgets.

The benchmark engine is deliberately small and deterministic. It compares finite
results against versioned reference values and fails closed when any configured budget
is exceeded. Benchmarks validate implementations; they do not promote finite models
into continuum claims.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
from typing import Any, Callable, Mapping

from gaugegap.hamiltonian_factory import build_and_audit
from gaugegap.quantum_information.no_hiding import audit_no_hiding
from gaugegap.standard_model_catalog import tree_level_observables


@dataclass(frozen=True)
class NumericCheck:
    path: str
    expected: float | int | bool | str
    actual: float | int | bool | str
    absolute_error: float | None
    allowed_error: float | None
    passed: bool


@dataclass(frozen=True)
class BenchmarkCaseResult:
    case_id: str
    runner: str
    passed: bool
    checks: tuple[NumericCheck, ...]
    claim_boundary: str


@dataclass(frozen=True)
class BenchmarkSuiteResult:
    schema: str
    passed: bool
    case_count: int
    failed_cases: tuple[str, ...]
    cases: tuple[BenchmarkCaseResult, ...]

    def summary(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "passed": self.passed,
            "case_count": self.case_count,
            "failed_cases": list(self.failed_cases),
            "cases": [
                {
                    **asdict(case),
                    "checks": [asdict(check) for check in case.checks],
                }
                for case in self.cases
            ],
        }


def _lookup(payload: Any, dotted_path: str) -> Any:
    value = payload
    for part in dotted_path.split("."):
        if isinstance(value, Mapping):
            value = value[part]
        elif isinstance(value, (list, tuple)):
            value = value[int(part)]
        else:
            raise KeyError(f"cannot descend through {part!r} in {dotted_path!r}")
    return value


def _run_standard_model(parameters: Mapping[str, Any]) -> dict[str, Any]:
    return tree_level_observables({key: float(value) for key, value in parameters.items()})


def _run_hamiltonian(parameters: Mapping[str, Any]) -> dict[str, Any]:
    values = dict(parameters)
    model_id = str(values.pop("model_id"))
    _, audit = build_and_audit(model_id, **values)
    return audit.summary()


def _run_no_hiding(parameters: Mapping[str, Any]) -> dict[str, Any]:
    values = dict(parameters)
    theta = float(values.pop("theta"))
    phi = float(values.pop("phi"))
    tolerance = float(values.pop("tolerance", 1e-10))
    if values:
        raise ValueError(f"unknown no-hiding parameters: {sorted(values)}")
    return audit_no_hiding(theta, phi, label="known-answer", tolerance=tolerance).summary()


_RUNNERS: dict[str, Callable[[Mapping[str, Any]], dict[str, Any]]] = {
    "standard_model_tree": _run_standard_model,
    "hamiltonian_audit": _run_hamiltonian,
    "no_hiding": _run_no_hiding,
}


def evaluate_check(actual: Any, check: Mapping[str, Any]) -> NumericCheck:
    expected = check["expected"]
    path = str(check["path"])
    if isinstance(expected, bool) or isinstance(expected, str):
        passed = actual == expected
        return NumericCheck(path, expected, actual, None, None, passed)
    if not isinstance(actual, (int, float)) or isinstance(actual, bool):
        return NumericCheck(path, expected, str(actual), None, None, False)
    actual_number = float(actual)
    expected_number = float(expected)
    absolute_error = abs(actual_number - expected_number)
    absolute_tolerance = float(check.get("abs_tol", 0.0))
    relative_tolerance = float(check.get("rel_tol", 0.0))
    allowed = max(absolute_tolerance, relative_tolerance * abs(expected_number))
    passed = math.isfinite(actual_number) and absolute_error <= allowed
    return NumericCheck(path, expected, actual_number, absolute_error, allowed, passed)


def run_case(case: Mapping[str, Any]) -> BenchmarkCaseResult:
    case_id = str(case["id"])
    runner_name = str(case["runner"])
    try:
        runner = _RUNNERS[runner_name]
    except KeyError as exc:
        raise ValueError(f"unknown benchmark runner {runner_name!r}") from exc
    payload = runner(case.get("parameters", {}))
    results: list[NumericCheck] = []
    for check in case.get("checks", []):
        path = str(check["path"])
        try:
            actual = _lookup(payload, path)
        except (KeyError, IndexError, TypeError, ValueError):
            actual = "<missing>"
        results.append(evaluate_check(actual, check))
    return BenchmarkCaseResult(
        case_id=case_id,
        runner=runner_name,
        passed=all(item.passed for item in results),
        checks=tuple(results),
        claim_boundary=str(
            case.get(
                "claim_boundary",
                "finite known-answer regression only; no continuum theorem claim",
            )
        ),
    )


def run_suite(spec_path: Path | str) -> BenchmarkSuiteResult:
    path = Path(spec_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "gaugegap.known_answers.v1":
        raise ValueError("unsupported benchmark schema")
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("benchmark suite must contain at least one case")
    ids = [str(case.get("id", "")) for case in raw_cases]
    if any(not case_id for case_id in ids) or len(ids) != len(set(ids)):
        raise ValueError("benchmark case IDs must be unique non-empty strings")
    cases = tuple(run_case(case) for case in raw_cases)
    failed = tuple(case.case_id for case in cases if not case.passed)
    return BenchmarkSuiteResult(
        schema="gaugegap.benchmark_results.v1",
        passed=not failed,
        case_count=len(cases),
        failed_cases=failed,
        cases=cases,
    )
