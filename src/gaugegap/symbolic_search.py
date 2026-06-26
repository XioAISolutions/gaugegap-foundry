"""Historically grounded symbolic-number tools with explicit null controls.

Equal numerical values are treated as symbolic associations only.  They do not
establish causation, prediction, secret coordination, or physical law.
"""
from __future__ import annotations

from dataclasses import dataclass
import random
import re
from typing import Callable, Iterable, Mapping, Sequence

CLAIM_BOUNDARY = (
    "Symbolic association only; no causal, predictive, scientific, or "
    "conspiratorial inference follows from equal numerical values."
)

HEBREW_STANDARD: dict[str, int] = {
    "א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6, "ז": 7, "ח": 8, "ט": 9,
    "י": 10, "כ": 20, "ך": 20, "ל": 30, "מ": 40, "ם": 40, "נ": 50, "ן": 50,
    "ס": 60, "ע": 70, "פ": 80, "ף": 80, "צ": 90, "ץ": 90, "ק": 100,
    "ר": 200, "ש": 300, "ת": 400,
}

ENGLISH_ORDINAL: dict[str, int] = {
    chr(code): code - 64 for code in range(ord("A"), ord("Z") + 1)
}

Cipher = Mapping[str, int] | Callable[[str], int]


@dataclass(frozen=True)
class SymbolicValue:
    text: str
    normalized: str
    cipher: str
    value: int
    claim_boundary: str = CLAIM_BOUNDARY


@dataclass(frozen=True)
class NullModelResult:
    observed_text: str
    target: int
    observed_distance: int
    trials: int
    equal_or_better: int
    empirical_p_value: float
    seed: int
    claim_boundary: str = CLAIM_BOUNDARY

    def summary(self) -> dict[str, object]:
        return {
            "schema": "gaugegap.symbolic_null_model.v1",
            "observed_text": self.observed_text,
            "target": self.target,
            "observed_distance": self.observed_distance,
            "trials": self.trials,
            "equal_or_better": self.equal_or_better,
            "empirical_p_value": self.empirical_p_value,
            "seed": self.seed,
            "claim_boundary": self.claim_boundary,
        }


def normalize_english(text: str) -> str:
    return "".join(character for character in text.upper() if "A" <= character <= "Z")


def normalize_hebrew(text: str) -> str:
    return "".join(character for character in text if character in HEBREW_STANDARD)


def cipher_value(text: str, cipher: Cipher, *, normalizer: Callable[[str], str]) -> int:
    normalized = normalizer(text)
    if callable(cipher):
        return int(cipher(normalized))
    return sum(cipher.get(character, 0) for character in normalized)


def evaluate(text: str, *, cipher_name: str = "english-ordinal") -> SymbolicValue:
    if cipher_name == "english-ordinal":
        normalizer = normalize_english
        cipher = ENGLISH_ORDINAL
    elif cipher_name == "hebrew-standard":
        normalizer = normalize_hebrew
        cipher = HEBREW_STANDARD
    else:
        raise ValueError(f"unknown cipher: {cipher_name}")
    normalized = normalizer(text)
    return SymbolicValue(text, normalized, cipher_name, cipher_value(text, cipher, normalizer=normalizer))


def equal_value_groups(texts: Iterable[str], *, cipher_name: str) -> dict[int, tuple[str, ...]]:
    grouped: dict[int, list[str]] = {}
    for text in texts:
        result = evaluate(text, cipher_name=cipher_name)
        grouped.setdefault(result.value, []).append(text)
    return {
        value: tuple(sorted(items))
        for value, items in sorted(grouped.items())
        if len(items) > 1
    }


def nearest_by_value(texts: Iterable[str], target: int, *, cipher_name: str) -> tuple[SymbolicValue, ...]:
    values = [evaluate(text, cipher_name=cipher_name) for text in texts]
    return tuple(sorted(values, key=lambda item: (abs(item.value - target), item.value, item.normalized)))


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\S+", text)


def null_distance_test(
    text: str,
    *,
    target: int,
    cipher_name: str = "english-ordinal",
    trials: int = 1000,
    seed: int = 0,
    corpus_tokens: Sequence[str] | None = None,
) -> NullModelResult:
    """Compare a chosen match with deterministic shuffled-token controls.

    The null model deliberately preserves token count and token-length profile.
    It is a diagnostic against post-hoc pattern selection, not a universal
    significance test for historical interpretation.
    """

    if trials < 1:
        raise ValueError("trials must be positive")
    observed = evaluate(text, cipher_name=cipher_name)
    observed_distance = abs(observed.value - target)
    tokens = list(corpus_tokens) if corpus_tokens is not None else _tokenize(text)
    if not tokens:
        tokens = [text]
    rng = random.Random(seed)
    equal_or_better = 0
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    for _ in range(trials):
        sampled: list[str] = []
        for token in tokens:
            clean = normalize_english(token)
            length = max(1, len(clean))
            sampled.append("".join(rng.choice(alphabet) for _ in range(length)))
        surrogate = " ".join(sampled)
        distance = abs(evaluate(surrogate, cipher_name="english-ordinal").value - target)
        if distance <= observed_distance:
            equal_or_better += 1

    return NullModelResult(
        observed_text=text,
        target=target,
        observed_distance=observed_distance,
        trials=trials,
        equal_or_better=equal_or_better,
        empirical_p_value=(equal_or_better + 1) / (trials + 1),
        seed=seed,
    )
