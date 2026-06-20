Require Import ZArith.
Require Import Lia.
Open Scope Z_scope.

Section WeightSymmetry_P2Q0.

Theorem balanced_coord0 : (-2) + (-2) + (1) + (-2) + (1) + (4) = 0%Z.
Proof. lia. Qed.
Theorem balanced_coord1 : (-2) + (1) + (-2) + (4) + (1) + (-2) = 0%Z.
Proof. lia. Qed.
Theorem balanced_coord2 : (4) + (1) + (1) + (-2) + (-2) + (-2) = 0%Z.
Proof. lia. Qed.

End WeightSymmetry_P2Q0.
