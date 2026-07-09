"""Known-answer tests for the exact single-plaquette SU(3) model (gaugegap-0006).

The physics anchors: the exact fusion dimension identity, the strong-coupling gap
(g²/2)·C₂(1,0) = (2/3)g², Wilson-loop behavior across the coupling, Gauss law by
construction (character basis), and truncation convergence.
"""
from __future__ import annotations

import numpy as np
import pytest

from gaugegap.gaugegap_su3_plaquette import (
    casimir,
    dimension,
    fuse_fundamental,
    fusion_dimension_identity,
    hamiltonian_dense,
    irrep_basis,
    solve_plaquette,
    trace_operator,
    truncation_convergence,
)


def test_known_dimensions_and_casimirs():
    assert dimension(0, 0) == 1 and dimension(1, 0) == 3 and dimension(0, 1) == 3
    assert dimension(1, 1) == 8 and dimension(3, 0) == 10  # octet, decuplet
    assert casimir(0, 0) == 0.0
    assert casimir(1, 0) == pytest.approx(4.0 / 3.0)
    assert casimir(1, 1) == pytest.approx(3.0)


def test_fusion_rule_and_dimension_identity():
    assert set(fuse_fundamental(1, 1)) == {(2, 1), (0, 2), (1, 0)}
    assert fusion_dimension_identity(max_label=8)


def test_hamiltonian_is_hermitian_and_real():
    h = hamiltonian_dense(1.0, 6)
    assert np.allclose(h, h.T)


def test_strong_coupling_gap_approaches_casimir_of_fundamental():
    result = solve_plaquette(coupling=5.0, cutoff=6)
    # Gap -> (g^2/2) C2(1,0) as g grows; at g=5 the magnetic correction is small.
    assert result.gap == pytest.approx(result.strong_coupling_gap, rel=0.02)
    # Wilson loop is tiny deep in the confining (strong-coupling) regime.
    assert result.wilson_loop_1x1 < 0.01


def test_wilson_loop_grows_toward_weak_coupling_and_stays_bounded():
    strong = solve_plaquette(3.0, 8)
    mid = solve_plaquette(1.0, 8)
    weak = solve_plaquette(0.7, 8)
    assert strong.wilson_loop_1x1 < mid.wilson_loop_1x1 < weak.wilson_loop_1x1
    assert 0.0 <= weak.wilson_loop_1x1 <= 1.0


def test_gauss_law_is_by_construction_in_the_character_basis():
    result = solve_plaquette(1.0, 4)
    assert result.gauss_law_by_construction
    assert "single-plaquette" in result.claim_boundary


def test_truncation_convergence_at_moderate_coupling():
    report = truncation_convergence(1.0, cutoffs=(3, 5, 8))
    assert report["converging"]
    # L=5 -> L=8 changes the gap by less than L=3 -> L=5 did.
    assert report["gap_differences"][-1] < 1e-3


def test_trace_operator_has_unit_fusion_multiplicities():
    m = trace_operator(4)
    assert set(np.unique(m)) <= {0.0, 1.0}
    basis = irrep_basis(4)
    singlet = basis.index((0, 0))
    fund = basis.index((1, 0))
    assert m[fund, singlet] == 1.0  # 1 ⊗ 3 = 3


def test_factory_registration_builds_and_audits():
    from gaugegap.hamiltonian_factory import build_and_audit

    artifact, audit = build_and_audit("su3-single-plaquette", coupling=1.0, cutoff=5)
    assert audit.hermitian and audit.square
    assert artifact.implementation_status == "exact_finite_truncation"
    assert artifact.metadata["gauss_law_by_construction"] is True
