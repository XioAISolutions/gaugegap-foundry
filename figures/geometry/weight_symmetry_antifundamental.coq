Require Import ZArith.
Require Import Lia.
Open Scope Z_scope.

Section WeightSymmetry_P0Q1.

Theorem balanced_coord0 : (-2) + (1) + (1) = 0%Z.
Proof. lia. Qed.
Theorem balanced_coord1 : (1) + (-2) + (1) = 0%Z.
Proof. lia. Qed.
Theorem balanced_coord2 : (1) + (1) + (-2) = 0%Z.
Proof. lia. Qed.

End WeightSymmetry_P0Q1.
