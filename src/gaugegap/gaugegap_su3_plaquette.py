"""Exact single-plaquette SU(3) lattice gauge model in the character basis.

This module supplies the exact SU(3) building block the multi-plaquette scaffold
(:mod:`gaugegap.gaugegap_su3_pure`) is still missing: a genuinely gauge-invariant
Kogut-Susskind Hamiltonian with a *real* magnetic term and a *real* Wilson loop,
for the one case where it is exactly tractable.

For a single plaquette, gauge fixing reduces pure gauge theory to quantum mechanics
on the group manifold, and every physical (gauge-invariant) state is a class
function of the plaquette holonomy ``U``. In the character basis ``{|p,q⟩}`` of
SU(3) irreps:

* the electric term is diagonal: ``H_E = (g²/2) C₂(p,q)`` with
  ``C₂ = (p² + q² + pq + 3p + 3q)/3``;
* multiplication by ``Tr U = χ_(1,0)(U)`` acts by the exact fusion rule
  ``(p,q) ⊗ (1,0) = (p+1,q) ⊕ (p−1,q+1) ⊕ (p,q−1)`` (all multiplicities one), and
  ``Tr U†`` is its transpose, so the magnetic term
  ``H_B = −(1/g²)·Re Tr U = −(1/(2g²))(M + Mᵀ)`` is an exact sparse hopping;
* the Wilson loop of the (only) 1×1 loop is the ground-state expectation
  ``W = ⟨(1/3) Re Tr U⟩``.

Gauss's law is satisfied **by construction**: the character basis contains only
gauge-invariant states. Truncation keeps irreps with ``p + q ≤ Λ`` and is
convergence-controlled (observables stabilize as Λ grows).

CLAIM BOUNDARY: exact finite truncation of the *single-plaquette* SU(3) Hamiltonian
under the stated convention. It is a defensible toy and known-answer anchor — not a
multi-plaquette lattice, not a continuum limit, and not a Yang-Mills mass-gap claim.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

IMPLEMENTATION_STATUS = "exact_finite_truncation"
CLAIM_BOUNDARY = (
    "exact single-plaquette SU(3) character-basis truncation only; not a "
    "multi-plaquette lattice, continuum limit, or Yang-Mills mass-gap claim"
)


def irrep_basis(cutoff: int) -> list[tuple[int, int]]:
    """All SU(3) irreps (p, q) with p + q <= cutoff, in a deterministic order."""
    if cutoff < 1:
        raise ValueError("cutoff must be >= 1")
    return [(p, q) for p in range(cutoff + 1) for q in range(cutoff + 1) if p + q <= cutoff]


def casimir(p: int, q: int) -> float:
    """Quadratic Casimir C2(p, q) = (p^2 + q^2 + pq + 3p + 3q)/3."""
    return (p * p + q * q + p * q + 3 * p + 3 * q) / 3.0


def dimension(p: int, q: int) -> int:
    """dim(p, q) = (p+1)(q+1)(p+q+2)/2."""
    return (p + 1) * (q + 1) * (p + q + 2) // 2


def fuse_fundamental(p: int, q: int) -> list[tuple[int, int]]:
    """Exact Clebsch-Gordan series (p,q) ⊗ (1,0); every multiplicity is one."""
    out = [(p + 1, q)]
    if p >= 1:
        out.append((p - 1, q + 1))
    if q >= 1:
        out.append((p, q - 1))
    return out


def fusion_dimension_identity(max_label: int = 6) -> bool:
    """Known answer: 3·dim(p,q) equals the summed dimensions of (p,q) ⊗ (1,0)."""
    return all(
        3 * dimension(p, q) == sum(dimension(*r) for r in fuse_fundamental(p, q))
        for p in range(max_label)
        for q in range(max_label)
    )


@dataclass(frozen=True)
class SU3PlaquetteResult:
    coupling: float
    cutoff: int
    basis_size: int
    ground_energy: float
    gap: float
    strong_coupling_gap: float
    wilson_loop_1x1: float
    gauss_law_by_construction: bool
    claim_boundary: str


def trace_operator(cutoff: int) -> np.ndarray:
    """Matrix of multiplication by χ_(1,0)(U) = Tr U in the truncated basis."""
    basis = irrep_basis(cutoff)
    index = {r: i for i, r in enumerate(basis)}
    m = np.zeros((len(basis), len(basis)))
    for r in basis:
        for rp in fuse_fundamental(*r):
            if rp in index:
                m[index[rp], index[r]] += 1.0
    return m


def hamiltonian_dense(coupling: float, cutoff: int) -> np.ndarray:
    """H = (g²/2)·diag(C₂) − (1/(2g²))(M + Mᵀ) in the truncated character basis."""
    if coupling <= 0:
        raise ValueError("coupling must be positive")
    basis = irrep_basis(cutoff)
    m = trace_operator(cutoff)
    h_e = np.diag([casimir(*r) for r in basis]) * (coupling * coupling / 2.0)
    h_b = -(1.0 / (coupling * coupling)) * 0.5 * (m + m.T)
    return h_e + h_b


def solve_plaquette(coupling: float, cutoff: int) -> SU3PlaquetteResult:
    """Exact diagonalization of the truncated single-plaquette Hamiltonian."""
    h = hamiltonian_dense(coupling, cutoff)
    m = trace_operator(cutoff)
    eigenvalues, eigenvectors = np.linalg.eigh(h)
    ground = eigenvectors[:, 0]
    wilson = float(ground @ (0.5 * (m + m.T) / 3.0) @ ground)
    return SU3PlaquetteResult(
        coupling=coupling,
        cutoff=cutoff,
        basis_size=h.shape[0],
        ground_energy=float(eigenvalues[0]),
        gap=float(eigenvalues[1] - eigenvalues[0]),
        strong_coupling_gap=(coupling * coupling / 2.0) * casimir(1, 0),
        wilson_loop_1x1=wilson,
        gauss_law_by_construction=True,
        claim_boundary=CLAIM_BOUNDARY,
    )


def emit_gap_certificate(coupling: float) -> tuple[str, str, float]:
    """Discharged Lean 4 / Coq proof that the strong-coupling mass gap is positive.

    The strong-coupling gap is ``m = (g²/2)·C₂(1,0)`` with ``C₂(1,0) = 4/3``. Trust
    inputs: ``g > 0`` (positive coupling) and ``c = 4/3 > 0`` (the fundamental
    Casimir); the assistant discharges ``m = (g²/2)·c > 0`` with positivity tactics.
    """
    g = float(coupling)
    c2_fund = casimir(1, 0)
    floor = (g * g / 2.0) * c2_fund
    lean = f"""import Mathlib.Tactic

