"""Generic machine-checkable enclosure certificates for an arbitrary Hermitian
matrix's spectrum.

Where ``curverank_formal_emit`` discharges the bespoke *separation* theorem, this
emits a discharged **global spectral enclosure** for ANY set of certified
eigenvalue intervals: given the interval kernel's per-eigenvalue bounds as the
single labelled trust input, the proof assistant discharges that every eigenvalue
lies within the global enclosure ``[min lo_i, max hi_i]`` (Lean 4 ``linarith`` /
Coq ``lra`` — no proof holes).

Trust boundary, exactly as in the separation emitter: the assistant checks the
real-arithmetic logic; it does NOT re-derive the spectral computation. The
enclosures come from the verified, directed-rounding interval kernel
(``verified_hermitian_eigenvalues``). This is verification infrastructure, not a
proof of the Riemann Hypothesis or any Millennium Prize problem.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple


@dataclass
class EnclosureCertificate:
    name: str
    n: int
    enclosures: List[Tuple[float, float]]
    global_lower: float
    global_upper: float
    lean4: str
    coq: str

    def to_dict(self) -> dict:
        return {
            "kind": "spectral_enclosure_certificate",
            "name": self.name,
            "n": self.n,
            "global_enclosure": [self.global_lower, self.global_upper],
            "lean4": self.lean4,
            "coq": self.coq,
            "trust_input": (
                "per-eigenvalue interval enclosures from the verified "
                "directed-rounding kernel (verified_hermitian_eigenvalues)"
            ),
        }


def _clean_ns(name: str) -> str:
    base = "".join(ch for ch in name.title() if ch.isalnum()) or "Matrix"
    if base[0].isdigit():
        base = "M" + base
    return base


def _lean4(ns: str, enclosures: Sequence[Tuple[float, float]],
           glo: float, ghi: float) -> str:
    lines = ["import Mathlib.Tactic", "", f"namespace SpectrumCertified.{ns}", ""]
    lines.append("/-- Abstract eigenvalues; the only used facts are the certified "
                 "interval\n    bounds below (the single trust input). -/")
    for i in range(len(enclosures)):
        lines.append(f"axiom lam_{i} : ℝ")
    lines.append("")
    lines.append("/-- TRUST INPUT — per-eigenvalue enclosures from the verified "
                 "interval kernel\n    (directed rounding). These are the only "
                 "axioms; the theorem is discharged. -/")
    for i, (lo, hi) in enumerate(enclosures):
        lines.append(f"axiom encl_{i} : {lo!r} ≤ lam_{i} ∧ lam_{i} ≤ {hi!r}")
    lines.append("")
    lines.append(f"def globalLo : ℝ := {glo!r}")
    lines.append(f"def globalHi : ℝ := {ghi!r}")
    lines.append("")
    lines.append("/-- Global spectral enclosure: every eigenvalue lies in "
                 "[globalLo, globalHi].\n    Discharged by `linarith` from the "
                 "certified bounds (no proof holes). -/")
    for i in range(len(enclosures)):
        lines.append(
            f"theorem eig_{i}_enclosed : globalLo ≤ lam_{i} ∧ "
            f"lam_{i} ≤ globalHi := by\n"
            f"  have h := encl_{i}\n"
            f"  unfold globalLo globalHi\n"
            f"  exact ⟨by linarith [h.1], by linarith [h.2]⟩"
        )
    lines.append("")
    lines.append(f"end SpectrumCertified.{ns}")
    return "\n".join(lines) + "\n"


def _coq(ns: str, enclosures: Sequence[Tuple[float, float]],
         glo: float, ghi: float) -> str:
    lines = ["(* Requires Coq >= 8.13 (decimal real literals). *)",
             "Require Import Reals.", "Require Import Lra.", "Open Scope R_scope.",
             "", f"Section SpectrumCertified_{ns}.", ""]
    for i in range(len(enclosures)):
        lines.append(f"Variable lam_{i} : R.")
    lines.append("")
    lines.append("(* TRUST INPUT: per-eigenvalue enclosures from the verified "
                 "interval kernel. *)")
    for i, (lo, hi) in enumerate(enclosures):
        lines.append(f"Hypothesis encl_{i} : {lo!r} <= lam_{i} /\\ lam_{i} <= {hi!r}.")
    lines.append("")
    lines.append(f"Definition globalLo : R := {glo!r}.")
    lines.append(f"Definition globalHi : R := {ghi!r}.")
    lines.append("")
    lines.append("(* Global spectral enclosure, discharged by lra (no holes). *)")
    for i in range(len(enclosures)):
        lines.append(
            f"Theorem eig_{i}_enclosed : globalLo <= lam_{i} /\\ lam_{i} <= globalHi.\n"
            f"Proof. unfold globalLo, globalHi. destruct encl_{i}. lra. Qed."
        )
    lines.append("")
    lines.append(f"End SpectrumCertified_{ns}.")
    return "\n".join(lines) + "\n"


def emit_enclosure_certificate(
    enclosures: Sequence[Tuple[float, float]], name: str = "Matrix"
) -> EnclosureCertificate:
    """Build discharged Lean 4 + Coq certificates for a global spectral enclosure.

    ``enclosures`` is a sequence of ``(lower, upper)`` certified eigenvalue
    intervals (e.g. from :func:`gaugegap.certify.certify_spectrum`).
    """
    encl = [(float(lo), float(hi)) for (lo, hi) in enclosures]
    if not encl:
        raise ValueError("no enclosures to certify")
    glo = min(lo for lo, _ in encl)
    ghi = max(hi for _, hi in encl)
    ns = _clean_ns(name)
    return EnclosureCertificate(
        name=name, n=len(encl), enclosures=encl,
        global_lower=glo, global_upper=ghi,
        lean4=_lean4(ns, encl, glo, ghi),
        coq=_coq(ns, encl, glo, ghi),
    )
