"""Models for the Verdict eval DSL.

The bundled classifiers are intentionally trivial, network-free, and
deterministic so an eval is fully reproducible and hermetic. They are NOT machine
learning — Verdict is a demonstration of *eval-first* semantics.

A **real** model plugs in behind the same interface: a ``Callable[[str], str]``
mapping an input to a predicted label. Register one with :func:`register_model`,
or wrap an external CLI/LLM with :func:`command_model` (no network dependency is
imported here, keeping the package and CI hermetic).
"""
from __future__ import annotations

import os
import re
import shlex
import subprocess
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


def register_model(name: str, fn: Callable[[str], str], *, overwrite: bool = False) -> None:
    """Register a real (or wrapped) model under ``name`` for use in `.verdict`.

    ``fn`` must map an input string to a predicted label string. This is the
    integration point for production models — wrap an LLM/HTTP/ML callable in a
    ``Callable[[str], str]`` and register it here before running the program.
    """
    if not callable(fn):
        raise TypeError("model must be callable: (str) -> str")
    if name in MODELS and not overwrite:
        raise ValueError(f"model {name!r} already registered; pass overwrite=True")
    MODELS[name] = fn


def command_model(template: str, *, timeout: float = 60.0) -> Callable[[str], str]:
    """Wrap an external command as a model, with no network import in this package.

    ``template`` is a shell command containing ``{input}``; the command's stdout
    (stripped) is the predicted label. Example::

        register_model("my_llm", command_model("my-classifier --text {input}"))

    Use this to plug a real LLM/CLI into Verdict without adding a provider
    dependency to the repo. The command itself is the user's responsibility.
    """
    def _run(text: str) -> str:
        cmd = template.replace("{input}", shlex.quote(text))
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                              timeout=timeout)
        if proc.returncode != 0:
            raise RuntimeError(f"model command failed ({proc.returncode}): "
                               f"{proc.stderr.strip()}")
        return proc.stdout.strip()
    return _run

