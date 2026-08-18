Require Import ZArith.
Require Import List.
Require Import Lia.
Import ListNotations.
Open Scope Z_scope.

(*
  Finite certificate for the arithmetic identity the Hadamard Forge verifier
  actually executes.

  The verifier never materializes a +-1 matrix: each row is a bitmask, and the
  inner product of rows u and v is computed as

      <u, v> = n - 2 * popcount(u XOR v)

  where n is the order and popcount(u XOR v) counts the positions where the two
  rows disagree.  The theorems below certify that this popcount form equals the
  textbook sum-of-products over the +-1 alphabet, that the diagonal case yields
  exactly n, and that a vanishing inner product forces the length to be even.

  Scope:
    Statements about a single pair of finite +-1 vectors of equal length.

  This is NOT a formalization of the Hadamard conjecture, and NOT the theorem
  that an order n >= 3 admitting a Hadamard matrix must satisfy 4 | n.  It
  certifies the exact integer arithmetic performed by the verifier and one
  elementary necessary condition (even length) that follows from it.
*)

Section GramIdentity.

Inductive sign : Type := Pos | Neg.

Definition value (s : sign) : Z :=
  match s with
  | Pos => 1
  | Neg => -1
  end.

Definition disagree (a b : sign) : Z :=
  match a, b with
  | Pos, Pos => 0
  | Neg, Neg => 0
  | _, _ => 1
  end.

(* Textbook inner product over the +-1 alphabet. *)
Fixpoint inner (u v : list sign) : Z :=
  match u, v with
  | a :: u', b :: v' => value a * value b + inner u' v'
  | _, _ => 0
  end.

(* The quantity the implementation obtains from popcount(u XOR v). *)
Fixpoint mismatches (u v : list sign) : Z :=
  match u, v with
  | a :: u', b :: v' => disagree a b + mismatches u' v'
  | _, _ => 0
  end.

Lemma disagree_bounds : forall a b, 0 <= disagree a b <= 1.
Proof.
  intros a b; destruct a; destruct b; simpl; lia.
Qed.

Lemma product_from_disagree :
  forall a b, value a * value b = 1 - 2 * disagree a b.
Proof.
  intros a b; destruct a; destruct b; simpl; reflexivity.
Qed.

Lemma mismatches_nonnegative :
  forall u v, 0 <= mismatches u v.
Proof.
  induction u as [| a u' IH]; intros v; simpl.
  - lia.
  - destruct v as [| b v']; simpl.
    + lia.
    + specialize (IH v'). pose proof (disagree_bounds a b). lia.
Qed.

(* Core identity: the popcount form the verifier computes agrees with the
   sum-of-products definition on vectors of equal length. *)
Theorem inner_eq_popcount_form :
  forall u v,
    length u = length v ->
    inner u v = Z.of_nat (length u) - 2 * mismatches u v.
Proof.
  induction u as [| a u' IH]; intros v Hlen.
  - cbn [inner mismatches length]. lia.
  - destruct v as [| b v'].
    + cbn [length] in Hlen. discriminate Hlen.
    + cbn [length] in Hlen. injection Hlen as Hlen'.
      specialize (IH v' Hlen').
      cbn [inner mismatches length].
      rewrite product_from_disagree, IH, Nat2Z.inj_succ.
      lia.
Qed.

Lemma mismatches_self : forall u, mismatches u u = 0.
Proof.
  induction u as [| a u' IH]; simpl.
  - reflexivity.
  - destruct a; simpl; lia.
Qed.

(* Diagonal gate: every diagonal entry of H * H^T equals the order. *)
Theorem inner_self_eq_length :
  forall u, inner u u = Z.of_nat (length u).
Proof.
  intros u.
  rewrite inner_eq_popcount_form by reflexivity.
  rewrite mismatches_self.
  lia.
Qed.

(* Off-diagonal gate, contrapositive form: orthogonal +-1 rows of equal length
   force that length to be even.  This is the elementary half of the necessary
   condition on Hadamard orders; the 4 | n statement is strictly stronger and is
   not proved here. *)
Theorem orthogonal_length_even :
  forall u v,
    length u = length v ->
    inner u v = 0 ->
    Z.of_nat (length u) = 2 * mismatches u v.
Proof.
  intros u v Hlen Horth.
  rewrite inner_eq_popcount_form in Horth by exact Hlen.
  lia.
Qed.

Corollary orthogonal_length_is_even :
  forall u v,
    length u = length v ->
    inner u v = 0 ->
    Z.Even (Z.of_nat (length u)).
Proof.
  intros u v Hlen Horth.
  exists (mismatches u v).
  apply orthogonal_length_even; assumption.
Qed.

End GramIdentity.
