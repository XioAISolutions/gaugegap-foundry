Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section Cherenkov_Cone.

(* c = cos(theta_c), nb = n*beta. *)
Variable c nb : R.

(* TRUST INPUT 1: at/above threshold n*beta >= 1. *)
Hypothesis above_threshold : nb >= 1.
(* TRUST INPUT 2: the cone cosine is positive. *)
Hypothesis cos_pos : c > 0.
(* TRUST INPUT 3: the Cherenkov relation cos(theta_c) * (n beta) = 1. *)
Hypothesis cherenkov_relation : c * nb = 1.

Theorem cone_valid : 0 < c /\ c <= 1.
Proof. split; nra. Qed.

End Cherenkov_Cone.
