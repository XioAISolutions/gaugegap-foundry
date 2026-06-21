Require Import Reals.
Require Import Lra.
Require Import Rdefinitions.
Open Scope R_scope.

Section WarpEnergy_Warp.

(* K = v_s^2 (y^2+z^2) / (4 r_s^2); s = f'(r_s)^2. *)
Variable K s : R.

(* TRUST INPUT 1: K is a ratio of squares, hence non-negative. *)
Hypothesis K_nonneg : K >= 0.
(* TRUST INPUT 2: s = f'(r_s)^2 is a square, hence non-negative. *)
Hypothesis s_nonneg : s >= 0.
(* PI > 0 (so the positive coefficient 1/(8*PI) is well defined). *)
Hypothesis pi_pos : PI > 0.

Theorem rho_nonpos : - (1 / (8 * PI)) * K * s <= 0.
Proof.
  assert (Hco : 1 / (8 * PI) > 0) by (apply Rlt_gt; apply Rdiv_lt_0_compat; lra).
  assert (Hks : K * s >= 0) by (apply Rle_ge; apply Rmult_le_pos; lra).
  nra.
Qed.

End WarpEnergy_Warp.
