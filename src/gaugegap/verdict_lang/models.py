"""Deterministic toy models for the Verdict eval DSL.

These are intentionally trivial, network-free classifiers so an eval is fully
reproducible and hermetic. They are NOT machine learning — Verdict is a
demonstration of *eval-first* semantics, not a model zoo. A real deployment would
register real models behind the same interface.
"""
from __future__ import annotations

import re
from typing import Callable, Dict

_POS = {"good", "great", "love", "excellent", "happy", "wonderful", "best",
        "amazing", "fantastic", "delightful"}
_NEG = {"bad", "terrible", "hate", "awful", "sad", "worst", "poor", "horrible",
        "disappointing", "broken"}


def _tokens(text: str) -> set:
    return set(re.findall(r"[a-z]+", text.lower()))


def keyword_sentiment(text: str) -> str:
    """Label by positive/negative keyword counts; ties and empties -> 'pos'."""
    toks = _tokens(text)
    pos, neg = len(toks & _POS), len(toks & _NEG)
    if neg > pos:
        return "neg"
    return "pos"


def always_pos(text: str) -> str:
    return "pos"


def always_neg(text: str) -> str:
    return "neg"


MODELS: Dict[str, Callable[[str], str]] = {
    "keyword_sentiment": keyword_sentiment,
    "always_pos": always_pos,
    "always_neg": always_neg,
}
