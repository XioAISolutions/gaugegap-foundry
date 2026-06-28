from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from gaugegap.quantum_information.density import density_matrix, partial_trace, trace_distance
from gaugegap.quantum_information.no_hiding import (
    audit_no_hiding,
    no_hiding_unitary,
    output_state,
    qubit_state,
    run_no_hiding_suite,
)
from gaugegap.quantum_provider import LocalStatevectorProvider, QuantumExecutionRequest

ROOT = Path(__file__).resolve().parents[1]


def test_partial_trace_of_bell_state_is_maximally_mixed():
    bell = np.array([1.0, 0.0, 0.0, 1.0], dtype=np.complex128) / math.sqrt(2.0)
    reduced = partial_trace(density_matrix(bell), (2, 2), keep=(0,))
    assert trace_distance(reduced, np.eye(2) / 2.0) < 1e-14


@pytest.mark.parametrize(
    "theta,phi",
    [
        (0.0, 0.0),
        (math.pi, 0.0),
        (math.pi / 2.0, 0.0),
        (math.pi / 2.0, math.pi / 2.0),
        (1.1, 0.7),
    ],
)
def test_no_hiding_audit_recovers_arbitrary_qubit(theta: float, phi: float):
    audit = audit_no_hiding(theta, phi)
    assert audit.passed, audit.summary()
    assert audit.system_bleaching_trace_distance < 1e-12
    assert audit.channel_bleaching_trace_distance < 1e-12
    assert audit.recovery_fidelity == pytest.approx(1.0, abs=1e-12)
    assert audit.bell_pair_fidelity == pytest.approx(1.0, abs=1e-12)
    assert audit.system_entropy == pytest.approx(1.0, abs=1e-12)
    assert audit.recovery_entropy == pytest.approx(0.0, abs=1e-12)
    assert audit.environment_entropy == pytest.approx(1.0, abs=1e-12)
    assert audit.mutual_information_system_environment == pytest.approx(2.0, abs=1e-12)
    assert audit.mutual_information_system_recovery == pytest.approx(0.0, abs=1e-12)


def test_suite_is_deterministic_and_input_independent():
    first = run_no_hiding_suite(random_count=5, seed=1234)
    second = run_no_hiding_suite(random_count=5, seed=1234)
    assert first == second
    assert first.passed
    assert first.case_count == 11
    assert first.maximum_system_dependence < 1e-12
    assert first.minimum_recovery_fidelity == pytest.approx(1.0, abs=1e-12)
    assert first.maximum_bloch_error < 1e-12


def test_identity_circuit_does_not_bleach_generic_input():
    psi = qubit_state(1.1, 0.7)
    zero = np.array([1.0, 0.0], dtype=np.complex128)
    state = np.kron(np.kron(psi, zero), zero)
    rho_system = partial_trace(density_matrix(state), (2, 2, 2), keep=(0,))
    assert trace_distance(rho_system, np.eye(2) / 2.0) > 0.49


def test_no_hiding_unitary_and_provider_sampling():
    unitary = no_hiding_unitary()
    assert np.linalg.norm(unitary.conj().T @ unitary - np.eye(8)) < 1e-12
    state = output_state(1.1, 0.7)
    provider = LocalStatevectorProvider()
    result = provider.execute(
        QuantumExecutionRequest("sample_statevector", tuple(state), shots=1000, seed=44)
    )
    assert result.counts is not None
    assert sum(result.counts.values()) == 1000
    assert set(result.counts) <= {"000", "001", "110", "111"}


def test_runner_emits_evidence_bundle(tmp_path: Path):
    output = tmp_path / "infogap"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_no_hiding.py"),
            "--random-count",
            "2",
            "--shots",
            "256",
            "--output-dir",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert summary["suite"]["passed"]
    assert summary["selected"]["recovery_fidelity"] == pytest.approx(1.0)
    assert (output / "cases.csv").exists()
    assert (output / "no_hiding_flow.svg").exists()


def test_complete_experience_contains_no_hiding_scene():
    script = ROOT / "scripts" / "generate_foundry_experience_complete.py"
    spec = importlib.util.spec_from_file_location("complete_infogap_test", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    dataset = module.build_dataset()
    ids = [scene["id"] for scene in dataset["scenes"]]
    assert dataset["schema"] == "gaugegap.foundry_experience.v4"
    assert "no-hiding" in ids
    assert ids.index("no-hiding") == ids.index("standard-model-anomalies") + 1
    assert len(ids) == 10
    scene = next(scene for scene in dataset["scenes"] if scene["id"] == "no-hiding")
    assert scene["suite"]["passed"]
    assert scene["selected"]["recovery_fidelity"] == pytest.approx(1.0)
