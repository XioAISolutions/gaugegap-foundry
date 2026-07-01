"""Tests for the NetGap noise layer (netgap-0006 channels, netgap-0007 distribution).

Exact CPTP channel facts: amplitude/phase/depolarizing channels are trace-preserving;
the average fidelity is (2 F_e + 1)/3 and beats the classical 2/3 bound exactly at its
threshold; and entanglement distributed through a lossy+noisy link is distillable while
its singlet fraction exceeds 1/2, with discharged certificates.
"""
from __future__ import annotations

import numpy as np
import pytest

from gaugegap.quantum.quantum_channel import (
    amplitude_damping_kraus,
    average_fidelity,
    beats_classical,
    channel_on_bell,
    depolarizing_kraus,
    distribute_entanglement,
    emit_advantage_certificate,
    emit_distillability_certificate,
    entanglement_fidelity,
    is_trace_preserving,
    phase_damping_kraus,
)


@pytest.mark.parametrize(
    "kraus",
    [amplitude_damping_kraus(0.3), phase_damping_kraus(0.4), depolarizing_kraus(0.5)],
)
def test_channels_are_trace_preserving(kraus):
    assert is_trace_preserving(kraus)


def test_channel_on_bell_is_a_valid_density_matrix():
    rho = channel_on_bell(amplitude_damping_kraus(0.3))
    assert np.isclose(np.trace(rho).real, 1.0)
    assert np.allclose(rho, rho.conj().T)
    assert np.min(np.linalg.eigvalsh(rho).real) > -1e-9


def test_identity_channel_has_unit_fidelity():
    assert entanglement_fidelity(amplitude_damping_kraus(0.0)) == pytest.approx(1.0)
    assert average_fidelity(amplitude_damping_kraus(0.0)) == pytest.approx(1.0)


def test_average_fidelity_relation_and_classical_bound():
    for kraus in (amplitude_damping_kraus(0.25), depolarizing_kraus(0.2)):
        f_e = entanglement_fidelity(kraus)
        assert average_fidelity(kraus) == pytest.approx((2 * f_e + 1) / 3)
    # Depolarizing beats the classical bound iff p < 2/3.
    assert beats_classical(depolarizing_kraus(0.66))
    assert not beats_classical(depolarizing_kraus(0.67))


def test_full_amplitude_damping_hits_the_classical_floor():
    # gamma = 1 sends everything to |0>: F_avg = 1/2 < 2/3.
    assert average_fidelity(amplitude_damping_kraus(1.0)) == pytest.approx(0.5)
    assert not beats_classical(amplitude_damping_kraus(1.0))


def test_entanglement_distribution_degrades_monotonically():
    clean = distribute_entanglement(0.9, 0.0, 0.0)
    noisy = distribute_entanglement(0.9, 0.3, 0.2)
    assert clean["singlet_fraction"] == pytest.approx(1.0)
    assert clean["distillable"] and noisy["distillable"]
    assert noisy["singlet_fraction"] < clean["singlet_fraction"]
    assert noisy["concurrence"] < clean["concurrence"]
    assert noisy["raw_distribution_rate"] < clean["raw_distribution_rate"]


def test_distribution_rate_scales_with_transmissivity():
    high = distribute_entanglement(0.9, 0.1, 0.05)
    low = distribute_entanglement(0.3, 0.1, 0.05)
    assert high["singlet_fraction"] == low["singlet_fraction"]  # conditional state is η-independent
    assert low["raw_distribution_rate"] < high["raw_distribution_rate"]


def test_certificates_have_no_holes():
    lean, coq = emit_advantage_certificate("amp", 0.9, 0.933)
    assert "quantum_advantage" in lean and "quantum_advantage" in coq
    assert "sorry" not in lean.lower() and "admitted" not in coq.lower()
    dlean, dcoq = emit_distillability_certificate("link", 0.9)
    assert "distillable_margin" in dlean and "distillable_margin" in dcoq
    assert "sorry" not in dlean.lower() and "admitted" not in dcoq.lower()
