(* Requires Coq >= 8.13 (decimal real literals) and Coquelicot-free Lra. *)
Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section CurveRankCertified_quantum_graph_n20.

(* Certified L2 spectral mismatch between the quantum-graph Laplacian truncation (n = 20) and
   the first 20 Riemann zeros; abstract real. *)
Variable M : R.

(* TRUST INPUT: interval-arithmetic certificate (external to Coq). *)
Hypothesis certified_lower_bound : M >= 76.1657160545473.

Definition separationThreshold : R := 1.0.

(* Separation theorem (finite truncation; not the Riemann Hypothesis).
   Discharged by lra from the certificate -- closed with Qed (no proof holes). *)
Theorem separated_from_zeros : M >= separationThreshold.
Proof.
  unfold separationThreshold.
  lra.
Qed.

End CurveRankCertified_quantum_graph_n20.
