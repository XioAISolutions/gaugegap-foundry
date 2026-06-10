from __future__ import annotations

import json
import math
from numbers import Real
from pathlib import Path
from typing import Any

from gaugegap.ledger import utc_now
from gaugegap.models.z2_plaquette import CLAIM_BOUNDARY


def make_gap_certificate(
    *,
    hypothesis_id: str,
    model: str,
    n_qubits: int,
    parameters: dict[str, Any],
    backend: dict[str, Any],
    ground_energy: float,
    first_excited_energy: float,
    gap: float,
    residual_norm: float | None = None,
    status: str = "finite_system_verified",
    git: dict[str, Any] | None = None,
    claim_boundary: str = CLAIM_BOUNDARY,
) -> dict[str, Any]:
    if not hypothesis_id:
        raise ValueError("hypothesis_id must not be empty")
    if not model:
        raise ValueError("model must not be empty")
    if n_qubits <= 0:
        raise ValueError("n_qubits must be positive")
    for name, value in (
        ("ground_energy", ground_energy),
        ("first_excited_energy", first_excited_energy),
        ("gap", gap),
    ):
        if not isinstance(value, Real) or not math.isfinite(float(value)):
            raise ValueError(f"{name} must be finite")
    if gap < 0.0:
        raise ValueError("gap must be non-negative")
    if not claim_boundary:
        raise ValueError("claim_boundary must not be empty")
    return {
        "schema": "gaugegap.gap_certificate.v1",
        "timestamp_utc": utc_now().isoformat(),
        "hypothesis_id": hypothesis_id,
        "model": model,
        "n_qubits": int(n_qubits),
        "parameters": parameters,
        "backend": backend,
        "ground_energy": float(ground_energy),
        "first_excited_energy": float(first_excited_energy),
        "gap": float(gap),
        "residual_norm": None if residual_norm is None else float(residual_norm),
        "status": status,
        "git": git or {},
        "claim_boundary": claim_boundary,
    }


def write_gap_certificate(path: Path, certificate: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(certificate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
