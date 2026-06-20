"""Discharged Lean 4 / Coq certificate for a two-sided eigenvalue bracket.

Given two trust inputs -- a certified lower bound (interval kernel) and a
variational upper bound (a quantum Ritz value, an upper bound by Courant-Fischer)
-- the proof assistant discharges ``lower <= E <= upper`` with no holes
(Lean ``linarith`` / Coq ``lra``). Same honest structure as the separation /
enclosure certificates: the assistant checks the real-arithmetic logic; the two
bounds are the labelled axioms.

CLAIM BOUNDARY: a verified statement about a finite-matrix eigenvalue, not a
continuum or Millennium claim.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BracketCertificate:
    label: str
    lower: float
    upper: float
    lean4: str
    coq: str

    def to_dict(self) -> dict:
        return {
            "kind": "eigenvalue_bracket_certificate",
            "label": self.label, "lower": self.lower, "upper": self.upper,
            "lean4": self.lean4, "coq": self.coq,
            "trust_inputs": ("certified interval lower bound; variational (Ritz) "
                             "upper bound"),
        }


def _ns(label: str) -> str:
    base = "".join(ch for ch in label.title() if ch.isalnum()) or "E"
    return base if not base[0].isdigit() else "E" + base


def emit_bracket_certificate(label: str, lower: float, upper: float
                             ) -> BracketCertificate:
    """Discharged Lean4 + Coq proof that ``lower <= E <= upper`` for eigenvalue E."""
    if lower > upper:
        raise ValueError(f"empty bracket: lower {lower} > upper {upper}")
    ns = _ns(label)
    lean = f"""import Mathlib.Tactic

namespace Bracket.{ns}

/-- The eigenvalue E (abstract); the only used facts are the two certified bounds. -/
axiom E : ℝ

/-- TRUST INPUT 1 -- certified lower bound from the interval-arithmetic kernel. -/
axiom certified_lower : E ≥ {lower!r}

/-- TRUST INPUT 2 -- variational (Ritz) upper bound: <psi|H|psi> >= E by
    Courant-Fischer, supplied by the quantum subspace eigensolver. -/
axiom variational_upper : E ≤ {upper!r}

/-- Two-sided certified bracket, discharged by linarith (no holes). -/
theorem bracket : {lower!r} ≤ E ∧ E ≤ {upper!r} := by
  constructor
  · linarith [certified_lower]
  · linarith [variational_upper]

end Bracket.{ns}
"""
    coq = f"""Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section Bracket_{ns}.

Variable E : R.

(* TRUST INPUT 1: certified interval lower bound. *)
Hypothesis certified_lower : E >= {lower!r}.
(* TRUST INPUT 2: variational (Ritz) upper bound. *)
Hypothesis variational_upper : E <= {upper!r}.

Theorem bracket : {lower!r} <= E /\\ E <= {upper!r}.
Proof. lra. Qed.

End Bracket_{ns}.
"""
    return BracketCertificate(label=label, lower=float(lower), upper=float(upper),
                              lean4=lean, coq=coq)
