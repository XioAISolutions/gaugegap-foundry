from fractions import Fraction

from gaugegap.anomaly_audit import Hypercharges, audit, neutron_charge, proton_charge
from gaugegap.hypercharge_solver import solve


def test_standard_model_assignment_cancels_registered_anomalies_exactly():
    h = Hypercharges()
    result = audit(h)
    assert result.passes
    assert result.su3_u1 == 0
    assert result.su2_u1 == 0
    assert result.u1_cubed == 0
    assert result.gravity_u1 == 0
    assert result.weak_doublets == 12
    assert proton_charge(h) == 1
    assert neutron_charge(h) == 0


def test_small_hypercharge_perturbation_is_detected():
    h = Hypercharges(y_u=Fraction(7, 10))
    result = audit(h)
    assert not result.passes
    assert result.su3_u1 != 0
    assert result.u1_cubed != 0
    assert result.gravity_u1 != 0


def test_minimal_solver_returns_fractional_quark_charges():
    solution = solve()
    h = solution.assignment
    assert solution.status == "unique_under_assumptions"
    assert h.y_q == Fraction(1, 6)
    assert h.y_u == Fraction(2, 3)
    assert h.y_d == Fraction(-1, 3)
    assert h.y_l == Fraction(-1, 2)
    assert h.y_e == -1
    assert audit(h).passes


def test_right_neutrino_case_exposes_anomaly_free_family():
    solution = solve(include_right_neutrino=True, family_y_q=Fraction(1, 5))
    assert solution.status == "underdetermined_family"
    assert solution.degrees_of_freedom == 1
    assert solution.assignment.y_nu is not None
    assert audit(solution.assignment).passes


def test_global_su2_parity_rejects_even_color_count_per_generation():
    h = Hypercharges(colors=2, y_q=Fraction(1, 4))
    result = audit(h)
    assert result.weak_doublets == 9
    assert not result.global_su2_pass
    assert not result.passes
