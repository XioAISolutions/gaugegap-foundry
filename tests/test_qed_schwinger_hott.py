import math

import numpy as np

from gaugegap.cohesive_gauge import audit_gauge_coherence
from gaugegap.qed_one_loop import (
    QEDParameters,
    audit_qed,
    pauli_form_factor,
    vacuum_polarization_scalar,
    vacuum_polarization_tensor,
)
from gaugegap.schwinger_model import (
    SchwingerConfig,
    build_projected_hamiltonian,
    enumerate_physical_basis,
    gauss_residuals,
    solve_schwinger,
)


def test_qed_vacuum_polarization_is_subtracted_and_transverse():
    params = QEDParameters(quadrature_order=96)
    assert vacuum_polarization_scalar(0.0, params) == 0.0
    q = np.array([0.7, -0.2, 0.4, 0.1])
    tensor = vacuum_polarization_tensor(q, params)
    assert np.linalg.norm(q @ tensor) < 1e-14


def test_qed_pauli_zero_momentum_and_ward_audit():
    params = QEDParameters(quadrature_order=96)
    expected = params.alpha / (2.0 * math.pi)
    assert abs(pauli_form_factor(0.0, params) - expected) < 1e-14
    audit = audit_qed(params=params)
    assert audit.passed
    assert audit.ward_takahashi_residual < 1e-12


def test_schwinger_basis_is_exact_gauss_sector():
    config = SchwingerConfig(n_sites=4, flux_truncation=2)
    basis = enumerate_physical_basis(config)
    assert len(basis) == 6
    assert all(all(value == 0 for value in gauss_residuals(state, config)) for state in basis)


def test_schwinger_projected_hamiltonian_is_hermitian_and_closed():
    config = SchwingerConfig(n_sites=4, flux_truncation=2)
    hamiltonian, basis, audit = build_projected_hamiltonian(config)
    assert hamiltonian.shape == (len(basis), len(basis))
    assert np.allclose(hamiltonian, hamiltonian.conj().T)
    assert audit.passed
    assert audit.transition_leakage_count == 0


def test_schwinger_solution_is_deterministic():
    config = SchwingerConfig(n_sites=4, flux_truncation=2, fermion_mass=0.2)
    first = solve_schwinger(config)
    second = solve_schwinger(config)
    assert first == second
    assert first.spectral_gap > 0.0
    assert abs(sum(first.charge_density)) < 1e-12


def test_finite_gauge_groupoid_coherence():
    certificate = audit_gauge_coherence()
    assert certificate.passed
    assert certificate.observable_transport_residual < 1e-12
