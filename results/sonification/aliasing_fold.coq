Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section Nyquist_Alias.

Variable fs f : R.

(* TRUST INPUT 1: tone above the Nyquist frequency. *)
Hypothesis over_nyquist : f > fs / 2.
(* TRUST INPUT 2: but below the sampling rate. *)
Hypothesis below_rate : f < fs.

Theorem aliasing_fold : 0 < fs - f /\ fs - f < fs / 2.
Proof. split; lra. Qed.

End Nyquist_Alias.
