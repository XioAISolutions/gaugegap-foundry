from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest

from gaugegap.radical_pair_forge import (
    GEOMAGNETIC_FIELD_T,
    HYPERFINE_REGISTRY,
    SYMMETRY_TOLERANCE,
    build_hamiltonian,
    fibonacci_directions,
    hilbert_dims,
    polarity_residual,
    resolve_inventory,
    run_radical_pair_forge,
    singlet_projector,
    singlet_yield_closed_form,
    singlet_yield_liouvillian,
    spin_operators,
    sweep_field_directions,
    zeeman_thermal_ratio,
)

ROOT = Path(__file__).resolve().parents[1]
RATE = 1.0e6


def test_spin_operators_satisfy_su2_algebra():
    for multiplicity in (2, 3, 4):
        sx, sy, sz = spin_operators(multiplicity)
        spin = (multiplicity - 1) / 2
        casimir = sx @ sx + sy @ sy + sz @ sz
        assert np.allclose(casimir, spin * (spin + 1) * np.eye(multiplicity))
        assert np.allclose(sx @ sy - sy @ sx, 1j * sz)
        assert np.allclose(sx, sx.conj().T)


def test_singlet_projector_is_a_rank_deficient_projector():
    dims = hilbert_dims(resolve_inventory("cryptochrome-like"))
    projector = singlet_projector(dims)
    assert np.allclose(projector @ projector, projector)
    assert np.allclose(projector, projector.conj().T)
    # One electronic singlet state per nuclear configuration.
    assert np.trace(projector).real == pytest.approx(int(np.prod(dims)) / 4)


def test_anisotropic_hyperfine_gives_a_compass_and_isotropic_hyperfine_does_not():
    couplings = resolve_inventory("cryptochrome-like")
    live = sweep_field_directions(couplings=couplings, rate_per_second=RATE, direction_count=80)
    control = sweep_field_directions(
        couplings=couplings, rate_per_second=RATE, direction_count=80, isotropic=True
    )
    assert live.anisotropy > 1e-3
    # The negative control: entanglement is untouched, the compass is gone.
    assert control.anisotropy < SYMMETRY_TOLERANCE


def test_singlet_yield_is_exactly_invariant_under_field_reversal():
    couplings = resolve_inventory("cryptochrome-like")
    residual = polarity_residual(couplings=couplings, rate_per_second=RATE, direction_count=40)
    assert residual < SYMMETRY_TOLERANCE

    # Spot-check one direction against its antipode at full precision.
    projector = singlet_projector(hilbert_dims(couplings))
    direction = np.array([0.37, -0.52, 0.77])
    forward = singlet_yield_closed_form(
        build_hamiltonian(
            field_tesla=GEOMAGNETIC_FIELD_T, direction=direction, couplings=couplings
        ),
        projector,
        RATE,
    )
    reversed_ = singlet_yield_closed_form(
        build_hamiltonian(
            field_tesla=GEOMAGNETIC_FIELD_T, direction=-direction, couplings=couplings
        ),
        projector,
        RATE,
    )
    assert forward == pytest.approx(reversed_, abs=1e-12)


def test_bare_zeeman_hamiltonian_traps_the_pair_in_the_singlet():
    # With no hyperfine coupling H commutes with P_S, so nothing mixes and the
    # yield is exactly one regardless of field direction or magnitude.
    projector = singlet_projector(hilbert_dims(()))
    for direction in fibonacci_directions(8):
        for field in (GEOMAGNETIC_FIELD_T, 5e-3):
            hamiltonian = build_hamiltonian(
                field_tesla=field, direction=direction, couplings=()
            )
            # Compare the commutator to the scale of H: at 5 mT the entries are
            # ~1e8 rad/s, so an absolute tolerance would say nothing.
            commutator = hamiltonian @ projector - projector @ hamiltonian
            assert np.abs(commutator).max() / np.abs(hamiltonian).max() < 1e-12
            assert singlet_yield_closed_form(hamiltonian, projector, RATE) == pytest.approx(1.0)


