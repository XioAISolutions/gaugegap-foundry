"""QSVT-style polynomial eigenvalue transform, certified against the spectrum.

Quantum Singular Value / eigenvalue Transformation (QSVT) applies a degree-d
polynomial P to the eigenvalues of a (block-encoded) Hermitian operator. This
module computes that transform classically and **certifies** it: the eigenvalues of
P(H) must lie inside P evaluated (in interval arithmetic) over the certified
eigenvalue enclosures. So the polynomial-of-the-spectrum result is bracketed by the
verified interval kernel — the verification-first treatment of QSVT.

(QSVT realises P via phase factors on a quantum computer; here we compute the
exact polynomial transform and certify it. No phase-factor synthesis is faked.)

CLAIM BOUNDARY: a certified polynomial transform of a finite Hermitian spectrum;
simulation/classical-reference level. Not a continuum or Millennium claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

import numpy as np

from gaugegap.rigorous.interval_arithmetic import Interval
from gaugegap.curverank_registry import build_certified_general


def _rescale_to_unit(H: np.ndarray, a: float, b: float) -> np.ndarray:
    """Map the spectral window [a, b] to [-1, 1]: x = (2H - (a+b)I)/(b-a)."""
    n = H.shape[0]
    return (2.0 * H - (a + b) * np.eye(n)) / (b - a)


def _poly_matrix(x: np.ndarray, coeffs: Sequence[float]) -> np.ndarray:
    """Monomial Horner P(x) for a matrix x (coeffs low->high degree)."""
    n = x.shape[0]
    acc = coeffs[-1] * np.eye(n, dtype=complex)
    for c in reversed(coeffs[:-1]):
        acc = acc @ x + c * np.eye(n, dtype=complex)
    return acc


def _poly_interval(x: Interval, coeffs: Sequence[float]) -> Interval:
    """Rigorous interval Horner P(x) (outward-rounded)."""
    acc = Interval.from_float(float(coeffs[-1]))
    for c in reversed(coeffs[:-1]):
        acc = acc * x + Interval.from_float(float(c))
    return acc


@dataclass
class QSVTResult:
    coeffs: List[float]
    window: Tuple[float, float]                 # [a, b] rescaled to [-1, 1]
    transformed_eigenvalues: List[float]        # eigenvalues of P(H_norm)
    reference_eigenvalues: List[float]          # P(rescaled classical eigenvalues)
    certified_enclosures: List[Tuple[float, float]]  # P([lo,hi]) per eigenvalue
    all_inside: bool                            # transform inside certified P-enclosures
    max_residual: float                         # vs reference

    def to_dict(self) -> dict:
        return {
            "kind": "qsvt_eigenvalue_transform",
            "coeffs": self.coeffs, "window": list(self.window),
            "transformed_eigenvalues": self.transformed_eigenvalues,
            "certified_enclosures": [list(e) for e in self.certified_enclosures],
            "all_inside_certified": self.all_inside,
            "max_residual_vs_reference": self.max_residual,
            "claim_boundary": ("certified polynomial transform of a finite Hermitian "
                               "spectrum; not a continuum/Millennium claim"),
        }


def qsvt_eigenvalue_transform(H: np.ndarray, coeffs: Sequence[float], *,
                              error: float = 1e-12) -> QSVTResult:
    """Apply the polynomial ``coeffs`` (monomial, low->high) to H's eigenvalues,
    rescaled to [-1, 1], and certify the transformed spectrum against the
    interval-enclosed spectrum.
    """
    H = np.asarray(H)
    H = (H + H.conj().T) / 2.0
    enclosures = build_certified_general(H, error=error)
    a = min(float(iv.lower) for iv in enclosures)
    b = max(float(iv.upper) for iv in enclosures)
    if b <= a:
        b = a + 1.0  # degenerate spectrum guard

    x_mat = _rescale_to_unit(H, a, b)
    Px = _poly_matrix(x_mat, coeffs)
    Px = (Px + Px.conj().T) / 2.0
    transformed = np.sort(np.real(np.linalg.eigvalsh(Px)))

    # reference: P on rescaled classical eigenvalues
    ev = np.sort(np.linalg.eigvalsh(H))
    x_ref = (2.0 * ev - (a + b)) / (b - a)
    reference = np.sort(np.array([float(np.polyval(list(reversed(coeffs)), xr))
                                  for xr in x_ref]))

    # certified: interval P over each rescaled certified enclosure
    half = Interval.from_float(2.0)
    shift = Interval.from_float(a + b)
    inv = Interval.from_float(1.0 / (b - a))
    cert: List[Tuple[float, float]] = []
    for iv in enclosures:
        x_int = (half * iv - shift) * inv
        p_int = _poly_interval(x_int, coeffs)
        cert.append((float(p_int.lower), float(p_int.upper)))
    cert_sorted = sorted(cert, key=lambda e: (e[0] + e[1]) / 2)

    # every transformed eigenvalue must lie in some certified P-enclosure
    all_inside = True
    for t in transformed:
        if not any(lo - 1e-9 <= t <= hi + 1e-9 for (lo, hi) in cert_sorted):
            all_inside = False
            break
    max_res = float(np.max(np.abs(transformed - reference))) if len(transformed) else 0.0

    return QSVTResult(
        coeffs=[float(c) for c in coeffs], window=(a, b),
        transformed_eigenvalues=[float(t) for t in transformed],
        reference_eigenvalues=[float(r) for r in reference],
        certified_enclosures=cert_sorted, all_inside=all_inside, max_residual=max_res,
    )
