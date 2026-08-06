"""Frozen-threshold calibration and unseen challenge evaluation for Jump Lab v0.6.

v0.5 introduced sealed answerable and none-of-the-above cases. v0.6 removes a
remaining degree of freedom: selection score and margin thresholds are chosen on
a disjoint calibration split, committed, then frozen before an unseen test split.
The suite also includes a deceptive no-fit case that leaves the target model just
above the old 0.70 confidence gate, making threshold calibration consequential.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
from html import escape
import json
from pathlib import Path
from statistics import fmean
from typing import Any, Iterable

from .artifact import dump_artifact
from .cart_executive import CartAbductiveExecutive
from .challenge import (
    CASE_HYBRID_NO_FIT,
    CASE_RATIO_SUPPORTED,
    SealedPendulumChallengeExecutive,
)
from .contracts import Observation, content_hash
from .executive import AbductiveExecutive, ExecutiveConfig
from .pendulum_executive import PendulumOutcome

CASE_DECEPTIVE_NO_FIT = "deceptive_no_fit"
CALIBRATION_CASES = (
    CASE_RATIO_SUPPORTED,
    CASE_DECEPTIVE_NO_FIT,
    CASE_HYBRID_NO_FIT,
)
DEFAULT_CALIBRATION_SEEDS = (2101, 2102, 2103, 2104)
DEFAULT_TEST_SEEDS = (2201, 2202, 2203, 2204, 2205)
DEFAULT_SCORE_GRID = (0.70, 0.75, 0.80, 0.85, 0.90, 0.95)
DEFAULT_MARGIN_GRID = (0.05, 0.10, 0.20, 0.30)


def _rehash(artifact: dict[str, Any]) -> dict[str, Any]:
    artifact["provenance"]["artifact_hash"] = "pending"
    artifact["provenance"]["artifact_hash"] = content_hash(artifact)
    return artifact


def _rate(items: list[dict[str, Any]], field: str) -> float | None:
    if not items:
        return None
    return round(fmean(1.0 if item[field] else 0.0 for item in items), 6)


class CalibratedPendulumChallengeExecutive(SealedPendulumChallengeExecutive):
    """Extend the sealed challenge with a high-confidence deceptive no-fit case."""

    def __init__(self, *, case_kind: str, **kwargs: Any) -> None:
        if case_kind not in CALIBRATION_CASES:
            raise ValueError(f"unknown calibrated challenge case: {case_kind}")
        base_kind = (
            CASE_RATIO_SUPPORTED
            if case_kind == CASE_DECEPTIVE_NO_FIT
            else case_kind
        )
        super().__init__(case_kind=base_kind, **kwargs)
        self.case_kind = case_kind

    def _hidden_case_spec(self) -> dict[str, Any]:
        if self.case_kind != CASE_DECEPTIVE_NO_FIT:
            return super()._hidden_case_spec()
        return {
            "challenge_id": f"pendulum-{self.case_kind}-{self.seed}",
            "case_kind": self.case_kind,
            "deterministic_seed": self.seed,
            "base_world": "simple-pendulum-holdout-v0.4",
            "perturbation": {
                "action": "repeat_observation",
                "target": "right_period_sensor",
                "offset_fraction": 0.03,
                "purpose": (
                    "leave the ratio model above the legacy confidence gate while "
                    "violating one of its registered predictions"
                ),
            },
        }

    def _answer_payload(self) -> dict[str, Any]:
        if self.case_kind != CASE_DECEPTIVE_NO_FIT:
            return super()._answer_payload()
        return {
            "expected_outcome": "abstain",
            "answerable_by_registered_deck": False,
        }

    def _perturb_repeat_observation(self, observation: Observation) -> Observation:
        readings = dict(observation.sensor_readings)
        period = readings.get("period_s")
        small = readings.get("small_angle_period_s")
        if period is None or small is None:
            raise ValueError("deceptive challenge requires period sensors")
        offset = max(0.05, abs(period) * 0.03)
        readings["period_s"] = period + offset
        readings["small_angle_period_s"] = small + offset
        readings["amplitude_correction_s"] = (
            readings["period_s"] - readings["small_angle_period_s"]
        )
        return replace(
            observation,
            observation_id=observation.observation_id + "-deceptive",
            state_id=content_hash(
                {
                    "source_state_id": observation.state_id,
                    "case_kind": self.case_kind,
                    "sensor_readings": readings,
                }
            ),
            sensor_readings=readings,
        )

    def _run_intervention(
        self,
        action,
        salience_score: float,
        index: int,
    ) -> PendulumOutcome:
        outcome = super()._run_intervention(action, salience_score, index)
        if not (
            self.case_kind == CASE_DECEPTIVE_NO_FIT
            and action.action_type == "repeat_observation"
        ):
            return outcome
        observation_b = self._perturb_repeat_observation(outcome.observation_b)
        pair_match = self._period_match(outcome.observation_a, observation_b)
        return PendulumOutcome(
            evidence_ref=outcome.evidence_ref,
            action=outcome.action,
            observation_a=outcome.observation_a,
            observation_b=observation_b,
            pair_match=pair_match,
            latent_difference=outcome.latent_difference,
            scope_boundary=outcome.scope_boundary,
            observed_signature="stable_repeat" if pair_match else "unstable_repeat",
            salience_score=outcome.salience_score,
        )


def _record_from_artifact(
    artifact: dict[str, Any],
    *,
    split: str,
    policy: str,
) -> dict[str, Any]:
    metrics = artifact.get("metrics") or {}
    evaluation = artifact.get("challenge_evaluation") or {}
    submission = evaluation.get("submission_payload") or {}
    answer = evaluation.get("answer_payload") or {}
    record: dict[str, Any] = {
        "split": split,
        "policy": policy,
        "seed": artifact.get("experiment", {}).get("deterministic_seed"),
        "case_kind": metrics.get("challenge_case_kind"),
        "artifact_hash": artifact.get("provenance", {}).get("artifact_hash"),
        "expected_outcome": answer.get("expected_outcome"),
        "top_semantic_key": metrics.get("evaluator_selected_semantic_key"),
        "top_blind_id": submission.get("top_blind_id"),
        "top_score": float(submission.get("top_score", 0.0)),
        "selection_margin": float(submission.get("selection_margin", 0.0)),
        "base_discovery_complete": bool(metrics.get("discovery_complete")),
        "experiments_run": int(metrics.get("experiments_run", 0)),
        "evidence_refs": list(submission.get("evidence_refs") or []),
    }
    record["record_hash"] = content_hash(record)
    return record


def apply_frozen_threshold(
    record: dict[str, Any],
    threshold: dict[str, float],
) -> dict[str, Any]:
    accepted = bool(
        record.get("base_discovery_complete")
        and float(record.get("top_score", 0.0)) >= float(threshold["minimum_score"])
        and float(record.get("selection_margin", 0.0))
        >= float(threshold["minimum_margin"])
    )
    selected_outcome = (
        record.get("top_semantic_key") if accepted else "abstain"
    )
    expected = record.get("expected_outcome")
    correct = selected_outcome == expected
    return {
        **record,
        "selected_outcome": selected_outcome,
        "abstained": not accepted,
        "correct": correct,
        "false_discovery": bool(expected == "abstain" and accepted),
        "positive_abstention": bool(expected != "abstain" and not accepted),
    }


def score_threshold(
    records: list[dict[str, Any]],
    threshold: dict[str, float],
) -> dict[str, Any]:
    decisions = [apply_frozen_threshold(record, threshold) for record in records]
    answerable = [item for item in decisions if item["expected_outcome"] != "abstain"]
    no_fit = [item for item in decisions if item["expected_outcome"] == "abstain"]
    accepted = [item for item in decisions if not item["abstained"]]
    return {
        "minimum_score": round(float(threshold["minimum_score"]), 6),
        "minimum_margin": round(float(threshold["minimum_margin"]), 6),
        "overall_accuracy": _rate(decisions, "correct"),
        "answerable_accuracy": _rate(answerable, "correct"),
        "abstention_accuracy": _rate(no_fit, "correct"),
        "false_discovery_rate": _rate(no_fit, "false_discovery"),
        "positive_abstention_rate": _rate(answerable, "positive_abstention"),
        "coverage": round(len(accepted) / len(decisions), 6) if decisions else None,
        "selective_accuracy": _rate(accepted, "correct"),
        "decision_count": len(decisions),
    }


def choose_frozen_threshold(
    records: list[dict[str, Any]],
    *,
    score_grid: Iterable[float] = DEFAULT_SCORE_GRID,
    margin_grid: Iterable[float] = DEFAULT_MARGIN_GRID,
    maximum_false_discovery_rate: float = 0.0,
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    candidates = [
        score_threshold(
            records,
            {"minimum_score": float(score), "minimum_margin": float(margin)},
        )
        for score in score_grid
        for margin in margin_grid
    ]
    feasible = [
        item
        for item in candidates
        if item["false_discovery_rate"] is not None
        and float(item["false_discovery_rate"]) <= maximum_false_discovery_rate
    ]
    pool = feasible or candidates
    chosen = min(
        pool,
        key=lambda item: (
            -float(item["overall_accuracy"] or 0.0),
            float(item["false_discovery_rate"] or 0.0),
            float(item["positive_abstention_rate"] or 0.0),
            -float(item["coverage"] or 0.0),
            float(item["minimum_score"]),
            float(item["minimum_margin"]),
        ),
    )
    threshold = {
        "minimum_score": float(chosen["minimum_score"]),
        "minimum_margin": float(chosen["minimum_margin"]),
    }
    return threshold, candidates


def calibration_commitment_payload(report: dict[str, Any]) -> dict[str, Any]:
    calibration = report.get("calibration") or {}
    return {
        "protocol": calibration.get("protocol"),
        "calibration_seeds": calibration.get("calibration_seeds"),
        "case_kinds": calibration.get("case_kinds"),
        "candidate_grid": calibration.get("candidate_grid"),
        "maximum_false_discovery_rate": calibration.get(
            "maximum_false_discovery_rate"
        ),
        "record_hashes": calibration.get("record_hashes"),
        "chosen_threshold": calibration.get("chosen_threshold"),
        "selection_objective": calibration.get("selection_objective"),
    }


def verify_calibration_commitment(report: dict[str, Any]) -> bool:
    calibration = report.get("calibration") or {}
    return calibration.get("threshold_commitment_hash") == content_hash(
        calibration_commitment_payload(report)
    )


def _train_memory(seed: int) -> tuple[dict[str, Any], list[str]]:
    elevator = AbductiveExecutive(
        seed=seed,
        config=ExecutiveConfig(use_salience=True, early_stop=True),
    ).run()
    cart = CartAbductiveExecutive(
        seed=seed,
        config=ExecutiveConfig(use_salience=True, early_stop=True),
        salience_memory=elevator["salience_memory"]["after"],
        parent_artifact_hashes=[elevator["provenance"]["artifact_hash"]],
    ).run()
    return cart["salience_memory"]["after"], [
        elevator["provenance"]["artifact_hash"],
        cart["provenance"]["artifact_hash"],
    ]


def _annotate_calibration(
    artifact: dict[str, Any],
    *,
    split: str,
    threshold_commitment_hash: str | None,
    threshold: dict[str, float] | None,
    calibration_record_hashes: list[str],
) -> dict[str, Any]:
    artifact["calibration_protocol"] = {
        "protocol": "disjoint_frozen_threshold_calibration_v1",
        "split": split,
        "threshold_frozen_before_test": split == "test",
        "threshold_commitment_hash": threshold_commitment_hash,
        "frozen_threshold": threshold,
        "calibration_record_hashes": list(calibration_record_hashes),
        "test_answers_used_for_calibration": False,
    }
    return _rehash(artifact)


def _policy_summary(rows: list[dict[str, Any]], policy: str) -> dict[str, Any]:
    decisions = [row[policy] for row in rows]
    answerable = [item for item in decisions if item["expected_outcome"] != "abstain"]
    no_fit = [item for item in decisions if item["expected_outcome"] == "abstain"]
    accepted = [item for item in decisions if not item["abstained"]]
    return {
        "overall_accuracy": _rate(decisions, "correct"),
        "answerable_accuracy": _rate(answerable, "correct"),
        "abstention_accuracy": _rate(no_fit, "correct"),
        "false_discovery_rate": _rate(no_fit, "false_discovery"),
        "positive_abstention_rate": _rate(answerable, "positive_abstention"),
        "coverage": round(len(accepted) / len(decisions), 6) if decisions else None,
        "selective_accuracy": _rate(accepted, "correct"),
        "mean_top_score": round(
            fmean(float(item["top_score"]) for item in decisions), 6
        ) if decisions else None,
        "frozen_decision_match_rate": _rate(decisions, "decision_matches_frozen"),
    }


def _reliability_bins(rows: list[dict[str, Any]], policy: str) -> list[dict[str, Any]]:
    edges = ((0.0, 0.75), (0.75, 0.85), (0.85, 0.95), (0.95, 1.000001))
    decisions = [row[policy] for row in rows]
    result = []
    for low, high in edges:
        items = [
            item
            for item in decisions
            if low <= float(item["top_score"]) < high
        ]
        result.append(
            {
                "lower": low,
                "upper": round(high, 6),
                "count": len(items),
                "empirical_accuracy": _rate(items, "correct"),
                "acceptance_rate": (
                    round(
                        fmean(0.0 if item["abstained"] else 1.0 for item in items),
                        6,
                    )
                    if items
                    else None
                ),
            }
        )
    return result


def run_calibrated_challenge_suite(
    calibration_seeds: Iterable[int] = DEFAULT_CALIBRATION_SEEDS,
    test_seeds: Iterable[int] = DEFAULT_TEST_SEEDS,
    *,
    output_dir: str | Path | None = None,
    maximum_false_discovery_rate: float = 0.0,
) -> dict[str, Any]:
    calibration_seed_list = [int(seed) for seed in calibration_seeds]
    test_seed_list = [int(seed) for seed in test_seeds]
    if not calibration_seed_list or not test_seed_list:
        raise ValueError("calibration and test splits must both be non-empty")
    if set(calibration_seed_list) & set(test_seed_list):
        raise ValueError("calibration and test seeds must be disjoint")

    root = Path(output_dir) if output_dir is not None else None
    if root is not None:
        root.mkdir(parents=True, exist_ok=True)

    calibration_records: list[dict[str, Any]] = []
    artifact_index: list[dict[str, Any]] = []
    for seed in calibration_seed_list:
        for case_kind in CALIBRATION_CASES:
            artifact = CalibratedPendulumChallengeExecutive(
                case_kind=case_kind,
                seed=seed,
                config=ExecutiveConfig(
                    use_salience=True,
                    early_stop=True,
                    confidence_threshold=0.70,
                ),
                minimum_selection_score=0.0,
                minimum_selection_margin=-1.0,
            ).run()
            artifact = _annotate_calibration(
                artifact,
                split="calibration",
                threshold_commitment_hash=None,
                threshold=None,
                calibration_record_hashes=[],
            )
            record = _record_from_artifact(
                artifact, split="calibration", policy="cold"
            )
            calibration_records.append(record)
            if root is not None:
                path = root / "calibration" / f"seed-{seed}" / f"{case_kind}.eja.json"
                dump_artifact(artifact, path)
                artifact_index.append(
                    {
                        "split": "calibration",
                        "seed": seed,
                        "case_kind": case_kind,
                        "policy": "cold",
                        "relative_path": str(path.relative_to(root)),
                        "artifact_hash": artifact["provenance"]["artifact_hash"],
                    }
                )

    threshold, candidates = choose_frozen_threshold(
        calibration_records,
        maximum_false_discovery_rate=maximum_false_discovery_rate,
    )
    candidate_grid = {
        "minimum_scores": list(DEFAULT_SCORE_GRID),
        "minimum_margins": list(DEFAULT_MARGIN_GRID),
    }
    report: dict[str, Any] = {
        "artifact_type": "jump_lab_calibrated_challenge_suite",
        "suite_version": "0.6",
        "artifact_root": str(root) if root is not None else None,
        "calibration": {
            "protocol": "disjoint_frozen_threshold_calibration_v1",
            "calibration_seeds": calibration_seed_list,
            "case_kinds": list(CALIBRATION_CASES),
            "candidate_grid": candidate_grid,
            "maximum_false_discovery_rate": maximum_false_discovery_rate,
            "record_hashes": [item["record_hash"] for item in calibration_records],
            "chosen_threshold": threshold,
            "selection_objective": [
                "maximize overall calibration accuracy",
                "respect the maximum false-discovery constraint",
                "minimize positive abstention",
                "maximize coverage",
                "prefer the least restrictive tied threshold",
            ],
            "threshold_commitment_hash": "pending",
            "records": calibration_records,
            "candidate_scorecards": candidates,
        },
        "test": {
            "test_seeds": test_seed_list,
            "case_kinds": list(CALIBRATION_CASES),
            "answers_used_for_calibration": False,
        },
        "runs": [],
        "summary": {},
        "artifact_index": artifact_index,
        "claim_boundary": (
            "This suite freezes selection thresholds on a disjoint deterministic "
            "calibration split and evaluates them on unseen deterministic seeds. It "
            "does not establish real-world calibration, open-ended hypothesis invention, "
            "or scientific validity outside the recorded toy worlds."
        ),
    }
    report["calibration"]["threshold_commitment_hash"] = content_hash(
        calibration_commitment_payload(report)
    )
    commitment = report["calibration"]["threshold_commitment_hash"]
    record_hashes = list(report["calibration"]["record_hashes"])

    rows: list[dict[str, Any]] = []
    for seed in test_seed_list:
        trained_memory, parents = _train_memory(seed)
        for case_kind in CALIBRATION_CASES:
            configurations = {
                "cold": {
                    "config": ExecutiveConfig(
                        use_salience=True,
                        early_stop=True,
                        confidence_threshold=0.70,
                    ),
                    "memory": None,
                    "parents": [],
                },
                "warm": {
                    "config": ExecutiveConfig(
                        use_salience=True,
                        early_stop=True,
                        confidence_threshold=0.70,
                    ),
                    "memory": trained_memory,
                    "parents": parents,
                },
                "fixed": {
                    "config": ExecutiveConfig(
                        use_salience=False,
                        early_stop=True,
                        confidence_threshold=0.70,
                    ),
                    "memory": None,
                    "parents": [],
                },
            }
            policy_records: dict[str, Any] = {}
            for policy, options in configurations.items():
                artifact = CalibratedPendulumChallengeExecutive(
                    case_kind=case_kind,
                    seed=seed,
                    config=options["config"],
                    salience_memory=options["memory"],
                    parent_artifact_hashes=options["parents"],
                    minimum_selection_score=threshold["minimum_score"],
                    minimum_selection_margin=threshold["minimum_margin"],
                ).run()
                artifact = _annotate_calibration(
                    artifact,
                    split="test",
                    threshold_commitment_hash=commitment,
                    threshold=threshold,
                    calibration_record_hashes=record_hashes,
                )
                record = _record_from_artifact(
                    artifact, split="test", policy=policy
                )
                frozen = apply_frozen_threshold(record, threshold)
                actual = artifact.get("challenge_evaluation") or {}
                frozen.update(
                    {
                        "actual_selected_outcome": actual.get("selected_outcome"),
                        "actual_correct": actual.get("correct"),
                        "decision_matches_frozen": (
                            actual.get("selected_outcome")
                            == frozen["selected_outcome"]
                            and bool(actual.get("correct")) == frozen["correct"]
                        ),
                        "threshold_commitment_hash": commitment,
                    }
                )
                policy_records[policy] = frozen
                if root is not None:
                    path = (
                        root
                        / "test"
                        / f"seed-{seed}"
                        / case_kind
                        / f"{policy}.eja.json"
                    )
                    dump_artifact(artifact, path)
                    artifact_index.append(
                        {
                            "split": "test",
                            "seed": seed,
                            "case_kind": case_kind,
                            "policy": policy,
                            "relative_path": str(path.relative_to(root)),
                            "artifact_hash": artifact["provenance"]["artifact_hash"],
                        }
                    )
            rows.append(
                {
                    "seed": seed,
                    "case_kind": case_kind,
                    **policy_records,
                }
            )

    report["runs"] = rows
    report["artifact_index"] = artifact_index
    summary = {
        "calibration_case_count": len(calibration_records),
        "test_case_count": len(rows),
        "split_disjoint": not bool(
            set(calibration_seed_list) & set(test_seed_list)
        ),
        "threshold_commitment_valid": verify_calibration_commitment(report),
        "chosen_threshold": threshold,
    }
    for policy in ("cold", "warm", "fixed"):
        summary[policy] = _policy_summary(rows, policy)
        summary[policy]["reliability_bins"] = _reliability_bins(rows, policy)
    report["summary"] = summary
    report["report_hash"] = "pending"
    report["report_hash"] = content_hash(report)
    return report


def render_calibration_html(report: dict[str, Any]) -> str:
    threshold = report.get("calibration", {}).get("chosen_threshold") or {}
    candidates = "".join(
        "<tr>"
        f"<td>{escape(str(item.get('minimum_score')))}</td>"
        f"<td>{escape(str(item.get('minimum_margin')))}</td>"
        f"<td>{escape(str(item.get('overall_accuracy')))}</td>"
        f"<td>{escape(str(item.get('false_discovery_rate')))}</td>"
        f"<td>{escape(str(item.get('coverage')))}</td>"
        "</tr>"
        for item in report.get("calibration", {}).get("candidate_scorecards", [])
    )
    rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('seed')))}</td>"
        f"<td>{escape(str(row.get('case_kind')))}</td>"
        f"<td>{escape(str(row.get('cold', {}).get('selected_outcome')))}</td>"
        f"<td>{escape(str(row.get('warm', {}).get('selected_outcome')))}</td>"
        f"<td>{escape(str(row.get('fixed', {}).get('selected_outcome')))}</td>"
        f"<td>{escape(str(row.get('warm', {}).get('correct')))}</td>"
        "</tr>"
        for row in report.get("runs", [])
    )
    raw = escape(json.dumps(report, indent=2, sort_keys=True))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Jump Lab Frozen Calibration</title><style>body{{font:16px/1.5 system-ui;margin:0;background:#07111f;color:#eef5ff}}main{{width:min(1280px,94vw);margin:36px auto}}section{{background:#101d31;border:1px solid #2a405f;border-radius:16px;padding:20px;margin:16px 0}}.stats{{display:flex;gap:10px;flex-wrap:wrap}}.stat{{padding:8px 12px;border:1px solid #2a405f;border-radius:999px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:9px;border-bottom:1px solid #2a405f;text-align:left}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#07111f;padding:14px;border-radius:10px}}strong{{color:#85e8b2}}</style></head><body><main><h1>GaugeGap Jump Lab v0.6 · Frozen threshold calibration</h1><div class="stats"><span class="stat">Minimum score <strong>{escape(str(threshold.get('minimum_score')))}</strong></span><span class="stat">Minimum margin <strong>{escape(str(threshold.get('minimum_margin')))}</strong></span><span class="stat">Commitment valid <strong>{escape(str(report.get('summary', {}).get('threshold_commitment_valid')))}</strong></span><span class="stat">Warm test accuracy <strong>{escape(str(report.get('summary', {}).get('warm', {}).get('overall_accuracy')))}</strong></span></div><section><h2>Calibration grid</h2><table><thead><tr><th>Score</th><th>Margin</th><th>Accuracy</th><th>False discovery</th><th>Coverage</th></tr></thead><tbody>{candidates}</tbody></table></section><section><h2>Unseen test split</h2><table><thead><tr><th>Seed</th><th>Case</th><th>Cold</th><th>Warm</th><th>Fixed</th><th>Warm correct</th></tr></thead><tbody>{rows}</tbody></table></section><section><h2>Raw report</h2><pre>{raw}</pre></section><p><strong>Claim boundary:</strong> {escape(str(report.get('claim_boundary', 'missing')))}</p></main></body></html>"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Calibrate frozen Jump Lab selection thresholds and test them"
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
    parser.add_argument("--out-dir", default="artifacts/jump-lab-calibration")
    parser.add_argument(
        "--report",
        default="artifacts/jump-lab-calibration/calibration-suite.json",
    )
    parser.add_argument(
        "--html",
        default="artifacts/jump-lab-calibration/calibration-suite.html",
    )
    args = parser.parse_args(argv)
    calibration_seeds = [
        int(value.strip())
        for value in args.calibration_seeds.split(",")
        if value.strip()
    ]
    test_seeds = [
        int(value.strip()) for value in args.test_seeds.split(",") if value.strip()
    ]
    report = run_calibrated_challenge_suite(
        calibration_seeds,
        test_seeds,
        output_dir=args.out_dir,
        maximum_false_discovery_rate=args.max_false_discovery_rate,
    )
    destination = Path(args.report)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.html:
        html = Path(args.html)
        html.parent.mkdir(parents=True, exist_ok=True)
        html.write_text(render_calibration_html(report), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
