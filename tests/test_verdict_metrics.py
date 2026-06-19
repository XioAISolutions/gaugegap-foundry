"""Tests for Verdict classification metrics and productization hooks."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.verdict_lang import metrics as M
from gaugegap.verdict_lang import (
    run_program, register_model, command_model, VerdictError, MODELS,
)


class TestMetrics(unittest.TestCase):
    def test_perfect_classification(self):
        m = M.compute_metrics(["pos", "neg"], ["pos", "neg"])
        self.assertEqual(m["accuracy"], 1.0)
        self.assertEqual(m["f1"], 1.0)
        self.assertEqual(m["precision"], 1.0)
        self.assertEqual(m["recall"], 1.0)

    def test_macro_f1_matches_hand_calc(self):
        # expected: pos,pos,neg,neg ; predicted: pos,neg,neg,neg
        # pos: tp=1 fp=0 fn=1 -> P=1.0 R=0.5 F1=0.667
        # neg: tp=2 fp=1 fn=0 -> P=0.667 R=1.0 F1=0.8
        # macro F1 = (0.667 + 0.8)/2 = 0.733
        m = M.compute_metrics(["pos", "pos", "neg", "neg"],
                              ["pos", "neg", "neg", "neg"])
        self.assertAlmostEqual(m["f1"], 0.7333, places=3)
        self.assertEqual(m["accuracy"], 0.75)

    def test_confusion_matrix(self):
        cm = M.confusion_matrix(["a", "a", "b"], ["a", "b", "b"])
        self.assertEqual(cm["a"]["a"], 1)
        self.assertEqual(cm["a"]["b"], 1)
        self.assertEqual(cm["b"]["b"], 1)

    def test_scalar_metric_rejects_unknown(self):
        m = M.compute_metrics(["a"], ["a"])
        with self.assertRaises(ValueError):
            M.scalar_metric(m, "nonsense")

    def test_empty_raises(self):
        with self.assertRaises(ValueError):
            M.compute_metrics([], [])


class TestProductizationHooks(unittest.TestCase):
    def _program(self, body: str) -> str:
        cases = ROOT / "examples" / "sentiment_cases.jsonl"
        return (f'dataset D = cases("{cases}")\n' + body)

    def test_f1_metric_in_program(self):
        prog = run_program(self._program(
            "model M = keyword_sentiment()\n"
            "eval E = run(M, D, metric=f1)\n"
            "assert score(E) >= 0.8\n"
        ))
        self.assertEqual(prog.evals["E"]["metric"], "f1")
        self.assertIn("metrics", prog.evals["E"])
        self.assertIn("confusion_matrix", prog.evals["E"]["metrics"])

    def test_register_custom_model(self):
        register_model("upper_pos", lambda t: "pos", overwrite=True)
        self.assertIn("upper_pos", MODELS)
        prog = run_program(self._program(
            "model M = upper_pos()\n"
            "eval E = run(M, D, metric=accuracy)\n"
        ))
        self.assertIn("E", prog.evals)

    def test_register_rejects_non_callable(self):
        with self.assertRaises(TypeError):
            register_model("bad", 123)  # type: ignore[arg-type]

    def test_failed_assertion_raises(self):
        with self.assertRaises(VerdictError):
            run_program(self._program(
                "model M = always_neg()\n"
                "eval E = run(M, D, metric=f1)\n"
                "assert score(E) >= 0.8\n"
            ))

    def test_command_model_wraps_shell(self):
        # A trivial deterministic command standing in for an external classifier.
        model = command_model("printf pos")
        self.assertEqual(model("anything"), "pos")


if __name__ == "__main__":
    unittest.main()
