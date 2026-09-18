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
    NUCLEAR_INVENTORIES,
    SYMMETRY_TOLERANCE,
    DirectionSample,
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


def test_samples_carry_antipodal_yields_that_demonstrate_the_degeneracy():
    couplings = resolve_inventory("cryptochrome-like")
    sweep = sweep_field_directions(couplings=couplings, rate_per_second=RATE, direction_count=40)
    pairs = [(s.singlet_yield, s.antipodal_singlet_yield) for s in sweep.samples]
    assert pairs
    # Every direction agrees with its true antipode to machine precision.
    assert max(abs(a - b) for a, b in pairs) < SYMMETRY_TOLERANCE


def test_mirrored_polar_angle_is_not_the_antipode_for_a_rhombic_tensor():
    # Guards the figure's honesty: the yield depends on azimuth too, so samples
    # at mirrored polar angles are NOT antipodal pairs and must not be presented
    # as evidence of the polarity degeneracy.
    couplings = resolve_inventory("cryptochrome-like")
    sweep = sweep_field_directions(couplings=couplings, rate_per_second=RATE, direction_count=120)
    by_polar = sorted(sweep.samples, key=lambda s: s.polar_deg)
    count = len(by_polar)
    mirrored_gap = max(
        abs(by_polar[i].singlet_yield - by_polar[count - 1 - i].singlet_yield)
        for i in range(count // 2)
    )
    # The mirrored-index discrepancy is a large fraction of the whole signal.
    assert mirrored_gap > 0.1 * sweep.anisotropy


def test_loaded_inventory_avoids_the_dense_liouvillian_blowup():
    # dim 72 would need a 5184-square dense Liouvillian (~1.6 GiB of temporaries
    # and a cubic solve), so the cross-check must fall back and say so.
    report = run_radical_pair_forge(
        inventory="loaded", direction_count=12, control_direction_count=8, rate_points=(1e6,)
    )
    controls = report.controls
    assert report.hilbert_dimension == 72
    assert controls["cross_check_hilbert_dimension"] <= controls["liouvillian_dim_limit"]
    assert controls["cross_check_inventory"] == "cryptochrome-like"
    assert controls["checks"]["closed_form_and_liouvillian_yields_agree"]
    # The prompt-recombination limit still uses the selected inventory.
    assert controls["checks"]["prompt_recombination_limit_equals_one"]


def test_small_inventory_cross_checks_against_itself():
    report = run_radical_pair_forge(
        inventory="cryptochrome-like",
        direction_count=12,
        control_direction_count=8,
        rate_points=(1e6,),
    )
    assert report.controls["cross_check_inventory"] == "cryptochrome-like"
    assert report.controls["cross_check_hilbert_dimension"] == 24


def test_claim_boundary_does_not_promise_a_lifetime_window():
    from gaugegap.radical_pair_forge import CLAIM_BOUNDARY

    assert "fast-recombination cutoff" in CLAIM_BOUNDARY
    assert "lifetime window" in CLAIM_BOUNDARY  # only to disclaim it
    assert "not a lifetime window" in CLAIM_BOUNDARY


def test_anisotropy_does_not_peak_near_the_larmor_rate():
    # Without relaxation there is no window: the low-rate end is not suppressed.
    # This pins the honest claim so nobody re-adds a microsecond optimum.
    couplings = resolve_inventory("cryptochrome-like")
    slow = sweep_field_directions(couplings=couplings, rate_per_second=1e3, direction_count=40)
    larmor = sweep_field_directions(couplings=couplings, rate_per_second=1e6, direction_count=40)
    assert slow.anisotropy >= larmor.anisotropy


def test_no_measured_field_can_be_silently_unpopulated():
    # Root cause of three separate review findings: a measured quantity with a
    # scalar default can be serialized unpopulated and read as a real result.
    # Every measurement field must be required, so a forgetful code path raises.
    import dataclasses

    from gaugegap.radical_pair_forge import DirectionSweep, RatePoint

    for cls in (DirectionSample, DirectionSweep, RatePoint):
        for field in dataclasses.fields(cls):
            if field.name == "samples":
                continue  # a container, not a measurement
            assert field.default is dataclasses.MISSING, (
                f"{cls.__name__}.{field.name} has a default; measured fields must be "
                "required so they cannot be silently unpopulated"
            )


def test_sweep_does_not_publish_a_control_it_never_computed():
    # The isotropic control is a comparison between two sweeps and belongs to the
    # report, not to a single sweep.  A single sweep must not carry a control field.
    sweep = sweep_field_directions(
        couplings=resolve_inventory("cryptochrome-like"), rate_per_second=RATE, direction_count=8
    )
    payload = sweep.summary()
    assert "isotropic_control_anisotropy" not in payload
    # The real control is published once, from an actual control sweep.
    report = run_radical_pair_forge(
        direction_count=12, control_direction_count=8, rate_points=(1e6,)
    )
    assert 0.0 < report.controls["isotropic_hyperfine_anisotropy"] < SYMMETRY_TOLERANCE


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


def test_default_output_dir_follows_the_selected_inventory(tmp_path: Path):
    # A valid CLI call must never overwrite another inventory's evidence bundle.
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_rp_runner", ROOT / "scripts" / "run_radical_pair_forge.py"
    )
    runner = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(runner)

    slugs = runner.OUTPUT_SLUGS
    # Every registered inventory has its own distinct destination.
    assert set(slugs) == set(NUCLEAR_INVENTORIES)
    assert len(set(slugs.values())) == len(slugs)
    # The default inventory keeps the slug its committed bundle already uses.
    assert slugs["cryptochrome-like"] == "cryptochrome-compass"


