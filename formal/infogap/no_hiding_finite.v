Require Import Reals.
Require Import Psatz.
Open Scope R_scope.

(*
  Finite algebraic certificate for the implemented three-qubit circuit.

  Scope:
    |psi>_S |00>_AB -> |Phi+>_SA |psi>_B

  The variables ar, ai, br, bi are the real and imaginary components of
  alpha and beta.  The scalar h is the Hadamard amplitude 1/sqrt(2), used
  only through h^2 = 1/2.  These theorems certify the probability identities
  used by the finite implementation; they are not a formalization of the
  general no-hiding theorem.
*)

Section FiniteNoHiding.

Variables ar ai br bi h : R.
Hypothesis input_normalized :
  ar * ar + ai * ai + br * br + bi * bi = 1.
Hypothesis hadamard_weight : h * h = / 2.

Definition alpha_probability : R := ar * ar + ai * ai.
Definition beta_probability : R := br * br + bi * bi.

Theorem input_probability_normalized :
  alpha_probability + beta_probability = 1.
Proof.
  unfold alpha_probability, beta_probability.
  exact input_normalized.
Qed.

Theorem system_zero_probability :
  (h * ar) * (h * ar) +
  (h * ai) * (h * ai) +
  (h * br) * (h * br) +
  (h * bi) * (h * bi) = / 2.
Proof.
  replace
    ((h * ar) * (h * ar) +
     (h * ai) * (h * ai) +
     (h * br) * (h * br) +
     (h * bi) * (h * bi))
    with ((h * h) * (ar * ar + ai * ai + br * br + bi * bi)) by ring.
  rewrite hadamard_weight, input_normalized.
  ring.
Qed.

Theorem system_one_probability :
  (h * ar) * (h * ar) +
  (h * ai) * (h * ai) +
  (h * br) * (h * br) +
  (h * bi) * (h * bi) = / 2.
Proof.
  apply system_zero_probability.
Qed.

Theorem recovery_zero_probability :
  2 * ((h * ar) * (h * ar) + (h * ai) * (h * ai)) =
  alpha_probability.
Proof.
  unfold alpha_probability.
  replace
    (2 * ((h * ar) * (h * ar) + (h * ai) * (h * ai)))
    with ((2 * (h * h)) * (ar * ar + ai * ai)) by ring.
  rewrite hadamard_weight.
  ring.
Qed.

Theorem recovery_one_probability :
  2 * ((h * br) * (h * br) + (h * bi) * (h * bi)) =
  beta_probability.
Proof.
  unfold beta_probability.
  replace
    (2 * ((h * br) * (h * br) + (h * bi) * (h * bi)))
    with ((2 * (h * h)) * (br * br + bi * bi)) by ring.
  rewrite hadamard_weight.
  ring.
Qed.

Theorem recovered_probability_normalized :
  2 * ((h * ar) * (h * ar) + (h * ai) * (h * ai)) +
  2 * ((h * br) * (h * br) + (h * bi) * (h * bi)) = 1.
Proof.
  rewrite recovery_zero_probability, recovery_one_probability.
  apply input_probability_normalized.
Qed.

End FiniteNoHiding.
