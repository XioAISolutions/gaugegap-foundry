Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section LiebRobinson_Front.

Variable vf vlr t : R.

(* TRUST INPUT 1: front velocity respects the Lieb-Robinson speed. *)
Hypothesis front_bounded : vf <= vlr.
(* TRUST INPUT 2: time is non-negative. *)
Hypothesis time_nonneg : t >= 0.

Theorem light_cone : vf * t <= vlr * t.
Proof. nra. Qed.

End LiebRobinson_Front.
