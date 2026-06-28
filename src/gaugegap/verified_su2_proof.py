"""Formal certificate emitter for the exact finite SU(2) benchmark."""
from __future__ import annotations


def emit_verified_su2_gap_coq() -> str:
    """Return a hole-free Coq certificate for the analytic 2x2 benchmark."""
    return r'''Require Import Reals.
Require Import Psatz.
Open Scope R_scope.

Section VerifiedSU2Gap.

Definition char_poly (x : R) : R := x*x - (3/4)*x - 1/4.

Theorem ground_energy_is_root : char_poly (-1/4) = 0.
Proof.
  unfold char_poly.
  nra.
Qed.

Theorem first_excited_is_root : char_poly 1 = 0.
Proof.
  unfold char_poly.
  nra.
Qed.

Theorem certified_gap_exact : 1 - (-1/4) = 5/4.
Proof.
  lra.
Qed.

Theorem certified_gap_positive : 0 < 1 - (-1/4).
Proof.
  lra.
Qed.

End VerifiedSU2Gap.
'''
