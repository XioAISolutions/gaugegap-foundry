"""StyleGap: finite linguistic-screening benchmark (human vs AI text).

Wires Rodrigues, Sturm & Pinheiro (iScience 2026, 29, 114976,
doi:10.1016/j.isci.2026.114976) into the foundry as a reproducible,
finite benchmark track.

CLAIM BOUNDARY: finite-corpus linguistic screening infrastructure for
transparent comparison of human-authored and LLM-generated text. It is
NOT an AI-detection product, does NOT claim generalizable detection, and
must not be described as solving machine-text identification. Proprietary
instruments (e.g. LIWC dictionaries) are replaced by explicit open
lexicons, labeled as proxies. Reported numbers are corpus-local.
"""
from __future__ import annotations

import math
import re
from collections import Counter

import numpy as np

TOKEN_RE = re.compile(r"[a-z\u00c0-\u00ff']+", re.IGNORECASE)
SENT_RE = re.compile(r"[.!?]+")

INFORMAL = {
    "lol", "yeah", "gonna", "wanna", "ok", "okay", "hey", "guys", "stuff",
    "cool", "awesome", "crazy", "kinda", "sorta", "wow", "ugh", "hmm",
}
POSITIVE = {
    "good", "great", "success", "benefit", "win", "improve", "best",
    "positive", "achieve", "gain", "happy", "proud", "progress", "solution",
    "opportunity", "ensure", "essential", "important",
}
NEGATIVE = {
    "bad", "fail", "crisis", "problem", "fear", "angry", "sad", "loss",
    "risk", "threat", "worse", "damage", "victim", "suffer", "danger",
}
PERSONAL = {"i", "me", "my", "we", "our", "you", "your", "us", "mine"}
TEMPORAL = {
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday",
    "sunday", "january", "february", "march", "april", "may", "june",
    "july", "august", "september", "october", "november", "december",
    "today", "yesterday", "tomorrow", "year", "month", "week", "day",
}


def _tokens(text: str):
    return [t.lower() for t in TOKEN_RE.findall(text)]


def _sentences(text: str):
    return [s for s in SENT_RE.split(text) if s.strip()]


def document_features(text: str) -> dict:
    """Per-document features.

    Proxies are explicitly labeled: they approximate the LIWC-style
    dimensions reported by Rodrigues et al. (2026) without using
    proprietary dictionaries.
    """
    toks = _tokens(text)
    sents = _sentences(text)
    n = len(toks)
    feats = {
        "word_count": float(n),
        "lexical_diversity": (len(set(toks)) / n) if n else 0.0,
        "avg_sentence_len": (n / len(sents)) if sents else 0.0,
    }
    if len(sents) >= 2:
        lens = [len(_tokens(s)) for s in sents]
        feats["sentence_len_std"] = float(np.std(lens))
    else:
        feats["sentence_len_std"] = 0.0
    if n:
        counts = Counter(toks)
        for name, lex in (
            ("informal_proxy", INFORMAL),
            ("positive_proxy", POSITIVE),
            ("negative_proxy", NEGATIVE),
            ("personal_proxy", PERSONAL),
            ("temporal_proxy", TEMPORAL),
        ):
            feats[name] = sum(counts[w] for w in lex) / n
    else:
        for name in ("informal_proxy", "positive_proxy", "negative_proxy",
                     "personal_proxy", "temporal_proxy"):
            feats[name] = 0.0
    return feats


def corpus_summary(docs: list[str]) -> dict:
    rows = [document_features(d) for d in docs]
    keys = sorted(rows[0].keys()) if rows else []
    out = {}
    for k in keys:
        vals = np.array([r[k] for r in rows], dtype=float)
        out[k] = {"mean": float(vals.mean()), "std": float(vals.std())}
    return out


