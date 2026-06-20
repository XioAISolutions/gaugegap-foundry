Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section Bracket_E0.

Variable E : R.

(* TRUST INPUT 1: certified interval lower bound. *)
Hypothesis certified_lower : E >= -12.787631637507566.
(* TRUST INPUT 2: variational (Ritz) upper bound. *)
Hypothesis variational_upper : E <= -12.787631637495053.

Theorem bracket : -12.787631637507566 <= E /\ E <= -12.787631637495053.
Proof. lra. Qed.

End Bracket_E0.
