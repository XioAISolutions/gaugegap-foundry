"""Verdict: a tiny eval-first language for honest model claims."""
from gaugegap.verdict_lang.interpreter import (
    Interpreter,
    Program,
    VerdictError,
    run_file,
    run_program,
)
from gaugegap.verdict_lang.models import MODELS, register_model, command_model
from gaugegap.verdict_lang.metrics import compute_metrics, SCALAR_METRICS

__all__ = [
    "Interpreter", "Program", "VerdictError", "run_file", "run_program",
    "MODELS", "register_model", "command_model",
    "compute_metrics", "SCALAR_METRICS",
]
