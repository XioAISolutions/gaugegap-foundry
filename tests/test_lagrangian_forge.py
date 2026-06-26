from __future__ import annotations

from dataclasses import replace

import pytest

from gaugegap.interaction_graph import build_interaction_graph
from gaugegap.lagrangian_audit import audit_standard_model
from gaugegap.standard_model_catalog import (
    InteractionSpec,
    standard_model_catalog,
    tree_level_observables,
)


def test_standard_model_catalog_is_complete_and_deterministic():
    catalog = standard_model_catalog()
    assert catalog.gauge_group == ("SU(3)c", "SU(2)L", "U(1)Y")
    assert len(catalog.sectors) == 8
    assert len(catalog.fields) >= 25
    assert len(catalog.interactions) >= 30
    assert catalog.summary() == standard_model_catalog().summary()
    assert "blackboard" in catalog.source_note.lower()
    assert "canonical" in catalog.source_note.lower()


def test_lagrangian_audit_passes_for_canonical_catalog():
    audit = audit_standard_model(standard_model_catalog())
    assert audit.passed, audit.summary()
    assert not audit.charge_violations
    assert not audit.unknown_references
    assert not audit.nonrenormalizable_terms
    assert all(check.passed for check in audit.checks)


def test_audit_fails_closed_on_charge_violation():
    catalog = standard_model_catalog()
    bad = InteractionSpec(
        interaction_id="bad-charge",
        label="deliberate invalid vertex",
        sector_id="electroweak_gauge",
        fields=("w_plus", "w_plus", "photon"),
        coupling="e",
        operator_dimension=4,
        parent_term="electroweak_gauge",
    )
    invalid = replace(catalog, interactions=catalog.interactions + (bad,))
    audit = audit_standard_model(invalid)
    assert not audit.passed
    assert any(item.startswith("bad-charge:") for item in audit.charge_violations)


def test_interaction_graph_resolves_every_vertex():
    catalog = standard_model_catalog()
    graph = build_interaction_graph(catalog)
    assert graph == build_interaction_graph(catalog)
    assert graph["summary"]["field_nodes"] == len(catalog.fields)
    assert graph["summary"]["interaction_hyperedges"] == len(catalog.interactions)
    assert all(edge["charge_sum_thirds"] == 0 for edge in graph["hyperedges"])
    node_ids = {node["id"] for node in graph["nodes"]}
    assert all(set(edge["fields"]) <= node_ids for edge in graph["hyperedges"])


def test_tree_level_electroweak_relations_have_massless_photon():
    values = tree_level_observables()
    assert values["m_w"] == pytest.approx(80.39, rel=0.01)
    assert values["m_z"] == pytest.approx(91.19, rel=0.01)
    assert values["m_h"] == pytest.approx(125.1, rel=0.02)
    assert values["photon_mass_squared_residual"] < 1e-9
    assert values["mixing_orthogonality_residual"] < 1e-12
    assert 0.0 < values["sin2_theta_w"] < 1.0
