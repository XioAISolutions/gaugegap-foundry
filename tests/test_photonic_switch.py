"""Tests for the NetGap finite photonic quantum-switch model (netgap-0001).

Exact finite linear-optics facts: the routing fabric is unitary and realizable as a
coupler mesh, every port reaches every port, unitarity preserves inner products / norm
/ fidelity, encoding conversion round-trips exactly, and routing preserves entanglement.
"""
from __future__ import annotations

import numpy as np

from gaugegap.quantum.photonic_switch import (
    beam_splitter,
    crossbar_reachability,
    emit_switch_certificate,
    entanglement_preserved_under_local_routing,
    inner_products_preserved,
    is_unitary,
    permutation_unitary,
    realize_routing_as_mesh,
    round_trip_fidelity,
    route_state,
    state_converter,
    switch_report,
)


def test_beam_splitter_and_permutation_are_unitary():
    assert is_unitary(beam_splitter(0.37, 1.1))
    assert is_unitary(permutation_unitary((2, 0, 3, 1)))


def test_permutation_routes_each_input_to_its_output():
    routing = (2, 0, 3, 1)
    p = permutation_unitary(routing)
    for i, j in enumerate(routing):
        e_in = np.eye(4)[:, i]
        assert np.argmax(np.abs(route_state(p, e_in))) == j


def test_mesh_reconstructs_the_fabric_exactly():
    routing = (3, 1, 0, 2)
    assert np.allclose(realize_routing_as_mesh(routing), permutation_unitary(routing), atol=1e-12)


def test_crossbar_reaches_every_routing():
    report = crossbar_reachability(4)
    assert report["num_routings"] == 24
    assert report["all_routings_unitary"]
    assert report["all_routings_realized_by_mesh"]


def test_unitarity_preserves_inner_products_and_norm():
    fabric = permutation_unitary((1, 3, 0, 2))
    rng = np.random.default_rng(1)
    phi = rng.standard_normal(4) + 1j * rng.standard_normal(4)
    psi = rng.standard_normal(4) + 1j * rng.standard_normal(4)
    assert inner_products_preserved(fabric, phi, psi)
    assert np.isclose(np.linalg.norm(route_state(fabric, psi)), np.linalg.norm(psi))


def test_state_converter_round_trips_exactly():
    conv = state_converter(0.9, 0.3)
    rng = np.random.default_rng(2)
    q = rng.standard_normal(2) + 1j * rng.standard_normal(2)
    q /= np.linalg.norm(q)
    assert round_trip_fidelity(conv, q) > 1.0 - 1e-9


def test_routing_preserves_entanglement():
    result = entanglement_preserved_under_local_routing(beam_splitter(0.7, 0.4))
    assert result["preserved"]
    assert np.isclose(result["entropy_before"], np.log(2))


def test_certificate_discharges_fidelity_preservation():
    lean, coq = emit_switch_certificate("demo", fid_in=1.0, fid_out=1.0, floor=1.0)
    assert "routing_preserves_fidelity" in lean
    assert "routing_preserves_fidelity" in coq
    assert "sorry" not in lean.lower()
    assert "admitted" not in coq.lower()


def test_switch_report_is_consistent():
    r = switch_report(n_modes=4)
    assert r["fabric_unitary"]
    assert r["mesh_reconstruction_error"] < 1e-12
    assert r["inner_products_preserved"] and r["norm_preserved"]
    assert r["round_trip_fidelity"] > 1.0 - 1e-9
    assert r["entanglement"]["preserved"]
    assert "not a" in r["claim_boundary"]
