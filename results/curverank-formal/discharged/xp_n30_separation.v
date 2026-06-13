(* Requires Coq >= 8.13 (decimal real literals) and Coquelicot-free Lra. *)
Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section CurveRankCertified_xp_n30.

(* Certified L2 spectral mismatch between the Berry-Keating xp truncation (n = 30) and
   the first 20 Riemann zeros; abstract real. *)
Variable M : R.

(* TRUST INPUT: interval-arithmetic certificate (external to Coq). *)
Hypothesis certified_lower_bound : M >= 40.00965971015598.

Definition separationThreshold : R := 1.0.

(* Separation theorem (finite truncation; not the Riemann Hypothesis).
   Discharged by lra from the certificate -- closed with Qed (no proof holes). *)
Theorem separated_from_zeros : M >= separationThreshold.
Proof.
  unfold separationThreshold.
  lra.
Qed.

End CurveRankCertified_xp_n30.
