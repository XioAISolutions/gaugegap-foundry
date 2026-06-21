Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section Branching_D3.

Variable Neff : R.

(* TRUST INPUT 1: Tr(rho^2) <= 1  =>  N_eff >= 1. *)
Hypothesis neff_lower : Neff >= 1.
(* TRUST INPUT 2: Tr(rho^2) >= 1/d  =>  N_eff <= d. *)
Hypothesis neff_upper : Neff <= 3.0.

Theorem branch_bracket : 1 <= Neff /\ Neff <= 3.0.
Proof. lra. Qed.

End Branching_D3.