namespace SU3Plaquette.Gap

/-- Coupling g and the fundamental quadratic Casimir c = C2(1,0) = 4/3 (abstract
    reals; only the labelled trust facts are used). -/
axiom g : ℝ
axiom c : ℝ

/-- TRUST INPUT 1 -- positive gauge coupling. -/
axiom g_pos : g > 0
/-- TRUST INPUT 2 -- positive fundamental Casimir (C2(1,0) = 4/3). -/
axiom c_pos : c > 0

/-- The strong-coupling single-plaquette mass gap (g²/2)·c is positive (no holes). -/
theorem gap_pos : (g * g / 2) * c > 0 := by
  have hg2 : g * g > 0 := mul_pos g_pos g_pos
  positivity

end SU3Plaquette.Gap
"""
    coq = f"""Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section SU3Plaquette_Gap.

(* Coupling g and the fundamental quadratic Casimir c = C2(1,0) = 4/3. *)
Variable g c : R.

(* TRUST INPUT 1: positive gauge coupling. *)
Hypothesis g_pos : g > 0.
(* TRUST INPUT 2: positive fundamental Casimir (C2(1,0) = 4/3). *)
Hypothesis c_pos : c > 0.

Theorem gap_pos : (g * g / 2) * c > 0.
Proof.
  assert (Hg2 : g * g > 0) by (apply Rmult_lt_0_compat; lra).
  nra.
Qed.

End SU3Plaquette_Gap.
"""
    return lean, coq, floor


def truncation_convergence(coupling: float, cutoffs: tuple[int, ...] = (3, 5, 8)) -> dict[str, object]:
    """Gap and Wilson loop across cutoffs; successive differences must shrink."""
    rows = [solve_plaquette(coupling, c) for c in cutoffs]
    gaps = [r.gap for r in rows]
    diffs = [abs(gaps[i + 1] - gaps[i]) for i in range(len(gaps) - 1)]
    return {
        "coupling": coupling,
        "cutoffs": list(cutoffs),
        "gaps": gaps,
        "wilson_loops": [r.wilson_loop_1x1 for r in rows],
        "gap_differences": diffs,
        "converging": all(diffs[i + 1] <= diffs[i] + 1e-12 for i in range(len(diffs) - 1)),
    }
