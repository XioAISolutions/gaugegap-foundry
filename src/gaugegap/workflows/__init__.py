"""Quantum workflow orchestration for emulator-to-hardware progression.

This module provides standardized workflows for:
1. Classical baseline → emulator validation → hardware submission
2. Cross-platform result comparison
3. Metadata capture and ledger recording
"""

from .emulator_to_hardware import (
    EmulatorToHardwareWorkflow,
    WorkflowResult,
    run_emulator_to_hardware,
)

__all__ = [
    "EmulatorToHardwareWorkflow",
    "WorkflowResult",
    "run_emulator_to_hardware",
]

# Made with Bob
