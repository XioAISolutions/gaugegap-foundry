"""Tests for the StyleGap finite linguistic-screening benchmark.

Claim boundary: finite-corpus protocol tests only. These tests verify
mechanics and determinism on crafted corpora, not detection performance.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gaugegap.stylegap_linguistic import (  # noqa: E402
    corpus_summary,
    document_features,
    ngram_log_odds,
    relative_difference,
    screening_protocol,
)

HUMAN = [
    "ok so honestly the meeting was kind of a mess yesterday. people were angry about the budget and i am tired of it.",
    "my neighbor lost power again monday and he is furious. it sucks, we are all exhausted this year honestly.",
    "the team lost saturday and fans were sad. same story, week after week. i guess we keep waiting.",
]
AI = [
    "The council convened to discuss the budget. The proposed program aims to ensure improved outcomes and to deliver significant benefits. Furthermore, it demonstrates sustainable planning.",
    "The event caused considerable disruption. Services are actively working to restore operations. It is essential to ensure affected households receive support and further updates.",
    "The team demonstrated resilience. The organization remains committed to continuous improvement and expresses full confidence in the coming fixtures and progress.",
]


def test_feature_keys_and_ranges():
    f = document_features("The plan will improve the road. It is a great success today.")
    assert set(f) == {
        "word_count", "lexical_diversity", "avg_sentence_len", "sentence_len_std",
        "informal_proxy", "positive_proxy", "negative_proxy",
        "personal_proxy", "temporal_proxy",
    }
    assert f["word_count"] > 0
    assert 0.0 < f["lexical_diversity"] <= 1.0
    assert f["avg_sentence_len"] > 0


def test_empty_text_is_safe():
    f = document_features("")
    assert f["word_count"] == 0.0
    assert f["lexical_diversity"] == 0.0


def test_relative_difference_direction():
    rd = relative_difference(HUMAN, AI, boots=200)
    assert rd["informal_proxy"]["ai_mean"] < rd["informal_proxy"]["human_mean"]
    assert rd["personal_proxy"]["ai_mean"] < rd["personal_proxy"]["human_mean"]


def test_log_odds_direction():
    res = ngram_log_odds(HUMAN, AI, n=1, top_k=5)
    ai_terms = dict(res["toward_b"])
    human_terms = dict(res["toward_a"])
    assert any(w in ai_terms for w in ("furthermore", "sustainable", "households", "demonstrates", "considerable"))
    assert any(w in human_terms for w in ("ok", "honestly", "sucks", "angry", "sad"))


def test_screening_determinism_and_separation():
    a = screening_protocol(HUMAN, AI, seed=7)
    b = screening_protocol(HUMAN, AI, seed=7)
    assert a == b
    assert a["accuracy_human_heldout"] >= 0.5
    assert a["accuracy_ai_heldout"] >= 0.5


def test_corpus_summary_shapes():
    s = corpus_summary(HUMAN)
    assert "word_count" in s and "mean" in s["word_count"]
