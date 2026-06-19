"""Public API: certify the spectrum of any Hermitian matrix.

``certify_spectrum`` is the product-facing entry point over the general
certified-eigenvalue kernel: give it a Hermitian matrix, get rigorous
directed-rounding interval enclosures for every eigenvalue (not floating-point
estimates), plus a structured certificate. For a registered candidate-operator
family it can additionally emit the discharged Lean 4 / Coq separation proof.

CLAIM BOUNDARY: the enclosures are rigorous finite-matrix spectral certificates.
This is verification infrastructure; it is not a proof of the Riemann Hypothesis
or any Millennium Prize problem.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

import numpy as np

from gaugegap.rigorous.interval_arithmetic import Interval
from gaugegap.curverank_registry import build_certified_general


@dataclass
class SpectrumCertificate:
    """Certified eigenvalue enclosures for a Hermitian matrix."""

    n: int
    enclosures: List[tuple]  # (lower, upper) per eigenvalue, ascending
    midpoints: List[float]
    max_width: float
    method: str = "interval_arithmetic_residual_bound"
    formal: Optional[dict] = field(default=None)

    def to_dict(self) -> dict:
        d = {
            "n": self.n,
            "method": self.method,
            "max_width": self.max_width,
            "enclosures": [list(e) for e in self.enclosures],
            "midpoints": self.midpoints,
            "claim_boundary": (
                "rigorous finite-matrix eigenvalue enclosures (verification "
                "infrastructure); not a proof of the Riemann Hypothesis or any "
                "Millennium Prize problem"
            ),
        }
        if self.formal is not None:
            d["formal"] = self.formal
        return d


def certify_spectrum(
    H: np.ndarray,
    *,
    error: float = 1e-12,
    formal_family: Optional[str] = None,
    emit_formal: bool = False,
    name: str = "Matrix",
    k_zeros: int = 20,
    threshold: float = 1.0,
) -> SpectrumCertificate:
    """Return certified eigenvalue enclosures for a Hermitian matrix ``H``.

    Parameters
    ----------
    H : a Hermitian (real-symmetric or complex-Hermitian) matrix.
    error : interval half-width added to each matrix entry (input uncertainty).
    formal_family : optional registered family ({"xp","dirac_rindler",
        "quantum_graph"}); when given, the discharged Lean/Coq *separation* proof
        for that family is attached. Only meaningful when ``H`` actually is that
        family's truncation.
    emit_formal : when True (and no ``formal_family``), attach a generic discharged
        Lean/Coq *global spectral enclosure* certificate for this matrix.
    name : a label used in the generic certificate's namespace.
    """
    enclosures: List[Interval] = build_certified_general(H, error=error)
    tuples = [tuple(float(x) for x in iv.to_tuple()) for iv in enclosures]
    midpoints = [(lo + hi) / 2.0 for (lo, hi) in tuples]
    max_width = max((hi - lo for (lo, hi) in tuples), default=0.0)

    formal = None
    if formal_family is not None:
        from gaugegap.rigorous.curverank_formal_emit import (
            discharged_separation_proof,
        )

        proof = discharged_separation_proof(
            formal_family, len(midpoints), k_zeros=k_zeros, threshold=threshold
        )
        formal = {
            "kind": "separation_proof",
            "family": proof.family,
            "separated": proof.lower_bound > proof.threshold,
            "lower_bound": proof.lower_bound,
            "lean4": proof.lean4,
            "coq": proof.coq,
        }
    elif emit_formal:
        from gaugegap.rigorous.enclosure_certificate import (
            emit_enclosure_certificate,
        )

        formal = emit_enclosure_certificate(tuples, name=name).to_dict()

    return SpectrumCertificate(
        n=len(midpoints),
        enclosures=tuples,
        midpoints=midpoints,
        max_width=max_width,
        formal=formal,
    )


def _load_matrix(path: Path) -> np.ndarray:
    if path.suffix == ".npy":
        return np.load(path)
    if path.suffix in (".csv", ".txt"):
        return np.loadtxt(path, delimiter="," if path.suffix == ".csv" else None)
    raise ValueError(f"unsupported matrix file {path!r}; use .npy/.csv/.txt")


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="Certify the spectrum of a Hermitian matrix (rigorous "
                    "interval enclosures).")
    ap.add_argument("matrix", type=Path,
                    help="matrix file (.npy / .csv / .txt), Hermitian")
    ap.add_argument("--error", type=float, default=1e-12,
                    help="input interval half-width per entry")
    ap.add_argument("--formal-family", type=str, default=None,
                    choices=[None, "xp", "dirac_rindler", "quantum_graph"],
                    help="attach the discharged Lean/Coq separation proof")
    ap.add_argument("--emit-formal", action="store_true",
                    help="attach a generic discharged Lean/Coq spectral-enclosure "
                         "certificate (for any Hermitian matrix)")
    ap.add_argument("--name", type=str, default="Matrix",
                    help="label for the generic certificate namespace")
    ap.add_argument("--output", type=Path, default=None,
                    help="write the JSON certificate here (default: stdout)")
    args = ap.parse_args(argv)

    H = _load_matrix(args.matrix)
    cert = certify_spectrum(H, error=args.error, formal_family=args.formal_family,
                            emit_formal=args.emit_formal, name=args.name)
    payload = json.dumps(cert.to_dict(), indent=2)
    if args.output is not None:
        args.output.write_text(payload)
        print(f"certified {cert.n} eigenvalues, max width {cert.max_width:.2e} "
              f"-> {args.output}")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
