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


@dataclass
class DischargedMonotonicity:
    family: str
    panel: List[int]
    k_zeros: int
    lowers: List[float]
    lean4: str
    coq: str


def _monotone_lean(family: str, panel: List[int], k: int, lowers: List[float]) -> str:
    ns = f"CurveRankCertified.Monotone{family.title().replace('_', '')}"
    label = _FAMILY_LABEL[family]
    conj = " ∧ ".join(f"({lowers[i]!r} < {lowers[i + 1]!r})" for i in range(len(lowers) - 1))
    return f"""import Mathlib.Tactic

namespace {ns}

/-- Certified L2 mismatch lower bounds for the {label} truncations at
    n ∈ {panel}, against the first {k} Riemann zeros. Each entry is a certified
    lower bound on the corresponding M_n (produced by the interval kernel). -/
def L : List ℝ := {lowers!r}

/-- The certified lower bounds are strictly increasing across the tested panel.
    This is a finite statement about the COMPUTED BOUNDS — not a continuum
    monotonicity claim about M_n, and not a proof of the Riemann Hypothesis.
    Discharged by `norm_num` (no proof holes). -/
theorem certified_bounds_strictly_increasing : {conj} := by
  norm_num

end {ns}
"""


def _monotone_coq(family: str, panel: List[int], k: int, lowers: List[float]) -> str:
    sec = f"CurveRankCertified_Monotone_{family}"
    label = _FAMILY_LABEL[family]
    conj = " /\\ ".join(f"({lowers[i]!r} < {lowers[i + 1]!r})" for i in range(len(lowers) - 1))
    return f"""(* Requires Coq >= 8.13 (decimal real literals). *)
Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section {sec}.

(* Certified mismatch lower bounds for the {label} truncations at n in {panel}
   vs the first {k} Riemann zeros; finite statement about the computed bounds. *)

Theorem certified_bounds_strictly_increasing : {conj}.
Proof.
  lra.
Qed.

End {sec}.
"""


def discharged_monotonicity_proof(
    family: str, panel: List[int], k_zeros: int = 20
) -> DischargedMonotonicity:
    """Discharged Lean/Coq proof that the certified lower bounds strictly increase
    across ``panel``. Raises ``ValueError`` if they do not (e.g. dirac_rindler),
    so a monotonicity claim can never pass unless the certificates support it."""
    if len(panel) < 2:
        raise ValueError("monotonicity needs a panel of at least 2 truncations")
    lowers = [float(certified_family_mismatch(family, n, k_zeros).lower) for n in panel]
    for a, b in zip(lowers, lowers[1:]):
        if not a < b:
            raise ValueError(
                f"{family}: certified lower bounds are not strictly increasing "
                f"across {panel}: {lowers}"
            )
    return DischargedMonotonicity(
        family=family, panel=list(panel), k_zeros=k_zeros, lowers=lowers,
        lean4=_monotone_lean(family, panel, k_zeros, lowers),
        coq=_monotone_coq(family, panel, k_zeros, lowers),
    )

