"""Spectra: a tiny declarative language for certified spectral screening."""
from gaugegap.spectra_lang.interpreter import (
    Interpreter,
    Program,
    SpectraError,
    run_file,
    run_program,
)

__all__ = ["Interpreter", "Program", "SpectraError", "run_file", "run_program"]
