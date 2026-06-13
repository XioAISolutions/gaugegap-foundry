"""Discharged formal proofs of the certified separation theorem.

Unlike the generic `formal_export` scaffolds (which leave the proof term as
`sorry`/`Admitted`), this emitter produces proofs that are **actually discharged**
by standard proof-assistant tactics (`linarith` in Lean 4, `lra` in Coq).

The honest structure of a computer-assisted proof over a verified numeric kernel:

    * the interval-arithmetic certificate (verified eigenvalue + zeta-zero
      enclosures, directed rounding) is imported as a SINGLE explicit, labelled
      axiom / hypothesis: ``M >= <certified lower bound>``;
    * the proof assistant then genuinely discharges the remaining real-arithmetic
      step ``M >= separation_threshold`` with no holes.

So the assistant checks the logic + arithmetic; the trust boundary is exactly one
clearly-marked axiom (the certificate). The assistant does NOT re-derive the
spectral computation, and this is NOT a proof of the Riemann Hypothesis — it is
the finite-truncation separation (a negative result).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from gaugegap.curverank_certified import certified_family_mismatch

_FAMILY_LABEL = {
    "xp": "Berry-Keating xp",
    "dirac_rindler": "Dirac-Rindler",
    "quantum_graph": "quantum-graph Laplacian",
}


@dataclass
class DischargedProof:
    family: str
    n: int
    k_zeros: int
    lower_bound: float
    upper_bound: float
    threshold: float
    lean4: str
    coq: str

    @property
    def separated(self) -> bool:
        return self.lower_bound > self.threshold


def _ident(family: str, n: int) -> str:
    return f"{family}_n{n}".replace("-", "_")


def _lean4(family: str, n: int, k: int, lower: float, thr: float) -> str:
    ns = f"CurveRankCertified.{_ident(family, n).title().replace('_', '')}"
    label = _FAMILY_LABEL[family]
    return f"""import Mathlib.Tactic

namespace {ns}

/-- The certified L2 spectral mismatch `M` between the {label} truncation
    (n = {n}) and the first {k} Riemann zeros. `M` is abstract; its only used
    property is the certified lower bound below. -/
axiom M : ℝ

/-- TRUST INPUT — interval-arithmetic certificate (external to Lean, produced by
    directed-rounding verified Hermitian eigenvalue enclosures and Arb-certified
    zeta-zero enclosures): `M ≥ {lower!r}`. This is the single axiom; everything
    below is discharged by Lean. -/
axiom certified_lower_bound : M ≥ {lower!r}

/-- Separation (impossibility) margin. -/
def separationThreshold : ℝ := {thr!r}

/-- Separation theorem (finite truncation, NOT the Riemann Hypothesis): the
    certified mismatch is bounded away from zero by the threshold. Fully
    discharged by `linarith` from the certificate (no proof holes). -/
theorem separated_from_zeros : M ≥ separationThreshold := by
  have h := certified_lower_bound
  unfold separationThreshold
  linarith

end {ns}
"""


def _coq(family: str, n: int, k: int, lower: float, thr: float) -> str:
    sec = f"CurveRankCertified_{_ident(family, n)}"
    label = _FAMILY_LABEL[family]
    return f"""(* Requires Coq >= 8.13 (decimal real literals) and Coquelicot-free Lra. *)
Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section {sec}.

(* Certified L2 spectral mismatch between the {label} truncation (n = {n}) and
   the first {k} Riemann zeros; abstract real. *)
Variable M : R.

(* TRUST INPUT: interval-arithmetic certificate (external to Coq). *)
Hypothesis certified_lower_bound : M >= {lower!r}.

Definition separationThreshold : R := {thr!r}.

(* Separation theorem (finite truncation; not the Riemann Hypothesis).
   Discharged by lra from the certificate -- closed with Qed (no proof holes). *)
Theorem separated_from_zeros : M >= separationThreshold.
Proof.
  unfold separationThreshold.
  lra.
Qed.

End {sec}.
"""


def discharged_separation_proof(
    family: str, n: int, k_zeros: int = 20, threshold: float = 1.0, **kwargs
) -> DischargedProof:
    """Build discharged Lean 4 + Coq separation proofs for one family/truncation."""
    iv = certified_family_mismatch(family, n, k_zeros, **kwargs)
    lower, upper = iv.to_tuple()
    lower_f, thr_f = float(lower), float(threshold)
    if lower_f <= thr_f:
        raise ValueError(
            f"{family} n={n}: certified lower bound {lower_f} does not exceed "
            f"threshold {thr_f}; no separation to prove."
        )
    return DischargedProof(
        family=family, n=n, k_zeros=k_zeros,
        lower_bound=lower_f, upper_bound=float(upper), threshold=thr_f,
        lean4=_lean4(family, n, k_zeros, lower_f, thr_f),
        coq=_coq(family, n, k_zeros, lower_f, thr_f),
    )


def all_family_proofs(
    n: int, k_zeros: int = 20, threshold: float = 1.0
) -> List[DischargedProof]:
    return [
        discharged_separation_proof(fam, n, k_zeros, threshold)
        for fam in ("xp", "dirac_rindler", "quantum_graph")
    ]
