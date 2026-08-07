"""Finite-grammar symbolic law synthesis for Jump Lab v0.7.

v0.4-v0.6 selected among pre-registered models. v0.7 removes that fixed model
deck in one controlled lane: the system receives a committed grammar of primitive
variables, exponent tokens, and operators, then enumerates candidate power laws
from those primitives. A held-out exponent combination is absent from calibration
targets but remains expressible by the grammar.

This is bounded symbolic synthesis, not open-ended scientific hypothesis invention.
"""

from __future__ import annotations

import argparse
from html import escape
import json
from math import exp, log, sqrt
from pathlib import Path
from random import Random
from statistics import fmean
from typing import Any, Iterable

from .artifact import dump_artifact
from .contracts import content_hash

GRAMMAR_EXPONENTS = (-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0)
DEFAULT_CALIBRATION_SEEDS = (3101, 3102, 3103, 3104)
DEFAULT_TEST_SEEDS = (3201, 3202, 3203, 3204, 3205)
DEFAULT_SCORE_GRID = (0.90, 0.95, 0.97, 0.98, 0.99, 0.995)
DEFAULT_MARGIN_GRID = (0.0, 0.01, 0.05, 0.10)

CASE_LINEAR_RATIO = "linear_ratio"
CASE_INVERSE_SQUARE = "inverse_square"
CASE_CALIBRATION_NO_FIT = "calibration_no_fit"
CASE_SQRT_RATIO_HOLDOUT = "sqrt_ratio_holdout"
CASE_INVERSE_PRODUCT_HOLDOUT = "inverse_product_holdout"
CASE_TEST_NO_FIT = "test_no_fit"

CALIBRATION_CASES = (
    CASE_LINEAR_RATIO,
    CASE_INVERSE_SQUARE,
    CASE_CALIBRATION_NO_FIT,
)
TEST_CASES = (
    CASE_SQRT_RATIO_HOLDOUT,
    CASE_INVERSE_PRODUCT_HOLDOUT,
    CASE_TEST_NO_FIT,
)

_CASE_SPECS: dict[str, dict[str, Any]] = {
    CASE_LINEAR_RATIO: {
        "kind": "power_law",
        "constant": 2.5,
        "a": 1.0,
        "b": -1.0,
    },
    CASE_INVERSE_SQUARE: {
        "kind": "power_law",
        "constant": 1.75,
        "a": 1.0,
        "b": -2.0,
    },
    CASE_CALIBRATION_NO_FIT: {
        "kind": "offset_piecewise",
        "constant": 3.0,
        "a": 0.5,
        "b": -0.5,
        "switch_x": 1.5,
        "upper_multiplier": 1.08,
    },
    CASE_SQRT_RATIO_HOLDOUT: {
        "kind": "power_law",
        "constant": 6.283185307179586,
        "a": 0.5,
        "b": -0.5,
    },
    CASE_INVERSE_PRODUCT_HOLDOUT: {
        "kind": "power_law",
        "constant": 4.0,
        "a": -0.5,
        "b": -0.5,
    },
    CASE_TEST_NO_FIT: {
        "kind": "offset_piecewise",
        "constant": 5.0,
        "a": -0.5,
        "b": -0.5,
        "switch_x": 1.5,
        "upper_multiplier": 1.10,
    },
}

_X_VALUES = (0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0)
_Z_VALUES = (0.6, 0.9, 1.2, 1.8, 2.4, 3.6)


def grammar_payload() -> dict[str, Any]:
    return {
        "variables": ["x", "z"],
        "response": "y",
        "form": "C * x^a * z^b",
        "exponent_tokens": list(GRAMMAR_EXPONENTS),
        "operators": ["multiply", "power"],
        "constant_fit": "geometric_mean_ratio",
        "candidate_generation": "cartesian_enumeration_from_primitives",
        "maximum_candidates": len(GRAMMAR_EXPONENTS) ** 2,
    }


def grammar_commitment_hash() -> str:
    return content_hash(grammar_payload())


