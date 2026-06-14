(* Requires Coq >= 8.13 (decimal real literals). *)
Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section CurveRankCertified_Monotone_xp.

(* Certified mismatch lower bounds for the Berry-Keating xp truncations at n in [10, 15, 20, 25, 30]
   vs the first 20 Riemann zeros; finite statement about the computed bounds. *)

Theorem certified_bounds_strictly_increasing : (27.391322449240906 < 29.390824646996478) /\ (29.390824646996478 < 35.5356899424466) /\ (35.5356899424466 < 36.603410611887064) /\ (36.603410611887064 < 40.00965971015598).
Proof.
  lra.
Qed.

End CurveRankCertified_Monotone_xp.
