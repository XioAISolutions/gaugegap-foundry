from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from gaugegap.formal_registry import build_formal_registry
from gaugegap.quantum_provider import (
    LocalStatevectorProvider,
    ProviderRegistry,
    QuantumExecutionRequest,
    mitigate_binary_counts,
)
from gaugegap.reproducibility import build_attestation
from gaugegap.scientific_benchmarks import evaluate_check, run_suite


ROOT = Path(__file__).resolve().parents[1]


def test_checked_in_known_answer_suite_passes():
    result = run_suite(ROOT / "benchmarks" / "known_answers.json")
    assert result.passed, result.summary()
    assert result.case_count == 4
    assert not result.failed_cases
    assert {case.case_id for case in result.cases} >= {
        "standard-model-tree-default",
        "infogap-no-hiding-generic-qubit",
    }


def test_error_budget_fails_closed():
    check = evaluate_check(1.01, {"path": "value", "expected": 1.0, "abs_tol": 0.001})
    assert not check.passed
    assert check.absolute_error == pytest.approx(0.01)
    assert check.allowed_error == pytest.approx(0.001)


def test_formal_registry_detects_holes(tmp_path: Path):
    (tmp_path / "proof.lean").write_text("theorem ok : True := by trivial\n", encoding="utf-8")
    (tmp_path / "hole.v").write_text("Theorem x : True. Admitted.\n", encoding="utf-8")
    registry = build_formal_registry(tmp_path)
    assert registry.artifact_count == 2
    assert registry.hole_free_count == 1
    assert registry.artifacts_with_holes == ("hole.v",)


def test_source_attestation_is_repeatable_and_sensitive(tmp_path: Path):
    (tmp_path / "src").mkdir()
    target = tmp_path / "src" / "model.py"
    target.write_text("VALUE = 1\n", encoding="utf-8")
    first = build_attestation(tmp_path, source_date_epoch=123)
    second = build_attestation(tmp_path, source_date_epoch=123)
    assert first == second
    target.write_text("VALUE = 2\n", encoding="utf-8")
    third = build_attestation(tmp_path, source_date_epoch=123)
    assert third.content_digest != first.content_digest


def test_local_provider_is_seeded_and_registry_is_fail_closed():
    provider = LocalStatevectorProvider()
    registry = ProviderRegistry()
    registry.register(provider)
    assert registry.ids() == ("local-statevector",)
    with pytest.raises(ValueError, match="already registered"):
        registry.register(provider)
    with pytest.raises(KeyError, match="unknown provider"):
        registry.get("missing")

    state = (2 ** -0.5, 0j, 0j, 2 ** -0.5)
    request = QuantumExecutionRequest("sample_statevector", state, shots=1000, seed=44)
    first = provider.execute(request)
    second = provider.execute(request)
    assert first == second
    assert first.counts is not None
    assert sum(first.counts.values()) == 1000
    assert set(first.counts) <= {"00", "11"}

    expectation = provider.execute(
        QuantumExecutionRequest("expectation_pauli_z", state, shots=0, seed=44, qubit=0)
    )
    assert expectation.expectation == pytest.approx(0.0, abs=1e-15)


def test_binary_readout_mitigation_recovers_distribution():
    true = np.array([0.8, 0.2])
    matrix = np.array([[0.9, 0.1], [0.1, 0.9]])
    measured = matrix @ true
    counts = {"0": int(round(measured[0] * 10000)), "1": int(round(measured[1] * 10000))}
    corrected = mitigate_binary_counts(counts, ((0.9, 0.1), (0.1, 0.9)))
    assert corrected["0"] == pytest.approx(0.8, abs=2e-4)
    assert corrected["1"] == pytest.approx(0.2, abs=2e-4)
    assert sum(corrected.values()) == pytest.approx(1.0)


def test_benchmark_schema_rejects_empty_suite(tmp_path: Path):
    path = tmp_path / "empty.json"
    path.write_text(json.dumps({"schema": "gaugegap.known_answers.v1", "cases": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="at least one case"):
        run_suite(path)
