"""Tests for the Verdict eval-first DSL.

Covers the defining semantic: a model claim (`assert score`) can only pass when
backed by a logged eval run, and fails honestly otherwise.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.verdict_lang import VerdictError, run_program, run_file


def _dataset(tmp: str) -> str:
    p = Path(tmp) / "cases.jsonl"
    rows = [
        {"input": "love this, excellent and good", "expected": "pos"},
        {"input": "great and wonderful, the best", "expected": "pos"},
        {"input": "terrible and awful, i hate it", "expected": "neg"},
        {"input": "the worst, horrible and bad", "expected": "neg"},
    ]
    p.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    return str(p)


class TestVerdict(unittest.TestCase):
    def test_score_assert_passes_when_eval_backs_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            prog = run_program(
                f'dataset D = cases("{_dataset(tmp)}")\n'
                "model M = keyword_sentiment()\n"
                "eval E = run(M, D, metric=accuracy)\n"
                "assert score(E) >= 0.9\n"
            )
            self.assertEqual(prog.evals["E"]["score"], 1.0)
            self.assertEqual(len(prog.assertions), 1)
            self.assertTrue(prog.assertions[0]["passed"])

    def test_score_assert_fails_for_weak_model(self):
        # always_pos gets 0.5 on a balanced set; the claim must fail.
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(VerdictError):
                run_program(
                    f'dataset D = cases("{_dataset(tmp)}")\n'
                    "model M = always_pos()\n"
                    "eval E = run(M, D, metric=accuracy)\n"
                    "assert score(E) >= 0.8\n"
                )

    def test_assert_requires_an_eval(self):
        # You cannot assert a score with no eval backing it.
        with self.assertRaises(VerdictError):
            run_program("assert score(E) >= 0.5\n")

    def test_no_regression_fails_below_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(VerdictError):
                run_program(
                    f'dataset D = cases("{_dataset(tmp)}")\n'
                    "model M = always_neg()\n"
                    "eval E = run(M, D, metric=accuracy)\n"
                    "assert no_regression(E, baseline=0.75)\n"
                )

    def test_parse_and_semantic_errors(self):
        with self.assertRaises(VerdictError):
            run_program("model M = no_such_model()\n")
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(VerdictError):
                run_program(
                    f'dataset D = cases("{_dataset(tmp)}")\n'
                    "model M = keyword_sentiment()\n"
                    "eval E = run(M, D, metric=f1)\n"  # unknown metric
                )
        with self.assertRaises(VerdictError):
            run_program("this is not valid verdict\n")

    def test_report_writes_log_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            run_program(
                f'dataset D = cases("{_dataset(tmp)}")\n'
                "model M = keyword_sentiment()\n"
                "eval E = run(M, D, metric=accuracy)\n"
                "assert score(E) >= 0.9\n"
                f'report "{out}"\n'
            )
            self.assertTrue((out / "verdict_report.json").exists())
            self.assertTrue((out / "E_log.jsonl").exists())
            self.assertEqual(len((out / "E_log.jsonl").read_text().splitlines()), 4)

    def test_example_program_runs(self):
        prog = run_file(ROOT / "examples" / "sentiment_eval.verdict")
        self.assertEqual(prog.evals["E"]["score"], 1.0)
        self.assertEqual(len(prog.assertions), 2)


if __name__ == "__main__":
    unittest.main()
