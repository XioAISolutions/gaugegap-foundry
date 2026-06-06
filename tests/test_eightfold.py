"""Tests for the certified Eightfold-Way / Gell-Mann-Okubo benchmark."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.eightfold import (
    OCTET,
    PDG_DECUPLET,
    PDG_OCTET,
    OctetModel,
    certified_coleman_glashow,
    certified_constituent_quark_masses,
    certified_decuplet_spacings,
    certified_distinct_levels,
    certified_eta_mixing,
    certified_gmo_residual_model,
    certified_meson_gmo,
    certified_octet_spectrum,
    certified_omega_prediction,
    certified_relations_battery,
    decuplet_weight_diagram_svg,
    gmo_residual_from_masses,
    octet_weight_diagram_svg,
)


def test_octet_has_eight_states():
    assert len(OCTET) == 8
    assert sum(1 for s in OCTET if s.multiplet == "N") == 2
    assert sum(1 for s in OCTET if s.multiplet == "Sigma") == 3
    assert sum(1 for s in OCTET if s.multiplet == "Lambda") == 1
    assert sum(1 for s in OCTET if s.multiplet == "Xi") == 2


def test_su3_limit_is_fully_degenerate():
    # With no breaking, all eight enclosures coincide: a single cluster.
    enc = certified_octet_spectrum(OctetModel(b=0.0, c=0.0))
    clusters = certified_distinct_levels(enc)
    assert len(clusters) == 1
    assert len(clusters[0]) == 8


def test_octet_breaking_certifies_four_distinct_levels():
    # b, c != 0 splits the octet into the four isospin multiplets, each pair of
    # certified-distinct levels separated (disjoint enclosures).
    enc = certified_octet_spectrum(OctetModel())
    clusters = certified_distinct_levels(enc)
    assert len(clusters) == 4
    assert sorted(len(c) for c in clusters) == [1, 2, 2, 3]  # Lambda,N,Xi,Sigma


def test_enclosures_contain_true_levels():
    model = OctetModel()
    enc = certified_octet_spectrum(model)
    lv = model.level_intervals()
    for m in lv.values():
        target = float(m.midpoint())
        assert any(e.contains(target) for e in enc)


def test_model_gmo_residual_is_certified_zero():
    # The GMO relation is exact for an octet-transforming breaking term.
    for model in (OctetModel(), OctetModel(a=900, b=-120, c=55), OctetModel(b=-200, c=10)):
        r = certified_gmo_residual_model(model)
        assert r.lower <= 0 <= r.upper
        assert float(r.width()) < 1e-6


def test_empirical_gmo_residual_is_small_and_certified():
    r = gmo_residual_from_masses(
        PDG_OCTET["N"], PDG_OCTET["Sigma"], PDG_OCTET["Lambda"], PDG_OCTET["Xi"]
    )
    # Known GMO discrepancy is about -26 MeV (~0.6% of the ~4.5 GeV combination).
    assert -27.0 < float(r.lower) and float(r.upper) < -24.0
    scale = 3 * PDG_OCTET["Lambda"][0] + PDG_OCTET["Sigma"][0]
    assert abs(float(r.midpoint())) / scale < 0.01


def test_certified_omega_prediction():
    omega = certified_omega_prediction(PDG_DECUPLET["Sigma_star"], PDG_DECUPLET["Xi_star"])
    measured = PDG_DECUPLET["Omega"][0]
    # The famous equal-spacing prediction lands within ~0.5% of the measured mass.
    assert abs(float(omega.midpoint()) - measured) / measured < 0.01
    # Certified interval has positive but small width from the input uncertainties.
    assert 0 < float(omega.width()) < 5.0


def test_decuplet_spacings_small():
    rels = certified_decuplet_spacings()
    assert len(rels) == 2
    for r in rels:
        assert r.residual.lower <= r.residual.upper
        assert r.rel_percent < 10.0  # equal spacing holds to within ~5%


def test_meson_gmo_quadratic_residual_sign():
    r = certified_meson_gmo()
    # 4K^2 - 3eta^2 - pi^2 is positive (eta-eta' mixing) and a few percent.
    assert float(r.residual.lower) > 0
    assert 2.0 < r.rel_percent < 10.0


def test_coleman_glashow_encloses_zero():
    r = certified_coleman_glashow()
    assert r.encloses_zero
    assert abs(float(r.residual.midpoint())) < 1.0  # MeV; relation holds tightly


def test_constituent_quark_masses():
    cq = certified_constituent_quark_masses()
    assert float(cq["m_s"].lower) > float(cq["m_q"].upper)  # strange heavier
    # strange-light splitting near the decuplet spacing (~140-150 MeV).
    assert 130.0 < float(cq["m_s_minus_m_q"].midpoint()) < 160.0


def test_eta_mixing_is_consistent():
    mix = certified_eta_mixing()
    # A real mixing angle requires t^2 >= 0; certify it is strictly positive.
    assert float(mix["t_sq"].lower) > 0
    assert float(mix["m1_sq"].lower) > float(mix["m8_sq"].upper)  # singlet heavier


def test_relations_battery_shape():
    battery = certified_relations_battery()
    assert len(battery) == 5
    for r in battery:
        assert r.residual.lower <= r.residual.upper
        assert isinstance(r.name, str) and r.name


def test_weight_diagrams_render():
    for svg, label in (
        (octet_weight_diagram_svg(), "octet"),
        (decuplet_weight_diagram_svg(), "decuplet"),
    ):
        assert svg.startswith("<svg")
        assert svg.rstrip().endswith("</svg>")
    assert "Omega-" in decuplet_weight_diagram_svg()
    assert "Lambda" in octet_weight_diagram_svg()
