"""Discharged certificate of an su(3) weight diagram's symmetry invariant.

Makes the geometric symmetry a *first-class verified claim*, in the same honest
style as ``curverank_formal_emit``: the multiplicity-weighted weight vectors sum to
zero (the diagram is balanced about the origin). In the sum-zero R^3 embedding each
coordinate is a multiple of 1/3, so ``3 * coord`` is an integer and the balance is
an EXACT integer identity, discharged by Lean ``norm_num`` / Coq ``lra`` (no holes,
no floating point). The Weyl-orbit closure (S3 symmetry) is reported with an
explicit witness count.

CLAIM BOUNDARY: a verified statement about su(3) representation-theory data, not a
physics claim.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from gaugegap.visualization.weight_diagrams import (
    su3_weights, su3_dimension, weyl_orbit_closed,
)


@dataclass
class WeightCertificate:
    dynkin: tuple
    dimension: int
    weyl_orbit_closed: bool
    coord_terms: List[List[int]]   # per coordinate: [mult_i * 3*coord_i]
    lean4: str
    coq: str

    def to_dict(self) -> dict:
        return {
            "kind": "weight_symmetry_certificate",
            "dynkin": list(self.dynkin),
            "dimension": self.dimension,
            "weyl_orbit_closed": self.weyl_orbit_closed,
            "balanced_about_origin": all(sum(t) == 0 for t in self.coord_terms),
            "lean4": self.lean4,
            "coq": self.coq,
        }


def _ns(p: int, q: int) -> str:
    return f"P{p}Q{q}"


def _expr(terms: List[int]) -> str:
    return " + ".join(f"({t})" for t in terms) if terms else "0"


def weight_symmetry_certificate(p: int, q: int) -> WeightCertificate:
    ws = su3_weights(p, q)
    # 3*coord is an exact integer; weight each by multiplicity.
    coord_terms: List[List[int]] = [[], [], []]
    for w in ws:
        for k in range(3):
            coord_terms[k].append(int(w["mult"]) * int(round(3 * w["r3"][k])))
    for k, terms in enumerate(coord_terms):
        if sum(terms) != 0:
            raise ValueError(f"coordinate {k} not balanced: sum={sum(terms)}")

    ns = _ns(p, q)
    lean_lines = ["import Mathlib.Tactic", "", f"namespace WeightSymmetry.{ns}", "",
                  f"/-- su(3) irrep (p,q)=({p},{q}), dim {su3_dimension(p, q)}. The "
                  "multiplicity-weighted\n    weights sum to zero (balanced about the "
                  "origin) — exact integer identity\n    (3*coord), discharged by "
                  "norm_num. A verifiable symmetry invariant. -/"]
    for k in range(3):
        lean_lines.append(
            f"theorem balanced_coord{k} : ({_expr(coord_terms[k])} : ℤ) = 0 := by "
            f"norm_num")
    lean_lines += ["", f"end WeightSymmetry.{ns}", ""]
    coq_lines = ["Require Import ZArith.", "Require Import Lia.", "Open Scope Z_scope.",
                 "", f"Section WeightSymmetry_{ns}.", ""]
    for k in range(3):
        coq_lines.append(
            f"Theorem balanced_coord{k} : {_expr(coord_terms[k])} = 0%Z.\n"
            f"Proof. lia. Qed.")
    coq_lines += ["", f"End WeightSymmetry_{ns}.", ""]

    return WeightCertificate(
        dynkin=(p, q), dimension=su3_dimension(p, q),
        weyl_orbit_closed=weyl_orbit_closed(ws),
        coord_terms=coord_terms,
        lean4="\n".join(lean_lines), coq="\n".join(coq_lines),
    )
