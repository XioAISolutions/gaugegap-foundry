"""Verdict — a tiny eval-first language for honest model claims.

Verdict is the AI-side sibling of Spectra (the certified spectral-screening DSL).
Its defining idea mirrors Spectra's: **evidence is a first-class semantic.** A
claim about a model — ``assert score(E) >= t`` or ``assert no_regression(...)`` —
can only pass if it is backed by a **logged, reproducible eval run** ``E``. You
cannot assert a score you did not measure, and ``report`` writes the full
per-case eval log so the claim is auditable.

This is deliberately small and honest: the bundled models are deterministic toy
classifiers (``models.py``), so every run is hermetic and reproducible. It is a
demonstration of eval-first semantics, **not** a production eval framework or a
claim about real model quality.

Grammar (one statement per line; ``#`` starts a comment)::

    dataset D = cases("examples/sentiment_cases.jsonl")
    model   M = keyword_sentiment()
    eval    E = run(M, D, metric=accuracy)
    assert  score(E) >= 0.8
    assert  no_regression(E, baseline=0.75)
    report  "results/verdict-demo"

Each ``cases`` file is JSONL with ``{"input": ..., "expected": ...}`` per line.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from gaugegap.verdict_lang.models import MODELS

_METRICS = {"accuracy"}


class VerdictError(Exception):
    """Raised on a parse error or an eval-backed assertion that does not hold."""


@dataclass
class Program:
    datasets: Dict[str, Dict] = field(default_factory=dict)
    models: Dict[str, str] = field(default_factory=dict)
    evals: Dict[str, Dict] = field(default_factory=dict)
    assertions: List[Dict] = field(default_factory=list)
    report_dir: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "claim_boundary": (
                "Eval-first demonstration with deterministic toy models; every "
                "claim is backed by a logged, reproducible eval run. Not a "
                "production eval framework or a claim about real model quality."
            ),
            "datasets": {k: {"path": v["path"], "n_cases": len(v["cases"])}
                         for k, v in self.datasets.items()},
            "models": self.models,
            "evals": {k: {"model": v["model"], "dataset": v["dataset"],
                          "metric": v["metric"], "score": v["score"],
                          "n_cases": len(v["log"]), "log_file": f"{k}_log.jsonl"}
                      for k, v in self.evals.items()},
            "assertions": self.assertions,
        }


_RE_DATASET = re.compile(r'^dataset\s+(\w+)\s*=\s*cases\(\s*"([^"]+)"\s*\)$')
_RE_MODEL = re.compile(r"^model\s+(\w+)\s*=\s*(\w+)\(\s*\)$")
_RE_EVAL = re.compile(
    r"^eval\s+(\w+)\s*=\s*run\(\s*(\w+)\s*,\s*(\w+)\s*,\s*metric\s*=\s*(\w+)\s*\)$"
)
_RE_ASSERT_SCORE = re.compile(r"^assert\s+score\(\s*(\w+)\s*\)\s*>=\s*([\d.]+)$")
_RE_ASSERT_NOREG = re.compile(
    r"^assert\s+no_regression\(\s*(\w+)\s*,\s*baseline\s*=\s*([\d.]+)\s*\)$"
)
_RE_REPORT = re.compile(r'^report\s+"([^"]+)"$')


class Interpreter:
    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self.p = Program()
        self.base = Path(base_dir) if base_dir else Path.cwd()

    def run(self, source: str) -> Program:
        for lineno, raw in enumerate(source.splitlines(), start=1):
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            try:
                self._exec(line)
            except VerdictError:
                raise
            except Exception as exc:
                raise VerdictError(f"line {lineno}: {exc}") from exc
        if self.p.report_dir is not None:
            self._write_report(Path(self.p.report_dir))
        return self.p

    def _exec(self, line: str) -> None:
        m = _RE_DATASET.match(line)
        if m:
            self._load_dataset(m.group(1), m.group(2))
            return
        m = _RE_MODEL.match(line)
        if m:
            name, model = m.group(1), m.group(2)
            if model not in MODELS:
                raise VerdictError(f"unknown model {model!r} "
                                   f"(known: {sorted(MODELS)})")
            self.p.models[name] = model
            return
        m = _RE_EVAL.match(line)
        if m:
            self._eval(*m.groups())
            return
        m = _RE_ASSERT_SCORE.match(line)
        if m:
            self._assert_score(m.group(1), float(m.group(2)))
            return
        m = _RE_ASSERT_NOREG.match(line)
        if m:
            self._assert_no_regression(m.group(1), float(m.group(2)))
            return
        m = _RE_REPORT.match(line)
        if m:
            self.p.report_dir = m.group(1)
            return
        raise VerdictError(f"cannot parse: {line!r}")

    def _load_dataset(self, name: str, path: str) -> None:
        p = (self.base / path) if not Path(path).is_absolute() else Path(path)
        if not p.exists():
            raise VerdictError(f"dataset file not found: {path}")
        cases = []
        for ln in p.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if not ln:
                continue
            rec = json.loads(ln)
            if "input" not in rec or "expected" not in rec:
                raise VerdictError(f"case missing input/expected: {rec}")
            cases.append(rec)
        if not cases:
            raise VerdictError(f"dataset {path} has no cases")
        self.p.datasets[name] = {"path": path, "cases": cases}

    def _eval(self, name: str, model_name: str, ds_name: str, metric: str) -> None:
        if model_name not in self.p.models:
            raise VerdictError(f"unknown model {model_name!r}")
        if ds_name not in self.p.datasets:
            raise VerdictError(f"unknown dataset {ds_name!r}")
        if metric not in _METRICS:
            raise VerdictError(f"unknown metric {metric!r} (known: {sorted(_METRICS)})")
        fn = MODELS[self.p.models[model_name]]
        cases = self.p.datasets[ds_name]["cases"]
        log = []
        correct = 0
        for rec in cases:
            pred = fn(str(rec["input"]))
            ok = pred == rec["expected"]
            correct += int(ok)
            log.append({"input": rec["input"], "expected": rec["expected"],
                        "prediction": pred, "correct": ok})
        score = correct / len(cases)
        self.p.evals[name] = {
            "model": model_name, "dataset": ds_name, "metric": metric,
            "score": score, "log": log,
        }

    def _assert_score(self, eval_name: str, threshold: float) -> None:
        if eval_name not in self.p.evals:
            raise VerdictError(f"unknown eval {eval_name!r} "
                               "(an assertion must be backed by an eval run)")
        score = self.p.evals[eval_name]["score"]
        if not score >= threshold:
            raise VerdictError(
                f"assertion failed: score({eval_name})={score:.4f} < {threshold} "
                "(claim not backed by the eval)"
            )
        self.p.assertions.append({
            "kind": "score", "eval": eval_name, "threshold": threshold,
            "score": score, "passed": True,
        })

    def _assert_no_regression(self, eval_name: str, baseline: float) -> None:
        if eval_name not in self.p.evals:
            raise VerdictError(f"unknown eval {eval_name!r}")
        score = self.p.evals[eval_name]["score"]
        if not score >= baseline:
            raise VerdictError(
                f"regression: score({eval_name})={score:.4f} < baseline {baseline}"
            )
        self.p.assertions.append({
            "kind": "no_regression", "eval": eval_name, "baseline": baseline,
            "score": score, "passed": True,
        })

    def _write_report(self, out: Path) -> None:
        out.mkdir(parents=True, exist_ok=True)
        (out / "verdict_report.json").write_text(
            json.dumps(self.p.to_dict(), indent=2), encoding="utf-8"
        )
        # The full per-case log is the evidence backing every assertion.
        for name, ev in self.p.evals.items():
            with (out / f"{name}_log.jsonl").open("w", encoding="utf-8") as fh:
                for row in ev["log"]:
                    fh.write(json.dumps(row, sort_keys=True) + "\n")


def run_program(source: str, base_dir: Optional[Path] = None) -> Program:
    return Interpreter(base_dir).run(source)


def run_file(path: str | Path) -> Program:
    path = Path(path)
    return Interpreter(base_dir=path.resolve().parent.parent).run(
        path.read_text(encoding="utf-8")
    )
