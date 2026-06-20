Require Import ZArith.
Require Import Lia.
Open Scope Z_scope.

Section WeightSymmetry_P1Q1.

Theorem balanced_coord0 : (-3) + (0) + (-3) + (0) + (3) + (0) + (3) = 0%Z.
Proof. lia. Qed.
Theorem balanced_coord1 : (0) + (-3) + (3) + (0) + (-3) + (3) + (0) = 0%Z.
Proof. lia. Qed.
Theorem balanced_coord2 : (3) + (3) + (0) + (0) + (0) + (-3) + (-3) = 0%Z.
Proof. lia. Qed.

End WeightSymmetry_P1Q1.