def _case_spec(case_kind: str, seed: int) -> dict[str, Any]:
    if case_kind not in _CASE_SPECS:
        raise ValueError(f"unknown synthesis case: {case_kind}")
    spec = dict(_CASE_SPECS[case_kind])
    spec.update(
        {
            "challenge_id": f"scaling-law-{case_kind}-{seed}",
            "case_kind": case_kind,
            "deterministic_seed": int(seed),
            "world": "two-variable-scaling-law-v0.7",
        }
    )
    return spec


def _target_payload(case_kind: str) -> dict[str, Any]:
    spec = _CASE_SPECS[case_kind]
    if spec["kind"] == "power_law":
        return {
            "expected_outcome": "synthesized_power_law",
            "representable_by_grammar": True,
            "target_exponents": [float(spec["a"]), float(spec["b"])],
        }
    return {
        "expected_outcome": "abstain",
        "representable_by_grammar": False,
        "target_exponents": None,
    }


def _response(spec: dict[str, Any], x: float, z: float) -> float:
    base = float(spec["constant"]) * (x ** float(spec["a"])) * (z ** float(spec["b"]))
    if spec["kind"] == "offset_piecewise" and x > float(spec["switch_x"]):
        return base * float(spec["upper_multiplier"])
    return base


def _design_points(seed: int, count: int = 9) -> list[tuple[float, float]]:
    rng = Random(int(seed))
    points = [(x, z) for x in _X_VALUES for z in _Z_VALUES]
    rng.shuffle(points)
    return points[:count]


def _measurements(case_kind: str, seed: int) -> list[dict[str, Any]]:
    spec = _case_spec(case_kind, seed)
    rows = []
    for index, (x, z) in enumerate(_design_points(seed), start=1):
        y = _response(spec, x, z)
        rows.append(
            {
                "evidence_ref": f"scale-evidence-{index:03d}",
                "x": x,
                "z": z,
                "y": y,
            }
        )
    return rows


def _fit_candidate(
    measurements: list[dict[str, Any]], a: float, b: float
) -> dict[str, Any]:
    ratios = [
        float(row["y"]) / ((float(row["x"]) ** a) * (float(row["z"]) ** b))
        for row in measurements
    ]
    fitted_constant = exp(fmean(log(value) for value in ratios))
    relative_errors = []
    for row in measurements:
        prediction = fitted_constant * (float(row["x"]) ** a) * (float(row["z"]) ** b)
        relative_errors.append(abs(prediction - float(row["y"])) / abs(float(row["y"])))
    rmse = sqrt(fmean(error * error for error in relative_errors))
    fit_score = 1.0 / (1.0 + 2.0 * rmse)
    complexity = abs(a) + abs(b) + 0.1 * int(a != 0.0) + 0.1 * int(b != 0.0)
    expression_payload = {
        "form": "C * x^a * z^b",
        "a": float(a),
        "b": float(b),
    }
    return {
        "candidate_id": content_hash(expression_payload),
        "expression": f"y = {fitted_constant:.12g} * x^{a:g} * z^{b:g}",
        "exponents": [float(a), float(b)],
        "fitted_constant": fitted_constant,
        "fit_score": round(fit_score, 12),
        "relative_rmse": round(rmse, 12),
        "max_relative_error": round(max(relative_errors), 12),
        "complexity": round(complexity, 6),
    }


