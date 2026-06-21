Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section SpeedLimit_TBuildup.

Variable t : R.

(* TRUST INPUT 1: Mandelstam-Tamm quantum speed limit. *)
Hypothesis mandelstam_tamm : t >= 0.29860027962613517.
(* TRUST INPUT 2: Margolus-Levitin quantum speed limit. *)
Hypothesis margolus_levitin : t >= 0.29860027962613517.

Theorem respects_qsl : t >= 0.29860027962613517.
Proof. lra. Qed.

End SpeedLimit_TBuildup.
