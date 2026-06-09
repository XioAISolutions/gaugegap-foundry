from __future__ import annotations

from gaugegap.gaugegap_su3_pure import (
    IMPLEMENTATION_STATUS,
    SU3PureGaugeConfig,
    SU3PureGaugeLattice,
)


def test_su3_lane_is_explicitly_prototype_scaffold() -> None:
    config = SU3PureGaugeConfig(
        nx=2,
        ny=2,
        g_electric=0.5,
        g_magnetic=1.0,
        truncation=0.5,
        boundary="open",
    )
    lattice = SU3PureGaugeLattice(config)
    metadata = lattice.to_dict()

    assert metadata["implementation_status"] == IMPLEMENTATION_STATUS
    assert metadata["implementation_status"] == "prototype_scaffold"
    assert metadata["verified_complete_su3"] is False
    assert metadata["verified_gauss_law"] is False


def test_su3_gap_result_carries_prototype_boundary() -> None:
    config = SU3PureGaugeConfig(
        nx=2,
        ny=2,
        g_electric=0.5,
        g_magnetic=1.0,
        truncation=0.5,
        boundary="open",
    )
    result = SU3PureGaugeLattice(config).compute_gap()

    assert result["implementation_status"] == "prototype_scaffold"
    assert result["verified_complete_su3"] is False
    assert result["verified_gauss_law"] is False
    assert result["method"] == "prototype_exact_diagonalization"
    assert result["gap"] is not None


def test_unimplemented_su3_observables_return_status_objects() -> None:
    config = SU3PureGaugeConfig(
        nx=2,
        ny=2,
        g_electric=0.5,
        g_magnetic=1.0,
        truncation=0.5,
        boundary="open",
    )
    lattice = SU3PureGaugeLattice(config)

    wilson = lattice.compute_wilson_loop(R=1, T=1)
    string = lattice.compute_string_tension()
    polyakov = lattice.compute_polyakov_loop()
    gauge = lattice.check_gauge_invariance()

    assert wilson["status"] == "not_implemented"
    assert string["status"] == "not_implemented"
    assert polyakov["status"] == "not_implemented"
    assert gauge["gauss_law_satisfied"] == "not_implemented"
    assert gauge["verified_gauss_law"] is False