def test_every_declared_validation_is_implemented_and_vice_versa():
    # Root cause of the registry-drift finding: validation.required in the
    # hypothesis YAML and the checks dict in code were related only by intent,
    # so the registry could declare a condition the code never evaluated. This
    # reconciles them exactly, in both directions.
    import yaml

    hypothesis = yaml.safe_load(
        (ROOT / "hypotheses" / "radicalpair-0001.yaml").read_text(encoding="utf-8")
    )
    declared = set(hypothesis["validation"]["required"])
    report = run_radical_pair_forge(
        direction_count=12, control_direction_count=8, rate_points=(1e6,)
    )
    implemented = set(report.controls["checks"])

    assert declared == implemented, (
        f"declared but not implemented: {sorted(declared - implemented)}; "
        f"implemented but not declared: {sorted(implemented - declared)}"
    )


def test_low_rate_condition_is_evaluated_even_when_the_caller_skips_that_rate():
    # A caller passing a single high rate must not be able to leave the
    # registered low-rate condition unevaluated while the report reads passed.
    report = run_radical_pair_forge(
        direction_count=12, control_direction_count=8, rate_points=(1e6,)
    )
    controls = report.controls
    assert len(report.rate_sweep) == 1  # caller's sweep really is a single point
    # ...yet the condition was still computed, from its own rate points.
    assert controls["low_rate_per_second"] < controls["larmor_comparable_rate_per_second"]
    assert controls["low_rate_anisotropy"] >= controls["larmor_comparable_anisotropy"]
    assert controls["checks"][
        "anisotropy_at_low_rate_is_not_suppressed_relative_to_the_larmor_rate"
    ]


def test_non_positive_field_is_rejected_because_magnitudes_are_published():
    for bad in (0.0, -50e-6):
        with pytest.raises(ValueError, match="must be positive"):
            run_radical_pair_forge(
                field_tesla=bad, direction_count=8, control_direction_count=6, rate_points=(1e6,)
            )


