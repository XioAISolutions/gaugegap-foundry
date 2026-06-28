Require Import Reals.
Require Import Psatz.
Open Scope R_scope.

Section VerifiedSU2Gap.

Definition char_poly (x : R) : R := x*x - (3/4)*x - 1/4.

Theorem ground_energy_is_root : char_poly (-1/4) = 0.
Proof.
  unfold char_poly.
  norm_num.
Qed.

Theorem first_excited_is_root : char_poly 1 = 0.
Proof.
  unfold char_poly.
  norm_num.
Qed.

Theorem certified_gap_exact : 1 - (-1/4) = 5/4.
Proof.
  norm_num.
Qed.

Theorem certified_gap_positive : 0 < 1 - (-1/4).
Proof.
  norm_num.
Qed.

End VerifiedSU2Gap.
