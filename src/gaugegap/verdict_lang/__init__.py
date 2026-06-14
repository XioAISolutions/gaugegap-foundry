"""Verdict: a tiny eval-first language for honest model claims."""
from gaugegap.verdict_lang.interpreter import (
    Interpreter,
    Program,
    VerdictError,
    run_file,
    run_program,
)

__all__ = ["Interpreter", "Program", "VerdictError", "run_file", "run_program"]