def test_closed_form_matches_exact_liouvillian_solve():
    couplings = resolve_inventory("cryptochrome-like")
    projector = singlet_projector(hilbert_dims(couplings))
    hamiltonian = build_hamiltonian(
        field_tesla=GEOMAGNETIC_FIELD_T, direction=(0.3, 0.4, 0.866), couplings=couplings
    )
    closed = singlet_yield_closed_form(hamiltonian, projector, RATE)
    assert closed == pytest.approx(
        singlet_yield_liouvillian(hamiltonian, projector, RATE, RATE), abs=1e-10
    )
    # Asymmetric rates have no closed form, so they must genuinely differ, and
    # must converge back to it as the rates are brought together.
    assert singlet_yield_liouvillian(hamiltonian, projector, 2.0 * RATE, RATE) != pytest.approx(
        closed, abs=1e-6
    )
    assert singlet_yield_liouvillian(
        hamiltonian, projector, RATE * (1.0 + 1e-9), RATE
    ) == pytest.approx(closed, abs=1e-8)


def test_prompt_recombination_limit_is_unity():
    couplings = resolve_inventory("cryptochrome-like")
    projector = singlet_projector(hilbert_dims(couplings))
    hamiltonian = build_hamiltonian(
        field_tesla=GEOMAGNETIC_FIELD_T, direction=(0.0, 0.0, 1.0), couplings=couplings
    )
    assert singlet_yield_closed_form(hamiltonian, projector, 1e14) == pytest.approx(1.0, abs=1e-6)


def test_fast_recombination_collapses_the_compass():
    couplings = resolve_inventory("cryptochrome-like")
    slow = sweep_field_directions(couplings=couplings, rate_per_second=RATE, direction_count=40)
    fast = sweep_field_directions(couplings=couplings, rate_per_second=1e10, direction_count=40)
    assert fast.anisotropy < 1e-6
    assert fast.anisotropy < slow.anisotropy / 1000.0


def test_loading_the_partner_radical_suppresses_the_compass():
    spin_free = sweep_field_directions(
        couplings=resolve_inventory("spin-free-partner"), rate_per_second=RATE, direction_count=60
    )
    loaded = sweep_field_directions(
        couplings=resolve_inventory("cryptochrome-like"), rate_per_second=RATE, direction_count=60
    )
    assert spin_free.anisotropy > loaded.anisotropy
    # Hyperfine coupling on the second radical costs close to an order of magnitude.
    assert spin_free.anisotropy / loaded.anisotropy > 3.0


def test_registry_tensors_are_symmetric_and_trace_preserved_by_the_isotropic_control():
    for coupling in HYPERFINE_REGISTRY.values():
        tensor = coupling.tensor_rad_per_s()
        assert np.allclose(tensor, tensor.T)
        isotropic = coupling.tensor_rad_per_s(isotropic=True)
        assert np.trace(isotropic) == pytest.approx(np.trace(tensor))
        assert np.allclose(isotropic, np.eye(3) * np.trace(tensor) / 3.0)
        assert coupling.anisotropy_mhz > 0.0


def test_zeeman_energy_is_negligible_against_thermal_energy():
    assert zeeman_thermal_ratio(GEOMAGNETIC_FIELD_T) == pytest.approx(2.2416e-7, rel=1e-3)
    assert zeeman_thermal_ratio(5e-3) == pytest.approx(2.2416e-5, rel=1e-3)


def test_report_passes_every_registered_check():
    report = run_radical_pair_forge(
        direction_count=80, control_direction_count=30, rate_points=(1e4, 1e6, 1e8, 1e10)
    )
    assert report.passed
    assert all(report.controls["checks"].values())
    assert report.hilbert_dimension == 24
    assert report.larmor_frequency_mhz == pytest.approx(1.4012, rel=1e-3)
    assert report.relative_contrast > 0.01
    summary = report.summary()
    assert summary["claim_level"] == "reproducible_finite_result"
    assert "not a magnetometer" in summary["claim_boundary"]
    assert "samples" not in summary["sweep"]
    assert "samples" in report.summary(include_samples=True)["sweep"]


def test_unknown_inventory_fails_closed():
    with pytest.raises(ValueError, match="unknown inventory"):
        resolve_inventory("robin-eye-over-usb")


def test_runner_emits_evidence_bundle(tmp_path: Path):
    output = tmp_path / "radicalpair"
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "run_radical_pair_forge.py"),
            "--direction-count",
            "40",
            "--control-direction-count",
            "20",
            "--rate-points",
            "4",
            "--output-dir",
            str(output),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
    assert summary["passed"]
    assert summary["controls"]["polarity_residual"] < SYMMETRY_TOLERANCE
    assert len(summary["sweep"]["samples"]) == 40
    assert summary["sources"]
    assert (output / "directions.csv").exists()
    assert (output / "rate_sweep.csv").exists()
    assert (output / "radical_pair_forge.svg").exists()
