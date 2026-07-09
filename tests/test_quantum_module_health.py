"""Orphaned-module triage guard (roadmap §7.5).

Several production-quality quantum modules are not yet wired into a ``foundry
run`` pipeline. Until they are, this guard keeps them from rotting: each must stay
importable and expose its advertised entry points. It also records that
``certified_shadows`` is the canonical shadow path that supersedes the legacy
``shadow_tomography`` module.
"""
from __future__ import annotations

import importlib

import pytest

pytest.importorskip("scipy")

# (module suffix under gaugegap.quantum, one advertised public attribute)
PRODUCTION_ORPHANS = [
    ("open_system", "steady_state"),
    ("adiabatic_quantum", "adiabatic_evolution"),
    ("ergotropy", "ergotropy"),
    ("optimal_control", "grape_optimization"),
    ("advanced_qpe", "standard_qpe"),
    ("quantum_metrology", "heisenberg_limit_protocol"),
    ("advanced_hamiltonian_simulation", "first_order_trotter"),
    # Triage 2026-06: substantive but unwired modules kept under guard.
    ("circuit_optimization", "optimize_circuit"),
    ("gauge_invariant_qec", "z2_toric_code"),
    ("measurement_mitigation", "build_full_calibration_matrix"),
    ("quantum_natural_gradient", "compute_parameter_shift_gradient"),
]


def test_su2_matter_track_module_stays_healthy():
    module = importlib.import_module("gaugegap.gaugegap_su2_matter")
    assert hasattr(module, "SU2GaugeMatterLattice")
    assert hasattr(module, "run_su2_gauge_matter_sweep")


@pytest.mark.parametrize("suffix,attribute", PRODUCTION_ORPHANS)
def test_production_quantum_modules_import_and_expose_entry_points(suffix, attribute):
    module = importlib.import_module(f"gaugegap.quantum.{suffix}")
    assert hasattr(module, attribute), f"{suffix} is missing {attribute}"


def test_certified_shadows_is_the_canonical_shadow_path():
    certified = importlib.import_module("gaugegap.quantum.certified_shadows")
    assert hasattr(certified, "certified_shadow_estimate")
    # The legacy module remains importable but is superseded.
    legacy = importlib.import_module("gaugegap.quantum.shadow_tomography")
    assert legacy is not certified
