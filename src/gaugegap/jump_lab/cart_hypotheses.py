"""Competing causal explanations for the force-to-mass cart benchmark."""

from __future__ import annotations

from .hypotheses import Hypothesis


def default_cart_hypotheses() -> list[Hypothesis]:
    return [
        Hypothesis(
            "C1",
            "measurement_error",
            "The matching trajectories are caused by unstable or aliased kinematic sensors.",
            ["sensor errors change across repeated observations"],
            ["stable repeated observations in both boxes"],
            score=0.35,
        ),
        Hypothesis(
            "C2",
            "identical_hidden_parameters",
            "The two carts have the same hidden force and the same hidden mass.",
            ["latent force and mass values are equal"],
            ["a direct latent measurement differs or an equal payload breaks the match"],
            score=0.45,
        ),
        Hypothesis(
            "C3",
            "active_trajectory_controller",
            "A hidden controller forces both carts to follow a prescribed trajectory.",
            ["kinematics are imposed independently of force and mass"],
            ["kinematics respond quantitatively to force-to-mass interventions"],
            score=0.40,
        ),
        Hypothesis(
            "C4",
            "force_mass_ratio_equivalence",
            "Different constant forces and masses can produce equal kinematic trajectories when their force-to-mass ratios and initial conditions match.",
            [
                "frictionless one-dimensional motion",
                "constant net force",
                "matched initial velocity and observation duration",
                "non-relativistic conditions",
            ],
            [
                "matched force-to-mass ratios produce different kinematics beyond tolerance under the stated assumptions"
            ],
            score=0.50,
        ),
    ]
