Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section TimeBandwidth_Tb.

(* Temporal width st and spectral width sw. *)
Variable st sw : R.

(* TRUST INPUT: Fourier uncertainty (Gabor), denominator cleared:
   sw * (2 * st) >= 1  (i.e. sw >= 1 / (2 st)). *)
Hypothesis fourier_uncertainty : sw * (2 * st) >= 1.

Theorem time_bandwidth : st * sw >= 1 / 2.
Proof. nra. Qed.

End TimeBandwidth_Tb.