# Every phrase this track has retracted across review rounds. Each is
# affirmative by construction, so a legitimate negated mention ("not a lifetime
# window") does not match, while a reinstated claim does. The repo-level
# claim_boundary_audit passed with zero high findings while two of these were
# live in the artifacts, so track-specific prohibitions need a track-specific
# guard.
RETRACTED_PHRASES = (
    "inclination sensor",          # own avoided-language list bans affirmative "sensor"
    "is a sensor",
    "window sits near",            # no lifetime window: no relaxation is modelled
    "microsecond optimum",
    "symmetric about 90",          # the figure plots antipodal pairs, not mirrored polar angles
    "sign of the effect is robust",
    "sign of that effect is robust",
    "Three of the four",           # only three results are structural; the fourth is not
)

GUARDED_ARTIFACTS = (
    "src/gaugegap/radical_pair_forge.py",
    "scripts/run_radical_pair_forge.py",
    "tests/test_radical_pair_forge.py",
    "docs/radical-pair-forge.md",
    "hypotheses/radicalpair-0001.yaml",
)


# A retracted phrase may legitimately appear inside its own prohibition ("Do not
# read a microsecond optimum out of this"), inside a kill criterion, or inside a
# recorded retraction quoting the old wording. Those are the artifact working as
# intended, so an occurrence only counts as a violation when nothing in its
# immediate context negates or forbids it.
NEGATION_MARKERS = (
    "not ",
    "no ",
    "never",
    "avoid",
    "forbid",
    "removed",
    "retract",
    "earlier draft",
    "output claims",
    "over-claim",
    "overstate",
)


# A phrase can also be legitimised by the block it sits in rather than by its own
# sentence: an entry in an "Avoided language" list or under kill_criteria is a
# prohibition even though the bullet itself reads affirmatively.
PROHIBITION_SECTIONS = (
    "avoided language",
    "avoided:",
    "kill_criteria",
    "exclusions",
    "must not",
    "do not",
)
PROHIBITION_LOOKBACK = 14


def _is_negated(context: str) -> bool:
    lowered = context.lower()
    return any(marker in lowered for marker in NEGATION_MARKERS)


def _in_prohibition_block(lines: list[str], number: int) -> bool:
    start = max(0, number - PROHIBITION_LOOKBACK)
    window = " ".join(lines[start:number]).lower()
    return any(marker in window for marker in PROHIBITION_SECTIONS)


def test_no_retracted_claim_reappears_in_the_tracks_own_artifacts():
    offenders = []
    for relative in GUARDED_ARTIFACTS:
        if relative.endswith("test_radical_pair_forge.py"):
            continue  # this file necessarily holds the phrases as data
        lines = (ROOT / relative).read_text(encoding="utf-8").splitlines()
        for number, line in enumerate(lines):
            for phrase in RETRACTED_PHRASES:
                if phrase.lower() not in line.lower():
                    continue
                # Include the previous line: this prose is hard-wrapped, so a
                # negation can sit just above the phrase it negates.
                context = (lines[number - 1] if number else "") + " " + line
                if not _is_negated(context) and not _in_prohibition_block(lines, number):
                    offenders.append(f"{relative}:{number + 1}: {phrase!r}")
    assert not offenders, "retracted claims reappeared unnegated: " + "; ".join(offenders)


def test_the_retracted_claim_guard_actually_catches_an_affirmative_claim(tmp_path: Path):
    # A guard that never fires is worthless, and this one was written after it
    # over-triggered on legitimate negations, so prove both directions.
    affirmative = tmp_path / "affirmative.md"
    affirmative.write_text("The model is an inclination sensor.\n", encoding="utf-8")
    lines = affirmative.read_text(encoding="utf-8").splitlines()
    assert not _is_negated(lines[0])

    negated = tmp_path / "negated.md"
    negated.write_text("This is not an inclination sensor.\n", encoding="utf-8")
    assert _is_negated(negated.read_text(encoding="utf-8").splitlines()[0])

    # A bullet under an "Avoided language" heading is a prohibition even though
    # the bullet itself reads affirmatively.
    block = ["Avoided language:", "", "- a microsecond optimum"]
    assert _in_prohibition_block(block, 2)
    assert not _in_prohibition_block(["Results:", "", "- a microsecond optimum"], 2)


