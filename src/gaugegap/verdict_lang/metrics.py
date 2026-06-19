"""Classification metrics for the Verdict eval DSL.

Pure-Python (no sklearn/numpy dependency) so an eval stays hermetic. Supports
multi-class labels via macro-averaging; the per-label and confusion-matrix
breakdowns are surfaced in the report as evidence.

Eval-first semantics are preserved: a metric is only ever computed from a logged
eval run, never asserted without measurement.
"""
from __future__ import annotations

from typing import Dict, List, Sequence

# Scalar metric names that an `assert score(...)` can reference.
SCALAR_METRICS = ("accuracy", "precision", "recall", "f1")


def confusion_matrix(expected: Sequence, predicted: Sequence) -> Dict[str, Dict[str, int]]:
    """Nested dict: confusion[true_label][pred_label] = count."""
    labels = sorted({str(x) for x in expected} | {str(x) for x in predicted})
    cm = {t: {p: 0 for p in labels} for t in labels}
    for e, p in zip(expected, predicted):
        cm[str(e)][str(p)] += 1
    return cm


def _per_label(expected: Sequence, predicted: Sequence) -> Dict[str, Dict[str, float]]:
    labels = sorted({str(x) for x in expected} | {str(x) for x in predicted})
    out: Dict[str, Dict[str, float]] = {}
    exp = [str(x) for x in expected]
    pred = [str(x) for x in predicted]
    for lab in labels:
        tp = sum(1 for e, p in zip(exp, pred) if p == lab and e == lab)
        fp = sum(1 for e, p in zip(exp, pred) if p == lab and e != lab)
        fn = sum(1 for e, p in zip(exp, pred) if p != lab and e == lab)
        support = sum(1 for e in exp if e == lab)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = (2 * precision * recall / (precision + recall)
              if (precision + recall) else 0.0)
        out[lab] = {
            "precision": precision, "recall": recall, "f1": f1,
            "support": support, "tp": tp, "fp": fp, "fn": fn,
        }
    return out


def compute_metrics(expected: Sequence, predicted: Sequence) -> Dict[str, object]:
    """Return accuracy + macro precision/recall/f1 + per-label + confusion matrix.

    Macro-averaging gives every class equal weight (robust to class imbalance).
    """
    if len(expected) != len(predicted):
        raise ValueError("expected and predicted must have equal length")
    if not expected:
        raise ValueError("no cases to score")
    n = len(expected)
    correct = sum(1 for e, p in zip(expected, predicted) if str(e) == str(p))
    accuracy = correct / n
    per_label = _per_label(expected, predicted)
    n_labels = len(per_label) or 1
    macro_precision = sum(v["precision"] for v in per_label.values()) / n_labels
    macro_recall = sum(v["recall"] for v in per_label.values()) / n_labels
    macro_f1 = sum(v["f1"] for v in per_label.values()) / n_labels
    return {
        "accuracy": accuracy,
        "precision": macro_precision,
        "recall": macro_recall,
        "f1": macro_f1,
        "per_label": per_label,
        "confusion_matrix": confusion_matrix(expected, predicted),
        "n_cases": n,
    }


def scalar_metric(metrics: Dict[str, object], name: str) -> float:
    """Extract a scalar metric (the value an assertion compares against)."""
    if name not in SCALAR_METRICS:
        raise ValueError(f"unknown metric {name!r}; choose from {SCALAR_METRICS}")
    return float(metrics[name])
