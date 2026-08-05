from gaugegap.jump_lab import (
    AbductiveExecutive,
    ExecutiveConfig,
    render_benchmark_html,
    render_discovery_html,
    run_benchmark,
)


def test_salience_policy_reaches_same_scoped_result_with_fewer_experiments():
    salience = AbductiveExecutive(
        seed=927451,
        config=ExecutiveConfig(use_salience=True, early_stop=True),
    ).run()
    baseline = AbductiveExecutive(
        seed=927451,
        config=ExecutiveConfig(use_salience=False, early_stop=True),
    ).run()

    assert salience["metrics"]["winner"] == "H4"
    assert baseline["metrics"]["winner"] == "H4"
    assert salience["metrics"]["discovery_complete"] is True
    assert baseline["metrics"]["discovery_complete"] is True
    assert salience["verification"]["verdict"] == "supported_within_scope"
    assert baseline["verification"]["verdict"] == "supported_within_scope"
    assert salience["metrics"]["experiments_run"] < baseline["metrics"]["experiments_run"]


def test_bounded_run_does_not_compile_axiom_before_evidence_threshold():
    artifact = AbductiveExecutive(
        seed=10,
        config=ExecutiveConfig(
            use_salience=False,
            early_stop=True,
            max_interventions=1,
        ),
    ).run()
    assert artifact["metrics"]["discovery_complete"] is False
    assert artifact["candidate_axiom"] is None


def test_paired_benchmark_preserves_winner_and_reports_savings():
    report = run_benchmark([1, 2, 3])
    summary = report["paired_summary"]
    assert summary["run_count"] == 3
    assert summary["same_winner_rate"] == 1.0
    assert summary["both_complete_rate"] == 1.0
    assert summary["same_verdict_rate"] == 1.0
    assert summary["mean_experiments_saved"] > 0


def test_discovery_report_contains_all_five_panels_and_claim_boundary():
    artifact = AbductiveExecutive(seed=99).run()
    html = render_discovery_html(artifact)
    assert "1 · Synthetic elevator world" in html
    assert "2 · Sensor experience" in html
    assert "3 · Competing hypotheses" in html
    assert "4 · Interventions" in html
    assert "5 · Candidate axiom and deterministic verdict" in html
    assert "Claim boundary" in html
    assert artifact["provenance"]["artifact_hash"] in html


def test_benchmark_report_carries_honest_scope_language():
    report = run_benchmark([7])
    html = render_benchmark_html(report)
    assert "BrainSNN-style salience A/B benchmark" in html
    assert "does not establish" in html