def relative_difference(human_docs: list[str], ai_docs: list[str],
                        seed: int = 20260920, boots: int = 2000) -> dict:
    """Per-feature delta% (AI vs human) with a bootstrap CI.

    Deterministic given `seed`. Corpus-local; see module claim boundary.
    """
    hr = [document_features(d) for d in human_docs]
    ar = [document_features(d) for d in ai_docs]
    rng = np.random.default_rng(seed)
    keys = sorted(hr[0].keys()) if hr else []
    hmat = (np.array([[r[k] for k in keys] for r in hr], dtype=float)
            if hr else np.zeros((0, len(keys))))
    amat = (np.array([[r[k] for k in keys] for r in ar], dtype=float)
            if ar else np.zeros((0, len(keys))))
    result = {}
    for j, k in enumerate(keys):
        h, a = hmat[:, j], amat[:, j]
        hm = float(h.mean()) if h.size else 0.0
        am = float(a.mean()) if a.size else 0.0
        delta = ((am - hm) / hm * 100.0) if hm else 0.0
        deltas = np.empty(boots)
        for b in range(boots):
            hs = rng.choice(h, size=h.size, replace=True) if h.size else np.zeros(0)
            as_ = rng.choice(a, size=a.size, replace=True) if a.size else np.zeros(0)
            hmean = hs.mean() if hs.size else 0.0
            amean = as_.mean() if as_.size else 0.0
            deltas[b] = ((amean - hmean) / hmean * 100.0) if hmean else 0.0
        lo, hi = np.percentile(deltas, [2.5, 97.5])
        result[k] = {
            "human_mean": hm, "ai_mean": am, "delta_pct": float(delta),
            "ci95": [float(lo), float(hi)],
            "excludes_zero": bool(lo > 0 or hi < 0),
        }
    return result


def ngram_log_odds(docs_a: list[str], docs_b: list[str], n: int = 1,
                   top_k: int = 15, prior: float = 0.5) -> dict:
    """Monroe-style log-odds with informative Dirichlet prior.

    Proxy for the SAGE n-gram salience analysis in Rodrigues et al. (2026):
    returns the top terms that distinguish corpus B from corpus A and
    vice versa. n in {1, 2}.
    """
    def grams(text, size):
        toks = _tokens(text)
        if size == 1:
            return toks
        return [" ".join(toks[i:i + size]) for i in range(len(toks) - size + 1)]

    ca, cb = Counter(), Counter()
    for d in docs_a:
        ca.update(grams(d, n))
    for d in docs_b:
        cb.update(grams(d, n))
    vocab = set(ca) | set(cb)
    na, nb = sum(ca.values()), sum(cb.values())
    scores = {}
    for w in vocab:
        ya, yb = ca.get(w, 0), cb.get(w, 0)
        pa = (ya + prior) / (na + prior * len(vocab))
        pb = (yb + prior) / (nb + prior * len(vocab))
        lo = math.log(pb / pa)
        var = 1.0 / (ya + prior) + 1.0 / (yb + prior)
        scores[w] = lo / math.sqrt(var) if var > 0 else 0.0
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return {"toward_b": ranked[:top_k], "toward_a": ranked[-top_k:][::-1]}


def screening_protocol(human_docs: list[str], ai_docs: list[str],
                       seed: int = 20260920, test_frac: float = 0.3) -> dict:
    """Nearest-centroid screening baseline with a held-out split.

    Deliberately simple and transparent: the benchmark's point is the
    protocol (split -> standardized features -> corpus-local scoring),
    not SOTA numbers. No detector claims: see module claim boundary.
    """
    rng = np.random.default_rng(seed)
    keys = sorted(document_features(human_docs[0]).keys())

    def mat(docs):
        return np.array([[document_features(d)[k] for k in keys] for d in docs],
                        dtype=float)

    H, A = mat(human_docs), mat(ai_docs)
    h_idx = rng.permutation(len(H))
    a_idx = rng.permutation(len(A))
    h_te = max(1, int(len(H) * test_frac))
    a_te = max(1, int(len(A) * test_frac))
    h_tr, h_test = H[h_idx[h_te:]], H[h_idx[:h_te]]
    a_tr, a_test = A[a_idx[a_te:]], A[a_idx[:a_te]]
    mu = np.vstack([h_tr, a_tr]).mean(axis=0)
    sd = np.vstack([h_tr, a_tr]).std(axis=0)
    sd[sd == 0] = 1.0

    def z(mm):
        return (mm - mu) / sd

    ch, ca = z(h_tr).mean(axis=0), z(a_tr).mean(axis=0)

    def acc(X, truth_ai):
        Xz = z(X)
        dh = np.linalg.norm(Xz - ch, axis=1)
        da = np.linalg.norm(Xz - ca, axis=1)
        pred = da < dh
        return float((pred == truth_ai).mean()) if len(Xz) else 0.0

    return {
        "features": keys,
        "n_train": [len(h_tr), len(a_tr)],
        "n_test": [len(h_test), len(a_test)],
        "accuracy_human_heldout": acc(h_test, False),
        "accuracy_ai_heldout": acc(a_test, True),
    }
