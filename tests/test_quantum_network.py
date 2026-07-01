"""Tests for the NetGap network layer (netgap-0002..0005).

Exact finite facts: any unitary factors into an adjacent-coupler mesh that reconstructs
it to machine precision; entanglement swapping maximally entangles the outer pair for
every Bell outcome; the heralded loss budget is monotone; and the BB84 key rate has the
right secure threshold with a discharged non-negativity certificate.
"""
from __future__ import annotations

import numpy as np
import pytest

from gaugegap.quantum.quantum_network import (
    bb84_key_rate,
    binary_entropy,
    emit_loss_certificate,
    emit_qkd_certificate,
    entanglement_swap,
    lossy_switch_chain,
    mesh_reconstruction_error,
    reck_decomposition,
)


def _haar_unitary(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((n, n)) + 1j * rng.standard_normal((n, n))
    q, r = np.linalg.qr(z)
    return q @ np.diag(np.diag(r) / np.abs(np.diag(r)))


# ---- netgap-0002
@pytest.mark.parametrize("n", [2, 3, 4, 6])
def test_reck_mesh_reconstructs_any_unitary(n):
    u = _haar_unitary(n, seed=n)
    assert mesh_reconstruction_error(u) < 1e-10


def test_reck_couplers_act_on_adjacent_modes():
    dec = reck_decomposition(_haar_unitary(5, seed=1))
    assert dec.couplers
    assert all(0 <= i < dec.n_modes - 1 for i, _ in dec.couplers)


# ---- netgap-0003
def test_entanglement_swap_maximally_entangles_outer_pair():
    result = entanglement_swap()
    assert result["all_outcomes_maximally_entangled"]
    assert abs(result["total_probability"] - 1.0) < 1e-9
    for outcome in result["outcomes"].values():
        assert abs(outcome["concurrence_AD"] - 1.0) < 1e-6


# ---- netgap-0004
def test_loss_budget_is_monotone_and_heralds_perfectly():
    result = lossy_switch_chain(eta=0.9, k=5)
    assert result["heralded_fidelity"] == 1.0
    assert np.isclose(result["success_probability"], 0.9 ** 5)
    assert result["loss_is_monotone"]
    assert result["success_after_one_more_switch"] <= result["success_probability"]


def test_loss_certificate_has_no_holes():
    lean, coq = emit_loss_certificate("chain", 0.9, 0.59)
    assert "loss_monotone" in lean and "loss_monotone" in coq
    assert "sorry" not in lean.lower() and "admitted" not in coq.lower()


# ---- netgap-0005
def test_bb84_threshold_and_rate_sign():
    assert bb84_key_rate(0.0)["key_rate"] == pytest.approx(1.0)
    assert bb84_key_rate(0.05)["secure"]
    above = bb84_key_rate(0.12)
    assert not above["secure"] and above["key_rate"] < 0.0
    assert 0.108 < bb84_key_rate(0.05)["secure_threshold_qber"] < 0.112


def test_binary_entropy_endpoints_and_peak():
    assert binary_entropy(0.0) == 0.0 and binary_entropy(1.0) == 0.0
    assert binary_entropy(0.5) == pytest.approx(1.0)


def test_qkd_certificate_has_no_holes():
    lean, coq = emit_qkd_certificate("bb84", 0.28, 0.44)
    assert "secure_key" in lean and "secure_key" in coq
    assert "sorry" not in lean.lower() and "admitted" not in coq.lower()
