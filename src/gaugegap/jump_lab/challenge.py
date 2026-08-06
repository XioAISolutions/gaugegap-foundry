"""Sealed positive and none-of-the-above challenges for Jump Lab v0.5.

The challenge lane adds a critical failure mode to the blinded pendulum benchmark:
a pre-registered model deck may contain no adequate model. The executive must
then abstain instead of compiling a false axiom. Hidden case specifications and
answer keys are committed before execution and revealed only in the evaluator
record after selection.
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
from .contracts import Observation, content_hash
from .executive import AbductiveExecutive, ExecutiveConfig
from .pendulum_executive import PendulumAbductiveExecutive, PendulumOutcome

CASE_RATIO_SUPPORTED = "ratio_supported"
CASE_HYBRID_NO_FIT = "hybrid_no_fit"
VALID_CASE_KINDS = {CASE_RATIO_SUPPORTED, CASE_HYBRID_NO_FIT}
DEFAULT_CHALLENGE_SEEDS = (1201, 1202, 1203, 1204, 1205)


def _commitment(value: Any) -> str:
    return content_hash(value)


def verify_challenge_commitments(artifact: dict[str, Any]) -> dict[str, bool]:
    """Recompute post-reveal commitments without trusting evaluator booleans."""
    protocol = artifact.get("challenge_protocol") or {}
    evaluation = artifact.get("challenge_evaluation") or {}
    hidden_spec = evaluation.get("hidden_case_spec")
    answer = evaluation.get("answer_payload")
    return {
        "case_commitment_valid": bool(
            isinstance(hidden_spec, dict)
            and protocol.get("case_commitment_hash") == _commitment(hidden_spec)
        ),
        "answer_commitment_valid": bool(
            isinstance(answer, dict)
            and protocol.get("answer_commitment_hash") == _commitment(answer)
        ),
        "answer_hidden_during_run": protocol.get("answer_visible_to_agent") is False,
    }


class SealedPendulumChallengeExecutive(PendulumAbductiveExecutive):
    """Run a committed pendulum case and permit a calibrated abstention."""

    def __init__(
        self,
        *,
        case_kind: str = CASE_RATIO_SUPPORTED,
        seed: int = 927451,
        tolerance: float = 1e-10,
        config: ExecutiveConfig | None = None,
        salience_memory: dict[str, Any] | None = None,
        parent_artifact_hashes: list[str] | None = None,
        minimum_selection_score: float = 0.70,
        minimum_selection_margin: float = 0.10,
    ) -> None:
        if case_kind not in VALID_CASE_KINDS:
            raise ValueError(f"unknown challenge case: {case_kind}")
        super().__init__(
            seed=seed,
            tolerance=tolerance,
            config=config or ExecutiveConfig(confidence_threshold=0.70),
            salience_memory=salience_memory,
            parent_artifact_hashes=parent_artifact_hashes,
        )
        self.case_kind = case_kind
        self.minimum_selection_score = float(minimum_selection_score)
        self.minimum_selection_margin = float(minimum_selection_margin)

    def _hidden_case_spec(self) -> dict[str, Any]:
        perturbation: dict[str, Any] | None = None
        if self.case_kind == CASE_HYBRID_NO_FIT:
            perturbation = {
                "action": "scale_length_and_gravity",
                "target": "right_period_sensor",
                "offset_fraction": 0.03,
                "purpose": "create mutually inconsistent deck evidence",
            }
        return {
            "challenge_id": f"pendulum-{self.case_kind}-{self.seed}",
            "case_kind": self.case_kind,
            "deterministic_seed": self.seed,
            "base_world": "simple-pendulum-holdout-v0.4",
            "perturbation": perturbation,
        }

    def _answer_payload(self) -> dict[str, Any]:
        return {
            "expected_outcome": (
                self.TARGET_KEY
                if self.case_kind == CASE_RATIO_SUPPORTED
                else "abstain"
            ),
            "answerable_by_registered_deck": self.case_kind == CASE_RATIO_SUPPORTED,
        }

    def _perturb_right_observation(self, observation: Observation) -> Observation:
        readings = dict(observation.sensor_readings)
        period = readings.get("period_s")
        small = readings.get("small_angle_period_s")
        if period is None or small is None:
            raise ValueError("challenge perturbation requires period sensors")
        offset = max(0.05, abs(period) * 0.03)
        readings["period_s"] = period + offset
        readings["small_angle_period_s"] = small + offset
        readings["amplitude_correction_s"] = (
            readings["period_s"] - readings["small_angle_period_s"]
        )
        state_id = content_hash(
            {
                "source_state_id": observation.state_id,
                "challenge": self.case_kind,
                "sensor_readings": readings,
            }
        )
        return replace(
            observation,
            observation_id=observation.observation_id + "-sealed",
            state_id=state_id,
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
            self.case_kind == CASE_HYBRID_NO_FIT
            and action.action_type == "scale_length_and_gravity"
        ):
            return outcome

        observation_b = self._perturb_right_observation(outcome.observation_b)
        pair_match = self._period_match(outcome.observation_a, observation_b)
        return PendulumOutcome(
            evidence_ref=outcome.evidence_ref,
            action=outcome.action,
            observation_a=outcome.observation_a,
            observation_b=observation_b,
            pair_match=pair_match,
            latent_difference=outcome.latent_difference,
            scope_boundary=outcome.scope_boundary,
            observed_signature="pair_matches" if pair_match else "pair_diverges",
            salience_score=outcome.salience_score,
        )

    def run(self) -> dict[str, Any]:
        hidden_spec = self._hidden_case_spec()
        answer_payload = self._answer_payload()
        artifact = super().run()

        ranked = sorted(
            artifact.get("hypotheses") or [],
            key=lambda item: (-float(item.get("score", 0.0)), str(item.get("id", ""))),
        )
        top = ranked[0] if ranked else {}
        second = ranked[1] if len(ranked) > 1 else {}
        top_score = float(top.get("score", 0.0))
        second_score = float(second.get("score", 0.0))
        margin = top_score - second_score
        base_complete = bool(artifact.get("metrics", {}).get("discovery_complete"))
        abstained = bool(
            not base_complete
            or top_score < self.minimum_selection_score
            or margin < self.minimum_selection_margin
        )
        selected_semantic_key = (
            None
            if abstained
            else artifact.get("metrics", {}).get("evaluator_selected_semantic_key")
        )
        selected_outcome = "abstain" if abstained else selected_semantic_key
        correct = selected_outcome == answer_payload["expected_outcome"]

        if abstained:
            reference_verification = artifact.get("verification")
            artifact["candidate_axiom"] = None
            artifact["verification"] = {
                "verifier": "gaugegap.jump_lab.sealed_challenge_abstention",
                "verdict": "not_evaluated_due_to_abstention",
                "reference_verification_withheld_from_selection": reference_verification,
                "claim_boundary": (
                    "No candidate axiom was accepted because the registered model deck "
                    "did not meet the selection score, margin, and evidence gates."
                ),
            }
            artifact["deductions"] = []

        evidence_refs = [
            item.get("evidence_ref")
            for item in artifact.get("trajectories") or []
            if item.get("evidence_ref")
        ]
        submission_payload = {
            "challenge_id": hidden_spec["challenge_id"],
            "selected_outcome": selected_outcome,
            "abstained": abstained,
            "top_blind_id": top.get("id"),
            "top_score": round(top_score, 6),
            "selection_margin": round(margin, 6),
            "evidence_refs": evidence_refs,
        }
        artifact["experiment"]["id"] = hidden_spec["challenge_id"]
        artifact["experiment"]["world"] = "sealed-pendulum-challenge-v0.5"
        artifact["challenge_protocol"] = {
            "protocol": "sealed_none_of_the_above_challenge_v1",
            "case_commitment_hash": _commitment(hidden_spec),
            "answer_commitment_hash": _commitment(answer_payload),
            "answer_visible_to_agent": False,
            "case_spec_visible_to_agent": False,
            "selection_rule": {
                "minimum_score": self.minimum_selection_score,
                "minimum_margin": self.minimum_selection_margin,
                "evidence_gates_required": True,
                "abstention_allowed": True,
            },
            "submission_hash": _commitment(submission_payload),
            "reveal_policy": "case specification and answer revealed only after submission",
        }
        artifact["challenge_evaluation"] = {
            "hidden_case_spec": hidden_spec,
            "answer_payload": answer_payload,
            "submission_payload": submission_payload,
            "selected_outcome": selected_outcome,
            "abstained": abstained,
            "correct": correct,
            "false_discovery": bool(
                answer_payload["expected_outcome"] == "abstain" and not abstained
            ),
            "positive_abstention": bool(
                answer_payload["expected_outcome"] != "abstain" and abstained
            ),
        }
        artifact["metrics"].update(
            {
                "challenge_case_kind": self.case_kind,
                "challenge_correct": correct,
                "abstained": abstained,
                "selection_margin": round(margin, 6),
                "selected_outcome": selected_outcome,
                "false_discovery": artifact["challenge_evaluation"]["false_discovery"],
            }
        )
        artifact["provenance"].update(
            {
                "generator": "gaugegap.jump_lab.SealedPendulumChallengeExecutive",
                "challenge_case_commitment": artifact["challenge_protocol"][
                    "case_commitment_hash"
                ],
                "challenge_answer_commitment": artifact["challenge_protocol"][
                    "answer_commitment_hash"
                ],
            }
        )
        artifact["provenance"]["artifact_hash"] = "pending"
        artifact["provenance"]["artifact_hash"] = content_hash(artifact)
        return artifact


def _metrics(artifact: dict[str, Any]) -> dict[str, Any]:
    metrics = artifact.get("metrics") or {}
    evaluation = artifact.get("challenge_evaluation") or {}
    return {
        "artifact_hash": artifact.get("provenance", {}).get("artifact_hash"),
        "case_kind": metrics.get("challenge_case_kind"),
        "experiments_run": metrics.get("experiments_run"),
        "selected_outcome": metrics.get("selected_outcome"),
        "abstained": metrics.get("abstained"),
        "correct": metrics.get("challenge_correct"),
        "false_discovery": metrics.get("false_discovery"),
        "selection_margin": metrics.get("selection_margin"),
        "policy": metrics.get("policy"),
        "commitments": verify_challenge_commitments(artifact),
        "expected_outcome": (evaluation.get("answer_payload") or {}).get(
            "expected_outcome"
        ),
    }


def run_challenge_suite(
    seeds: Iterable[int] = DEFAULT_CHALLENGE_SEEDS,
    *,
    output_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Run answerable and no-fit cases under cold, warm, and fixed policies."""
    resolved = [int(seed) for seed in seeds]
    if not resolved:
        raise ValueError("at least one seed is required")
    root = Path(output_dir) if output_dir is not None else None
    if root is not None:
        root.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    artifact_index: list[dict[str, Any]] = []
    for seed in resolved:
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
        trained_memory = cart["salience_memory"]["after"]
        parents = [
            elevator["provenance"]["artifact_hash"],
            cart["provenance"]["artifact_hash"],
        ]

        for case_kind in (CASE_RATIO_SUPPORTED, CASE_HYBRID_NO_FIT):
            runs = {
                "cold": SealedPendulumChallengeExecutive(
                    case_kind=case_kind,
                    seed=seed,
                    config=ExecutiveConfig(
                        use_salience=True,
                        early_stop=True,
                        confidence_threshold=0.70,
                    ),
                ).run(),
                "warm": SealedPendulumChallengeExecutive(
                    case_kind=case_kind,
                    seed=seed,
                    config=ExecutiveConfig(
                        use_salience=True,
                        early_stop=True,
                        confidence_threshold=0.70,
                    ),
                    salience_memory=trained_memory,
                    parent_artifact_hashes=parents,
                ).run(),
                "fixed": SealedPendulumChallengeExecutive(
                    case_kind=case_kind,
                    seed=seed,
                    config=ExecutiveConfig(
                        use_salience=False,
                        early_stop=True,
                        confidence_threshold=0.70,
                    ),
                ).run(),
            }
            if root is not None:
                case_root = root / f"seed-{seed}" / case_kind
                case_root.mkdir(parents=True, exist_ok=True)
                for policy, artifact in runs.items():
                    path = case_root / f"{policy}.eja.json"
                    dump_artifact(artifact, path)
                    artifact_index.append(
                        {
                            "seed": seed,
                            "case_kind": case_kind,
                            "policy": policy,
                            "path": str(path),
                            "hash": artifact["provenance"]["artifact_hash"],
                            "parents": artifact["provenance"].get(
                                "parent_artifact_hashes", []
                            ),
                        }
                    )
            metrics = {policy: _metrics(artifact) for policy, artifact in runs.items()}
            rows.append(
                {
                    "seed": seed,
                    "case_kind": case_kind,
                    **metrics,
                    "warm_vs_cold_experiments_saved": (
                        metrics["cold"]["experiments_run"]
                        - metrics["warm"]["experiments_run"]
                    ),
                    "warm_vs_fixed_experiments_saved": (
                        metrics["fixed"]["experiments_run"]
                        - metrics["warm"]["experiments_run"]
                    ),
                    "warm_parent_linked": all(
                        parent
                        in runs["warm"]["provenance"].get(
                            "parent_artifact_hashes", []
                        )
                        for parent in parents
                    ),
                }
            )

    policies = ("cold", "warm", "fixed")
    answerable = [row for row in rows if row["case_kind"] == CASE_RATIO_SUPPORTED]
    no_fit = [row for row in rows if row["case_kind"] == CASE_HYBRID_NO_FIT]
    summary: dict[str, Any] = {
        "seed_count": len(resolved),
        "case_count": len(rows),
        "answerable_case_count": len(answerable),
        "no_fit_case_count": len(no_fit),
        "warm_parent_link_rate": round(
            fmean(1.0 if row["warm_parent_linked"] else 0.0 for row in rows), 6
        ),
        "warm_vs_cold_mean_experiments_saved": round(
            fmean(row["warm_vs_cold_experiments_saved"] for row in rows), 6
        ),
        "warm_vs_fixed_mean_experiments_saved": round(
            fmean(row["warm_vs_fixed_experiments_saved"] for row in rows), 6
        ),
    }
    for policy in policies:
        summary[f"{policy}_overall_accuracy"] = round(
            fmean(1.0 if row[policy]["correct"] else 0.0 for row in rows), 6
        )
        summary[f"{policy}_answerable_accuracy"] = round(
            fmean(1.0 if row[policy]["correct"] else 0.0 for row in answerable), 6
        )
        summary[f"{policy}_abstention_accuracy"] = round(
            fmean(1.0 if row[policy]["correct"] else 0.0 for row in no_fit), 6
        )
        summary[f"{policy}_false_discovery_rate"] = round(
            fmean(1.0 if row[policy]["false_discovery"] else 0.0 for row in no_fit),
            6,
        )
        summary[f"{policy}_coverage"] = round(
            fmean(0.0 if row[policy]["abstained"] else 1.0 for row in rows), 6
        )
        summary[f"{policy}_commitment_valid_rate"] = round(
            fmean(
                1.0
                if all(row[policy]["commitments"].values())
                else 0.0
                for row in rows
            ),
            6,
        )

    return {
        "artifact_type": "jump_lab_sealed_challenge_suite",
        "suite_version": "0.5",
        "training_worlds": ["einstein-elevator-v0.3", "force-mass-cart-v0.3"],
        "challenge_world": "sealed-pendulum-challenge-v0.5",
        "case_kinds": [CASE_RATIO_SUPPORTED, CASE_HYBRID_NO_FIT],
        "challenge_protocol": {
            "answerable_and_none_of_the_above_cases": True,
            "pre_execution_case_commitments": True,
            "pre_execution_answer_commitments": True,
            "answer_visible_during_run": False,
            "abstention_allowed": True,
            "open_ended_abduction": False,
        },
        "runs": rows,
        "summary": summary,
        "artifact_index": artifact_index,
        "claim_boundary": (
            "This suite measures calibrated selection and abstention over a sealed, "
            "hand-authored deterministic challenge family. It does not demonstrate "
            "open-ended hypothesis invention, real-world scientific validity, or "
            "general cross-domain discovery."
        ),
    }


