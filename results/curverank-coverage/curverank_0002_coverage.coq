(* Discharged coverage certificates emitted by gaugegap.curverank_coverage.
   Requires Coq >= 8.13; uses only the standard library (Reals, Lra).

   CLAIM BOUNDARY: each theorem states that one finite truncation of one
   candidate operator cannot reach a supplied comparison threshold at a stated
   tolerance. These are not statements about the proportion of zeta zeros on the
   critical line, and they neither support nor contradict the Riemann
   Hypothesis. *)
Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section CurveRankCoverage_xp_n16_k12.

(* TRUST INPUT (external to Coq): the certified screen reports that at most
   0 of the 12 zero enclosures are matched within tolerance
   0.5 by the truncated xp spectrum at n = 16.
   The bound comes from interval enclosures with directed rounding; Coq does not
   re-derive it. *)
Variable coverage_xp_n16_k12 : R.
Hypothesis certified_upper_bound_xp_n16_k12 :
  coverage_xp_n16_k12 <= 0 / 1.

Definition comparisonThreshold_xp_n16_k12 : R := 269 / 400.

(* Finite negative result: this truncation cannot reach the supplied comparison
   threshold. Not a statement about the zeta zeros, and not a proof or
   disproof of the Riemann Hypothesis. Discharged by lra; closed with Qed. *)
Theorem coverage_below_threshold_xp_n16_k12 :
  coverage_xp_n16_k12 < comparisonThreshold_xp_n16_k12.
Proof.
  unfold comparisonThreshold_xp_n16_k12.
  lra.
Qed.

End CurveRankCoverage_xp_n16_k12.

Section CurveRankCoverage_xp_n24_k12.

(* TRUST INPUT (external to Coq): the certified screen reports that at most
   1 of the 12 zero enclosures are matched within tolerance
   0.5 by the truncated xp spectrum at n = 24.
   The bound comes from interval enclosures with directed rounding; Coq does not
   re-derive it. *)
Variable coverage_xp_n24_k12 : R.
Hypothesis certified_upper_bound_xp_n24_k12 :
  coverage_xp_n24_k12 <= 1 / 12.

Definition comparisonThreshold_xp_n24_k12 : R := 269 / 400.

(* Finite negative result: this truncation cannot reach the supplied comparison
   threshold. Not a statement about the zeta zeros, and not a proof or
   disproof of the Riemann Hypothesis. Discharged by lra; closed with Qed. *)
Theorem coverage_below_threshold_xp_n24_k12 :
  coverage_xp_n24_k12 < comparisonThreshold_xp_n24_k12.
Proof.
  unfold comparisonThreshold_xp_n24_k12.
  lra.
Qed.

End CurveRankCoverage_xp_n24_k12.

Section CurveRankCoverage_xp_n32_k12.

(* TRUST INPUT (external to Coq): the certified screen reports that at most
   4 of the 12 zero enclosures are matched within tolerance
   0.5 by the truncated xp spectrum at n = 32.
   The bound comes from interval enclosures with directed rounding; Coq does not
   re-derive it. *)
Variable coverage_xp_n32_k12 : R.
Hypothesis certified_upper_bound_xp_n32_k12 :
  coverage_xp_n32_k12 <= 1 / 3.

Definition comparisonThreshold_xp_n32_k12 : R := 269 / 400.

(* Finite negative result: this truncation cannot reach the supplied comparison
   threshold. Not a statement about the zeta zeros, and not a proof or
   disproof of the Riemann Hypothesis. Discharged by lra; closed with Qed. *)
Theorem coverage_below_threshold_xp_n32_k12 :
  coverage_xp_n32_k12 < comparisonThreshold_xp_n32_k12.
Proof.
  unfold comparisonThreshold_xp_n32_k12.
  lra.
Qed.

End CurveRankCoverage_xp_n32_k12.

Section CurveRankCoverage_xp_n40_k12.

(* TRUST INPUT (external to Coq): the certified screen reports that at most
   0 of the 12 zero enclosures are matched within tolerance
   0.5 by the truncated xp spectrum at n = 40.
   The bound comes from interval enclosures with directed rounding; Coq does not
   re-derive it. *)
Variable coverage_xp_n40_k12 : R.
Hypothesis certified_upper_bound_xp_n40_k12 :
  coverage_xp_n40_k12 <= 0 / 1.

Definition comparisonThreshold_xp_n40_k12 : R := 269 / 400.

(* Finite negative result: this truncation cannot reach the supplied comparison
   threshold. Not a statement about the zeta zeros, and not a proof or
   disproof of the Riemann Hypothesis. Discharged by lra; closed with Qed. *)
Theorem coverage_below_threshold_xp_n40_k12 :
  coverage_xp_n40_k12 < comparisonThreshold_xp_n40_k12.
Proof.
  unfold comparisonThreshold_xp_n40_k12.
  lra.
Qed.

End CurveRankCoverage_xp_n40_k12.