def test_kill_criteria_forbidding_sensor_language_are_honoured_by_the_claim_boundary():
    # The registry forbids describing the result as a sensor; the module's own
    # CLAIM_BOUNDARY must therefore only ever mention "sensor" in the negative.
    from gaugegap.radical_pair_forge import CLAIM_BOUNDARY

    lowered = CLAIM_BOUNDARY.lower()
    assert "sensor" in lowered  # it is disclaimed explicitly
    assert "not a magnetometer or sensor design" in lowered


def test_the_strength_probe_holds_tensor_shape_fixed():
    # Without this the probe confounds magnitude with shape and cannot support
    # any conclusion about coupling strength. An earlier version hand-wrote each
    # magnitude and let the transverse-to-axial ratio drift from -0.057 to -0.100.
    from gaugegap.radical_pair_forge import probe_partner_suppression

    strength = [p for p in probe_partner_suppression() if p.axis == "strength"]
    assert len(strength) >= 4
    shapes = {round(p.transverse_to_axial_ratio, 12) for p in strength}
    assert len(shapes) == 1, f"shape varies across the strength series: {shapes}"
    # And the magnitudes genuinely differ, or the series tests nothing.
    assert len({round(p.axial_mhz, 9) for p in strength}) == len(strength)


def test_partner_probe_backs_the_documented_non_monotonicity():
    # The docs quote this probe as the reason no general claim is made about the
    # direction of partner suppression, so the probe must be code, not pasted
    # shell output. These assertions pin the exact statements the prose makes.
    from gaugegap.radical_pair_forge import probe_partner_suppression

    points = {p.label: p for p in probe_partner_suppression()}
    assert len(points) == 6

    # Claim 1: no probe tensor increases the anisotropy.
    assert not any(p.increases_anisotropy for p in points.values())
    assert all(p.ratio_to_spin_free < 1.0 for p in points.values())

    # Claim 2: suppression is NOT monotonic in coupling strength, with shape and
    # orientation held fixed -- 1 MHz suppresses more than 5 MHz. This survives
    # the fixed-shape redesign, so it is a statement about strength alone.
    assert (
        points["strength-1mhz"].ratio_to_spin_free
        < points["strength-5mhz"].ratio_to_spin_free
    )
    assert (
        points["strength-0.2mhz"].ratio_to_spin_free
        > points["strength-1mhz"].ratio_to_spin_free
    )


def test_probe_is_recorded_in_the_evidence_bundle():
    report = run_radical_pair_forge(
        direction_count=12, control_direction_count=8, rate_points=(1e6,)
    )
    controls = report.controls
    assert len(controls["partner_probe"]) == 6
    assert controls["partner_probe_any_increase"] is False
    # Fixed direction count, so the recorded numbers cannot drift from the prose.
    assert controls["partner_probe_directions"] == 120


def test_each_inventory_gets_a_distinct_benchmark_id():
    # Guards the class that keeps recurring: a value fixed at construction where
    # a derived one is needed. Two inventories must never be identifiable as the
    # same run, or consumers keyed on benchmark_id conflate or overwrite them.
    ids = {}
    for inventory in sorted(NUCLEAR_INVENTORIES):
        report = run_radical_pair_forge(
            inventory=inventory, direction_count=8, control_direction_count=6, rate_points=(1e6,)
        )
        ids[inventory] = report.benchmark_id
        assert report.inventory == inventory
    assert len(set(ids.values())) == len(ids), f"benchmark_id collision: {ids}"
    assert ids["cryptochrome-like"] == "radicalpair-0001-cryptochrome-compass"
