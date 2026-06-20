Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section Bracket_E0Temple.

Variable E : R.

(* TRUST INPUT 1: certified interval lower bound. *)
Hypothesis certified_lower : E >= -3.493959207442449.
(* TRUST INPUT 2: variational (Ritz) upper bound. *)
Hypothesis variational_upper : E <= -3.488277972662546.

Theorem bracket : -3.493959207442449 <= E /\ E <= -3.488277972662546.
Proof. lra. Qed.

End Bracket_E0Temple.
