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
    certified_gell_mann_nishijima,
    certified_gmo_residual_model,
    certified_isospin_ratios,
    certified_meson_gmo,
    certified_moment_predictions,
    certified_moment_relations,
    certified_axial_fd,
    certified_cabibbo_angle,
    certified_cabibbo_universality,
    certified_ckm_unitarity,
    certified_fk_fpi_su3_breaking,
    certified_hyperon_axial,
    certified_vus_determinations,
    certified_vus_vud_consistency,
    certified_octet_spectrum,
    certified_omega_prediction,
    certified_quark_moments,
    certified_relations_battery,
    certified_sigma_lambda_transition,
    certified_su3_decompositions,
    certified_vector_mixing,
    certified_vector_quark_content,
    decuplet_weight_diagram_svg,
    gmo_residual_from_masses,
    octet_weight_diagram_svg,
    su3_dim,
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


def test_vector_ideal_mixing():
    rels = certified_vector_quark_content()
    assert len(rels) == 2
    for r in rels:
        assert r.rel_percent < 3.0  # ideal mixing holds to ~1%
    # A real octet-singlet mixing angle requires t^2 > 0.
    assert float(certified_vector_mixing()["t_sq"].lower) > 0


def test_quark_moments_and_predictions():
    q = certified_quark_moments()
    assert float(q["mu_u"].midpoint()) > 0 > float(q["mu_d"].midpoint())
    preds = certified_moment_predictions()
    assert len(preds) == 4
    # Quark-model octet moments are right to within ~25%.
    for r in preds:
        assert r.rel_percent < 30.0


def test_moment_ratio_and_sigma0():
    rels = certified_moment_relations()
    ratio = next(r for r in rels if "mu_p/mu_n" in r.name)
    # Measured ratio is near -1.46, so residual from -3/2 is small and positive.
    assert 0 < float(ratio.residual.midpoint()) < 0.1


def test_sigma_lambda_transition_consistent():
    r = certified_sigma_lambda_transition()
    # SU(6) prediction agrees with the measured transition moment.
    assert r.encloses_zero


def test_isospin_ratios_exact():
    ratios = certified_isospin_ratios()
    for _name, iv, _exact in ratios:
        assert float(iv.width()) == 0.0  # exact rationals, zero width
    two_to_one = ratios[0][1]
    assert float(two_to_one.lower) == 2.0


def test_gell_mann_nishijima_exact():
    r = certified_gell_mann_nishijima()
    # Q = I3 + Y/2 holds exactly across all 17 octet+decuplet states.
    assert float(r.residual.lower) == 0.0 == float(r.residual.upper)


def test_su3_dimensions():
    assert su3_dim(0, 0) == 1
    assert su3_dim(1, 0) == 3
    assert su3_dim(1, 1) == 8
    assert su3_dim(3, 0) == 10
    assert su3_dim(2, 2) == 27


def test_su3_decompositions_exact():
    decs = certified_su3_decompositions()
    assert len(decs) == 4
    for r in decs:
        # product dimension equals the sum of summand dimensions, exactly.
        assert float(r.residual.lower) == 0.0 == float(r.residual.upper)


def test_ckm_unitarity_and_cabibbo_angle():
    u = certified_ckm_unitarity()
    # First-row unitarity holds to better than 1% (residual near zero).
    assert abs(float(u.residual.midpoint())) < 0.01
    ang = certified_cabibbo_angle()
    # Cabibbo angle is ~13 degrees.
    assert 12.0 < float(ang.midpoint()) < 14.0
    assert ang.lower <= ang.upper


def test_axial_fd_consistency():
    r = certified_axial_fd()
    # F + D should reproduce g_A to within the fit uncertainties.
    assert abs(float(r.residual.midpoint())) < 0.05


def test_hyperon_axial_predictions():
    rels = certified_hyperon_axial()
    assert len(rels) == 3
    # The Cabibbo SU(3) predictions are consistent with the measured g1/f1.
    for r in rels:
        assert r.encloses_zero


def test_vus_determinations():
    rows = certified_vus_determinations()
    assert len(rows) == 3
    for row in rows:
        # Each channel gives a Cabibbo angle near 13 degrees.
        assert 12.5 < float(row["angle_deg"].midpoint()) < 13.5
        assert row["vus"].lower <= row["vus"].upper


def test_cabibbo_universality_tension():
    u = certified_cabibbo_universality()
    # The first-row / Cabibbo-angle tension: small, negative, not enclosing zero.
    assert not u.encloses_zero
    assert abs(float(u.residual.midpoint())) < 0.01


def test_fk_fpi_su3_breaking():
    b = certified_fk_fpi_su3_breaking()
    # f_K/f_pi - 1 is about 0.19 (SU(3) breaking in decay constants).
    assert 0.15 < float(b.residual.midpoint()) < 0.22


def test_vus_vud_consistency():
    c = certified_vus_vud_consistency()
    # Kmu2 and first-row agree on |V_us/V_ud|.
    assert c.encloses_zero


def test_dashboard_builds():
    # Exercise the self-contained HTML dashboard generator (so CI catches breaks).
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from build_eightfold_dashboard import build_html

    html_doc = build_html()
    assert html_doc.startswith("<!DOCTYPE html>")
    assert html_doc.rstrip().endswith("</html>")
    for token in ("Mass-relation battery", "Cabibbo", "<svg", "tensor decompositions"):
        assert token in html_doc