def synthesize_candidates(measurements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = [
        _fit_candidate(measurements, float(a), float(b))
        for a in GRAMMAR_EXPONENTS
        for b in GRAMMAR_EXPONENTS
    ]
    return sorted(
        candidates,
        key=lambda item: (
            -float(item["fit_score"]),
            float(item["complexity"]),
            str(item["candidate_id"]),
        ),
    )


def apply_synthesis_threshold(
    record: dict[str, Any], threshold: dict[str, float]
) -> dict[str, Any]:
    accepted = bool(
        float(record["top_score"]) >= float(threshold["minimum_score"])
        and float(record["selection_margin"]) >= float(threshold["minimum_margin"])
    )
    expected = record["expected_outcome"]
    selected = "synthesized_power_law" if accepted else "abstain"
    target_pair = record.get("target_exponents")
    recovered_pair = record.get("top_exponents")
    exact_recovery = bool(
        accepted
        and target_pair is not None
        and [float(value) for value in recovered_pair] == [float(value) for value in target_pair]
    )
    correct = bool(
        (expected == "abstain" and not accepted)
        or (expected == "synthesized_power_law" and exact_recovery)
    )
    return {
        **record,
        "selected_outcome": selected,
        "accepted": accepted,
        "abstained": not accepted,
        "exact_exponent_recovery": exact_recovery,
        "correct": correct,
        "false_discovery": bool(expected == "abstain" and accepted),
        "positive_abstention": bool(expected != "abstain" and not accepted),
    }


def _rate(items: list[dict[str, Any]], field: str) -> float | None:
    if not items:
        return None
    return round(fmean(1.0 if item[field] else 0.0 for item in items), 6)


def score_synthesis_threshold(
    records: list[dict[str, Any]], threshold: dict[str, float]
) -> dict[str, Any]:
    decisions = [apply_synthesis_threshold(record, threshold) for record in records]
    positives = [item for item in decisions if item["expected_outcome"] != "abstain"]
    no_fit = [item for item in decisions if item["expected_outcome"] == "abstain"]
    accepted = [item for item in decisions if item["accepted"]]
    return {
        "minimum_score": float(threshold["minimum_score"]),
        "minimum_margin": float(threshold["minimum_margin"]),
        "overall_accuracy": _rate(decisions, "correct"),
        "positive_accuracy": _rate(positives, "correct"),
        "abstention_accuracy": _rate(no_fit, "correct"),
        "false_discovery_rate": _rate(no_fit, "false_discovery"),
        "positive_abstention_rate": _rate(positives, "positive_abstention"),
        "coverage": round(len(accepted) / len(decisions), 6) if decisions else None,
        "exact_recovery_rate": _rate(positives, "exact_exponent_recovery"),
    }


def choose_synthesis_threshold(
    records: list[dict[str, Any]],
    *,
    score_grid: Iterable[float] = DEFAULT_SCORE_GRID,
    margin_grid: Iterable[float] = DEFAULT_MARGIN_GRID,
    maximum_false_discovery_rate: float = 0.0,
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    scorecards = [
        score_synthesis_threshold(
            records,
            {"minimum_score": float(score), "minimum_margin": float(margin)},
        )
        for score in score_grid
        for margin in margin_grid
    ]
    feasible = [
        item
        for item in scorecards
        if item["false_discovery_rate"] is not None
        and float(item["false_discovery_rate"]) <= float(maximum_false_discovery_rate)
    ]
    chosen = min(
        feasible or scorecards,
        key=lambda item: (
            -float(item["overall_accuracy"] or 0.0),
            float(item["false_discovery_rate"] or 0.0),
            float(item["positive_abstention_rate"] or 0.0),
            -float(item["exact_recovery_rate"] or 0.0),
            -float(item["coverage"] or 0.0),
            float(item["minimum_score"]),
            float(item["minimum_margin"]),
        ),
    )
    return {
        "minimum_score": float(chosen["minimum_score"]),
        "minimum_margin": float(chosen["minimum_margin"]),
    }, scorecards


def _candidate_hypotheses(
    candidates: list[dict[str, Any]], measurements: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    refs = [str(row["evidence_ref"]) for row in measurements]
    result = []
    for candidate in candidates[:5]:
        result.append(
            {
                "id": candidate["candidate_id"],
                "class": "generated_symbolic_power_law",
                "statement": candidate["expression"],
                "assumptions": [
                    "positive x and z",
                    "single multiplicative constant across the measured domain",
                    "exponents drawn from the committed finite grammar",
                ],
                "falsifiers": [
                    "held-out measurements exceed the declared relative-error tolerance",
                    "a simpler generated expression achieves the same fit",
                ],
                "evidence_for": refs if float(candidate["max_relative_error"]) <= 0.05 else [],
                "evidence_against": refs if float(candidate["max_relative_error"]) > 0.05 else [],
                "statement_visible_to_agent": True,
                "generated": True,
                "exponents": candidate["exponents"],
                "fit_score": candidate["fit_score"],
            }
        )
    return result


def _verify_candidate(
    case_kind: str,
    seed: int,
    candidate: dict[str, Any],
    *,
    tolerance: float = 1e-8,
) -> dict[str, Any]:
    spec = _case_spec(case_kind, seed)
    a, b = [float(value) for value in candidate["exponents"]]
    c = float(candidate["fitted_constant"])
    probe_seed = seed + 100_003
    probes = _design_points(probe_seed, count=6)
    errors = []
    cases = []
    for x, z in probes:
        observed = _response(spec, x, z)
        predicted = c * (x ** a) * (z ** b)
        relative_error = abs(predicted - observed) / abs(observed)
        errors.append(relative_error)
        cases.append(
            {
                "x": x,
                "z": z,
                "observed_y": observed,
                "predicted_y": predicted,
                "relative_error": relative_error,
            }
        )
    max_error = max(errors)
    return {
        "verifier": "gaugegap.jump_lab.finite_grammar_holdout_verifier",
        "verdict": "supported_within_scope" if max_error <= tolerance else "refuted_within_scope",
        "probe_count": len(cases),
        "max_relative_error": max_error,
        "tolerance": tolerance,
        "cases": cases,
        "claim_boundary": (
            "The verifier checks deterministic held-out points in this synthetic scaling-law "
            "world only; it does not prove a universal physical law."
        ),
    }


def _record_from_run(
    case_kind: str,
    seed: int,
    candidates: list[dict[str, Any]],
    *,
    split: str,
) -> dict[str, Any]:
    target = _target_payload(case_kind)
    top = candidates[0]
    runner_up = candidates[1]
    record = {
        "split": split,
        "seed": int(seed),
        "case_kind": case_kind,
        "expected_outcome": target["expected_outcome"],
        "target_exponents": target["target_exponents"],
        "top_candidate_id": top["candidate_id"],
        "top_exponents": top["exponents"],
        "top_score": float(top["fit_score"]),
        "selection_margin": round(float(top["fit_score"]) - float(runner_up["fit_score"]), 12),
    }
    record["record_hash"] = content_hash(record)
    return record


def run_synthesis_case(
    case_kind: str,
    seed: int,
    *,
    split: str,
    threshold: dict[str, float],
    threshold_commitment_hash: str | None = None,
    calibration_record_hashes: list[str] | None = None,
) -> dict[str, Any]:
    measurements = _measurements(case_kind, seed)
    candidates = synthesize_candidates(measurements)
    record = _record_from_run(case_kind, seed, candidates, split=split)
    decision = apply_synthesis_threshold(record, threshold)
    spec = _case_spec(case_kind, seed)
    target_payload = _target_payload(case_kind)
    selected = candidates[0]

    candidate_axiom = None
    verification: dict[str, Any]
    deductions: list[dict[str, Any]] = []
    if decision["accepted"]:
        candidate_axiom = {
            "id": f"synthesized-scaling-law-{selected['candidate_id'].split(':')[-1][:12]}",
            "statement": (
                "Within the tested positive-input scaling domain, the response follows "
                f"{selected['expression']}."
            ),
            "assumptions": [
                "x and z are positive",
                "one multiplicative constant applies across the tested domain",
                "the finite exponent grammar contains the operative exponent pair",
            ],
            "falsifiers": [
                "held-out deterministic probes exceed the recorded relative-error tolerance",
                "new measurements require an exponent outside the committed grammar",
            ],
            "excluded_claims": [
                "universality outside the synthetic world",
                "open-ended symbolic invention",
                "causal identification from observational fit alone",
            ],
            "generated_candidate_id": selected["candidate_id"],
            "exponents": selected["exponents"],
            "fitted_constant": selected["fitted_constant"],
        }
        verification = _verify_candidate(case_kind, seed, selected)
        deductions = [
            {
                "statement": "The synthesized expression predicts held-out scaling responses.",
                "evidence_refs": [str(row["evidence_ref"]) for row in measurements],
                "verifier": verification["verifier"],
            }
        ]
    else:
        verification = {
            "verifier": "gaugegap.jump_lab.finite_grammar_abstention",
            "verdict": "not_evaluated_due_to_abstention",
            "claim_boundary": (
                "No candidate axiom was compiled because the best generated expression did "
                "not clear the frozen synthesis threshold."
            ),
        }

    trajectories = [
        {
            "evidence_ref": row["evidence_ref"],
            "intervention": {
                "action_type": "set_scaling_inputs",
                "parameters": {"x": row["x"], "z": row["z"]},
            },
            "observations": [
                {
                    "observation_id": f"obs-{row['evidence_ref']}",
                    "sensor_readings": {"x": row["x"], "z": row["z"], "y": row["y"]},
                }
            ],
        }
        for row in measurements
    ]

    artifact: dict[str, Any] = {
        "crumb_version": "1.5",
        "artifact_type": "eja_experiment",
        "experiment": {
            "id": spec["challenge_id"],
            "world": "finite-grammar-scaling-law-v0.7",
            "deterministic_seed": int(seed),
        },
        "experience": {
            "initial_observations": trajectories[:2][0]["observations"] + trajectories[:2][1]["observations"],
        },
        "surprise": {
            "type": "scaling_regularities_without_registered_model_deck",
            "description": (
                "Repeated positive-input measurements suggest a compact multiplicative law, "
                "but no full expression is pre-registered for selection."
            ),
        },
        "hypotheses": _candidate_hypotheses(candidates, measurements),
        "trajectories": trajectories,
        "synthesis_candidates": candidates,
        "candidate_axiom": candidate_axiom,
        "deductions": deductions,
        "verification": verification,
        "metrics": {
            "discovery_complete": bool(decision["accepted"]),
            "experiments_run": len(measurements),
            "winner": selected["candidate_id"],
            "winner_score": selected["fit_score"],
            "selected_outcome": decision["selected_outcome"],
            "abstained": decision["abstained"],
            "challenge_correct": decision["correct"],
            "false_discovery": decision["false_discovery"],
            "exact_exponent_recovery": decision["exact_exponent_recovery"],
            "selection_margin": decision["selection_margin"],
        },
        "synthesis_protocol": {
            "protocol": "finite_symbolic_grammar_v1",
            "split": split,
            "grammar": grammar_payload(),
            "grammar_commitment_hash": grammar_commitment_hash(),
            "case_commitment_hash": content_hash(spec),
            "target_commitment_hash": content_hash(target_payload),
            "target_visible_to_agent": False,
            "target_expression_pre_registered": False,
            "candidate_generation": "cartesian_enumeration_from_primitives",
            "generated_candidate_count": len(candidates),
            "frozen_threshold": dict(threshold),
            "threshold_commitment_hash": threshold_commitment_hash,
            "calibration_record_hashes": list(calibration_record_hashes or []),
            "test_answers_used_for_calibration": False,
        },
        "synthesis_evaluation": {
            "hidden_case_spec": spec,
            "target_payload": target_payload,
            "selected_candidate_id": selected["candidate_id"],
            "selected_exponents": selected["exponents"],
            "selected_outcome": decision["selected_outcome"],
            "accepted": decision["accepted"],
            "correct": decision["correct"],
            "exact_exponent_recovery": decision["exact_exponent_recovery"],
            "false_discovery": decision["false_discovery"],
            "positive_abstention": decision["positive_abstention"],
        },
        "provenance": {
            "generator": "gaugegap.jump_lab.run_synthesis_case",
            "hypothesis_origin": "finite_symbolic_grammar_enumeration",
            "hidden_state_exposed_to_agent": False,
            "parent_artifact_hashes": [],
            "artifact_hash": "pending",
        },
    }
    artifact["provenance"]["artifact_hash"] = content_hash(artifact)
    return artifact


def synthesis_commitment_payload(report: dict[str, Any]) -> dict[str, Any]:
    calibration = report.get("calibration") or {}
    return {
        "protocol": calibration.get("protocol"),
        "grammar_commitment_hash": report.get("grammar_commitment_hash"),
        "calibration_seeds": calibration.get("calibration_seeds"),
        "calibration_cases": calibration.get("calibration_cases"),
        "record_hashes": calibration.get("record_hashes"),
        "candidate_grid": calibration.get("candidate_grid"),
        "maximum_false_discovery_rate": calibration.get("maximum_false_discovery_rate"),
        "chosen_threshold": calibration.get("chosen_threshold"),
        "selection_objective": calibration.get("selection_objective"),
    }


def verify_synthesis_commitment(report: dict[str, Any]) -> bool:
    calibration = report.get("calibration") or {}
    return calibration.get("threshold_commitment_hash") == content_hash(
        synthesis_commitment_payload(report)
    )


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    positives = [row for row in rows if row["expected_outcome"] != "abstain"]
    no_fit = [row for row in rows if row["expected_outcome"] == "abstain"]
    accepted = [row for row in rows if row["accepted"]]
    return {
        "overall_accuracy": _rate(rows, "correct"),
        "positive_accuracy": _rate(positives, "correct"),
        "no_fit_abstention_accuracy": _rate(no_fit, "correct"),
        "false_discovery_rate": _rate(no_fit, "false_discovery"),
        "positive_abstention_rate": _rate(positives, "positive_abstention"),
        "exact_exponent_recovery_rate": _rate(positives, "exact_exponent_recovery"),
        "coverage": round(len(accepted) / len(rows), 6) if rows else None,
        "mean_top_score": round(fmean(float(row["top_score"]) for row in rows), 6)
        if rows
        else None,
    }


def run_symbolic_synthesis_suite(
    calibration_seeds: Iterable[int] = DEFAULT_CALIBRATION_SEEDS,
    test_seeds: Iterable[int] = DEFAULT_TEST_SEEDS,
    *,
    output_dir: str | Path | None = None,
    maximum_false_discovery_rate: float = 0.0,
) -> dict[str, Any]:
    calibration_seed_list = [int(seed) for seed in calibration_seeds]
    test_seed_list = [int(seed) for seed in test_seeds]
    if not calibration_seed_list or not test_seed_list:
        raise ValueError("calibration and test seed sets must both be non-empty")
    if set(calibration_seed_list) & set(test_seed_list):
        raise ValueError("calibration and test seeds must be disjoint")

    root = Path(output_dir) if output_dir is not None else None
    if root is not None:
        root.mkdir(parents=True, exist_ok=True)

    raw_threshold = {"minimum_score": 0.0, "minimum_margin": 0.0}
    calibration_records: list[dict[str, Any]] = []
    artifact_index: list[dict[str, Any]] = []
    for seed in calibration_seed_list:
        for case_kind in CALIBRATION_CASES:
            measurements = _measurements(case_kind, seed)
            candidates = synthesize_candidates(measurements)
            record = _record_from_run(case_kind, seed, candidates, split="calibration")
            calibration_records.append(record)
            artifact = run_synthesis_case(
                case_kind,
                seed,
                split="calibration",
                threshold=raw_threshold,
            )
            if root is not None:
                path = root / "calibration" / f"seed-{seed}" / f"{case_kind}.eja.json"
                dump_artifact(artifact, path)
                artifact_index.append(
                    {
                        "split": "calibration",
                        "seed": seed,
                        "case_kind": case_kind,
                        "relative_path": str(path.relative_to(root)),
                        "artifact_hash": artifact["provenance"]["artifact_hash"],
                    }
                )

    threshold, scorecards = choose_synthesis_threshold(
        calibration_records,
        maximum_false_discovery_rate=maximum_false_discovery_rate,
    )
    report: dict[str, Any] = {
        "artifact_type": "jump_lab_symbolic_synthesis_suite",
        "suite_version": "0.7",
        "artifact_root": str(root) if root is not None else None,
        "grammar": grammar_payload(),
        "grammar_commitment_hash": grammar_commitment_hash(),
        "calibration": {
            "protocol": "disjoint_frozen_synthesis_threshold_v1",
            "calibration_seeds": calibration_seed_list,
            "calibration_cases": list(CALIBRATION_CASES),
            "record_hashes": [record["record_hash"] for record in calibration_records],
            "candidate_grid": {
                "minimum_scores": list(DEFAULT_SCORE_GRID),
                "minimum_margins": list(DEFAULT_MARGIN_GRID),
            },
            "maximum_false_discovery_rate": maximum_false_discovery_rate,
            "chosen_threshold": threshold,
            "selection_objective": [
                "maximize calibration accuracy",
                "respect the maximum false-discovery constraint",
                "minimize positive abstention",
                "maximize exact exponent recovery",
                "maximize coverage",
                "prefer the least restrictive tied threshold",
            ],
            "threshold_commitment_hash": "pending",
            "records": calibration_records,
            "candidate_scorecards": scorecards,
        },
        "test": {
            "test_seeds": test_seed_list,
            "test_cases": list(TEST_CASES),
            "answers_used_for_calibration": False,
        },
        "runs": [],
        "summary": {},
        "artifact_index": artifact_index,
        "claim_boundary": (
            "This suite performs bounded symbolic synthesis inside a finite, committed power-law "
            "grammar. The held-out exponent combinations are absent from calibration targets, "
            "but the grammar itself is hand-authored. This is not open-ended scientific invention."
        ),
    }
    report["calibration"]["threshold_commitment_hash"] = content_hash(
        synthesis_commitment_payload(report)
    )
    commitment = report["calibration"]["threshold_commitment_hash"]
    calibration_hashes = list(report["calibration"]["record_hashes"])

    rows: list[dict[str, Any]] = []
    for seed in test_seed_list:
        for case_kind in TEST_CASES:
            artifact = run_synthesis_case(
                case_kind,
                seed,
                split="test",
                threshold=threshold,
                threshold_commitment_hash=commitment,
                calibration_record_hashes=calibration_hashes,
            )
            candidates = artifact["synthesis_candidates"]
            record = _record_from_run(case_kind, seed, candidates, split="test")
            decision = apply_synthesis_threshold(record, threshold)
            decision.update(
                {
                    "artifact_hash": artifact["provenance"]["artifact_hash"],
                    "verification_verdict": artifact["verification"]["verdict"],
                    "threshold_commitment_hash": commitment,
                }
            )
            rows.append(decision)
            if root is not None:
                path = root / "test" / f"seed-{seed}" / f"{case_kind}.eja.json"
                dump_artifact(artifact, path)
                artifact_index.append(
                    {
                        "split": "test",
                        "seed": seed,
                        "case_kind": case_kind,
                        "relative_path": str(path.relative_to(root)),
                        "artifact_hash": artifact["provenance"]["artifact_hash"],
                    }
                )

    calibration_pairs = {
        tuple(record["target_exponents"])
        for record in calibration_records
        if record["target_exponents"] is not None
    }
    test_pairs = {
        tuple(row["target_exponents"])
        for row in rows
        if row["target_exponents"] is not None
    }
    report["runs"] = rows
    report["artifact_index"] = artifact_index
    report["summary"] = {
        **_summary(rows),
        "split_disjoint": True,
        "threshold_commitment_valid": verify_synthesis_commitment(report),
        "grammar_commitment_valid": report["grammar_commitment_hash"] == grammar_commitment_hash(),
        "holdout_target_pairs_disjoint": calibration_pairs.isdisjoint(test_pairs),
        "calibration_target_pairs": [list(pair) for pair in sorted(calibration_pairs)],
        "test_target_pairs": [list(pair) for pair in sorted(test_pairs)],
        "generated_candidates_per_run": len(GRAMMAR_EXPONENTS) ** 2,
        "chosen_threshold": threshold,
    }
    report["report_hash"] = "pending"
    report["report_hash"] = content_hash(report)
    return report


def render_synthesis_html(report: dict[str, Any]) -> str:
    threshold = report.get("calibration", {}).get("chosen_threshold") or {}
    rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('seed')))}</td>"
        f"<td>{escape(str(row.get('case_kind')))}</td>"
        f"<td>{escape(str(row.get('top_exponents')))}</td>"
        f"<td>{escape(str(row.get('top_score')))}</td>"
        f"<td>{escape(str(row.get('selected_outcome')))}</td>"
        f"<td>{escape(str(row.get('exact_exponent_recovery')))}</td>"
        f"<td>{escape(str(row.get('correct')))}</td>"
        "</tr>"
        for row in report.get("runs", [])
    )
    raw = escape(json.dumps(report, indent=2, sort_keys=True))
    summary = report.get("summary") or {}
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Jump Lab Symbolic Synthesis</title><style>body{{font:16px/1.5 system-ui;margin:0;background:#07111f;color:#eef5ff}}main{{width:min(1280px,94vw);margin:36px auto}}section{{background:#101d31;border:1px solid #2a405f;border-radius:16px;padding:20px;margin:16px 0}}.stats{{display:flex;gap:10px;flex-wrap:wrap}}.stat{{padding:8px 12px;border:1px solid #2a405f;border-radius:999px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:9px;border-bottom:1px solid #2a405f;text-align:left}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#07111f;padding:14px;border-radius:10px}}strong{{color:#85e8b2}}</style></head><body><main><h1>GaugeGap Jump Lab v0.7 · Finite-grammar symbolic synthesis</h1><div class="stats"><span class="stat">Minimum score <strong>{escape(str(threshold.get('minimum_score')))}</strong></span><span class="stat">Exact recovery <strong>{escape(str(summary.get('exact_exponent_recovery_rate')))}</strong></span><span class="stat">No-fit abstention <strong>{escape(str(summary.get('no_fit_abstention_accuracy')))}</strong></span><span class="stat">Holdout pair disjoint <strong>{escape(str(summary.get('holdout_target_pairs_disjoint')))}</strong></span></div><section><h2>Unseen synthesis runs</h2><table><thead><tr><th>Seed</th><th>Case</th><th>Generated exponents</th><th>Score</th><th>Decision</th><th>Exact recovery</th><th>Correct</th></tr></thead><tbody>{rows}</tbody></table></section><section><h2>Raw report</h2><pre>{raw}</pre></section><p><strong>Claim boundary:</strong> {escape(str(report.get('claim_boundary', 'missing')))}</p></main></body></html>"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run finite-grammar symbolic synthesis with disjoint calibration and test splits"
    )
    parser.add_argument(
        "--calibration-seeds",
        default=",".join(str(seed) for seed in DEFAULT_CALIBRATION_SEEDS),
    )
    parser.add_argument(
        "--test-seeds",
        default=",".join(str(seed) for seed in DEFAULT_TEST_SEEDS),
    )
    parser.add_argument("--max-false-discovery-rate", type=float, default=0.0)
    parser.add_argument("--out-dir", default="artifacts/jump-lab-synthesis")
    parser.add_argument(
        "--report", default="artifacts/jump-lab-synthesis/synthesis-suite.json"
    )
    parser.add_argument(
        "--html", default="artifacts/jump-lab-synthesis/synthesis-suite.html"
    )
    args = parser.parse_args(argv)
    calibration_seeds = [
        int(value.strip()) for value in args.calibration_seeds.split(",") if value.strip()
    ]
    test_seeds = [
        int(value.strip()) for value in args.test_seeds.split(",") if value.strip()
    ]
    report = run_symbolic_synthesis_suite(
        calibration_seeds,
        test_seeds,
        output_dir=args.out_dir,
        maximum_false_discovery_rate=args.max_false_discovery_rate,
    )
    destination = Path(args.report)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.html:
        html_path = Path(args.html)
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(render_synthesis_html(report), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
