Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section Ergotropy_WExtractable.

Variable W : R.

(* TRUST INPUT 1: passive state minimizes cyclic energy => W >= 0. *)
Hypothesis work_nonneg : W >= 0.
(* TRUST INPUT 2: passive energy >= ground energy E0 => W <= <H> - E0. *)
Hypothesis work_bounded : W <= 2.0000000000000004.

Theorem no_free_energy : 0 <= W /\ W <= 2.0000000000000004.
Proof. lra. Qed.

End Ergotropy_WExtractable.