def render_challenge_html(report: dict[str, Any]) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('seed')))}</td>"
        f"<td>{escape(str(row.get('case_kind')))}</td>"
        f"<td>{escape(str(row.get('cold', {}).get('selected_outcome')))}</td>"
        f"<td>{escape(str(row.get('warm', {}).get('selected_outcome')))}</td>"
        f"<td>{escape(str(row.get('fixed', {}).get('selected_outcome')))}</td>"
        f"<td>{escape(str(row.get('warm', {}).get('correct')))}</td>"
        f"<td>{escape(str(row.get('warm', {}).get('false_discovery')))}</td>"
        "</tr>"
        for row in report.get("runs", [])
    )
    summary = report.get("summary") or {}
    raw = escape(json.dumps(report, indent=2, sort_keys=True))
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Jump Lab Sealed Challenge</title><style>body{{font:16px/1.5 system-ui;margin:0;background:#07111f;color:#eef5ff}}main{{width:min(1240px,94vw);margin:36px auto}}section{{background:#101d31;border:1px solid #2a405f;border-radius:16px;padding:20px;margin:16px 0}}.stats{{display:flex;gap:10px;flex-wrap:wrap}}.stat{{padding:8px 12px;border:1px solid #2a405f;border-radius:999px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:9px;border-bottom:1px solid #2a405f;text-align:left}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#07111f;padding:14px;border-radius:10px}}strong{{color:#85e8b2}}</style></head><body><main><h1>GaugeGap Jump Lab v0.5 · Sealed challenge</h1><div class="stats"><span class="stat">Cases <strong>{escape(str(summary.get('case_count')))}</strong></span><span class="stat">Warm accuracy <strong>{escape(str(summary.get('warm_overall_accuracy')))}</strong></span><span class="stat">Warm abstention accuracy <strong>{escape(str(summary.get('warm_abstention_accuracy')))}</strong></span><span class="stat">Warm false-discovery rate <strong>{escape(str(summary.get('warm_false_discovery_rate')))}</strong></span></div><section><h2>Challenge runs</h2><table><thead><tr><th>Seed</th><th>Case</th><th>Cold</th><th>Warm</th><th>Fixed</th><th>Warm correct</th><th>False discovery</th></tr></thead><tbody>{rows}</tbody></table></section><section><h2>Raw report</h2><pre>{raw}</pre></section><p><strong>Claim boundary:</strong> {escape(str(report.get('claim_boundary', 'missing')))}</p></main></body></html>"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the sealed Jump Lab challenge suite")
    parser.add_argument(
        "--seeds",
        default=",".join(str(seed) for seed in DEFAULT_CHALLENGE_SEEDS),
        help="comma-separated deterministic seeds",
    )
    parser.add_argument("--out-dir", default="artifacts/jump-lab-challenge")
    parser.add_argument("--report", default="artifacts/jump-lab-challenge.json")
    parser.add_argument("--html", default="artifacts/jump-lab-challenge.html")
    args = parser.parse_args(argv)
    seeds = [int(value.strip()) for value in args.seeds.split(",") if value.strip()]
    report = run_challenge_suite(seeds, output_dir=args.out_dir)
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    if args.html:
        html_path = Path(args.html)
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_text(render_challenge_html(report), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
