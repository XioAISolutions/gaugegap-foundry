"""Error-budget and seed-repeatability tests (issue #12, A6)."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.error_budget import ErrorBudget, ErrorComponent  # noqa: E402
from gaugegap.seeding import child_seeds, default_seed, make_rng  # noqa: E402


# --- error budget -----------------------------------------------------------

def test_stochastic_combines_in_quadrature():
    b = ErrorBudget("gap")
    b.add("shot noise", 3.0, "statistical", "stochastic")
    b.add("sampling", 4.0, "statistical", "stochastic")
    assert math.isclose(b.stochastic_total(), 5.0)  # sqrt(3^2+4^2)
    assert b.bound_total() == 0.0
    assert math.isclose(b.total(), 5.0)


def test_bounds_add_linearly_and_total_is_conservative():
    b = ErrorBudget("gap")
    b.add("shot noise", 3.0, "statistical", "stochastic")
    b.add("truncation", 2.0, "truncation", "bound")
    b.add("model offset", 1.0, "systematic", "bound")
    assert math.isclose(b.stochastic_total(), 3.0)
    assert math.isclose(b.bound_total(), 3.0)         # 2 + 1, linear
    assert math.isclose(b.total(), 6.0)               # 3 + 3, conservative


def test_dominant_and_by_category():
    b = ErrorBudget("gap")
    b.add("a", 1.0, "statistical", "stochastic")
    b.add("b", 5.0, "truncation", "bound")
    b.add("c", 1.0, "numerical", "stochastic")
    assert b.dominant().name == "b"
    cats = b.by_category()
    assert set(cats) == {"statistical", "truncation", "numerical"}
    assert math.isclose(cats["truncation"], 5.0)


def test_error_component_rejects_bad_input():
    for bad in (-1.0, float("nan"), float("inf")):
        try:
            ErrorComponent("x", bad)
            assert False, "should reject"
        except ValueError:
            pass
    try:
        ErrorComponent("x", 1.0, category="nonsense")
        assert False
    except ValueError:
        pass


# --- seeding ---------------------------------------------------------------

def test_make_rng_is_reproducible():
    a = make_rng(7).standard_normal(5)
    b = make_rng(7).standard_normal(5)
    np.testing.assert_array_equal(a, b)
    c = make_rng(8).standard_normal(5)
    assert not np.array_equal(a, c)


def test_make_rng_passthrough_and_default():
    g = make_rng(3)
    assert make_rng(g) is g            # an existing Generator is returned unchanged
    # None uses the (reproducible) default seed.
    np.testing.assert_array_equal(
        make_rng(None).standard_normal(3), make_rng(default_seed()).standard_normal(3)
    )


def test_child_seeds_are_deterministic_and_distinct():
    s1 = child_seeds(42, 4)
    s2 = child_seeds(42, 4)
    assert s1 == s2
    assert len(set(s1)) == 4          # independent streams


# --- the fixed stochastic functions are now reproducible -------------------

def test_mass_gap_metrology_reproducible_and_no_global_pollution():
    from gaugegap.quantum import quantum_metrology as qm

    H = np.diag([1.0, -1.0])
    # Pin the global RNG, run a seeded call, confirm the global stream is untouched.
    np.random.seed(0)
    before = np.random.get_state()[1][0]
    r1 = qm.mass_gap_metrology(H, n_measurements=50, seed=99)
    r2 = qm.mass_gap_metrology(H, n_measurements=50, seed=99)
    after = np.random.get_state()[1][0]
    assert r1.parameter_estimate == r2.parameter_estimate     # reproducible
    assert before == after                                    # no global pollution


def test_crab_optimization_does_not_seed_global_numpy():
    from gaugegap.quantum import optimal_control as oc

    H_drift = np.diag([1.0, -1.0])
    H_controls = [np.array([[0.0, 1.0], [1.0, 0.0]])]
    psi0 = np.array([1.0, 0.0], dtype=complex)
    psi1 = np.array([0.0, 1.0], dtype=complex)

    np.random.seed(12345)
    sentinel = np.random.random()
    np.random.seed(12345)
    oc.crab_optimization(H_drift, H_controls, psi0, psi1, T=1.0, n_basis=3,
                         max_iterations=2, seed=7)
    # If crab still called np.random.seed(42) internally, this would differ.
    assert np.random.random() == sentinel
