"""Pre-registered prediction models for the pendulum holdout benchmark."""

from __future__ import annotations

from .blind import BlindModelSpec


def pendulum_model_specs() -> list[BlindModelSpec]:
    return [
        BlindModelSpec(
            key="sensor_fault",
            hypothesis_class="measurement_error",
            statement="The matching periods are caused by unstable period sensors.",
            assumptions=("sensor errors vary across repeats",),
            falsifiers=("stable repeated period readings",),
            predictions={
                "repeat_observation": "unstable_repeat",
                "scale_length_and_gravity": "unspecified",
                "add_equal_length": "unspecified",
                "increase_amplitude": "unspecified",
                "expose_length_sensor": "unspecified",
            },
        ),
        BlindModelSpec(
            key="length_only",
            hypothesis_class="single_parameter_length",
            statement="The period is controlled by pendulum length alone.",
            assumptions=("gravity does not affect the period",),
            falsifiers=("different lengths produce matching periods after a controlled test",),
            predictions={
                "repeat_observation": "stable_repeat",
                "scale_length_and_gravity": "pair_diverges",
                "add_equal_length": "pair_diverges",
                "increase_amplitude": "pair_matches",
                "expose_length_sensor": "latent_difference",
            },
        ),
        BlindModelSpec(
            key="gravity_only",
            hypothesis_class="single_parameter_gravity",
            statement="The period is controlled by gravitational strength alone.",
            assumptions=("length does not affect the period",),
            falsifiers=("different gravity values produce matching periods after a controlled test",),
            predictions={
                "repeat_observation": "stable_repeat",
                "scale_length_and_gravity": "pair_diverges",
                "add_equal_length": "pair_matches",
                "increase_amplitude": "pair_matches",
                "expose_length_sensor": "latent_difference",
            },
        ),
        BlindModelSpec(
            key="length_gravity_ratio",
            hypothesis_class="dimensionless_ratio_equivalence",
            statement=(
                "Within the ideal small-angle regime, the period depends on the "
                "length-to-gravity ratio rather than either latent parameter alone."
            ),
            assumptions=(
                "ideal simple pendulum",
                "small angular amplitude",
                "negligible damping",
                "uniform gravitational field",
            ),
            falsifiers=(
                "equal length-to-gravity ratios produce periods that differ beyond tolerance",
            ),
            predictions={
                "repeat_observation": "stable_repeat",
                "scale_length_and_gravity": "pair_matches",
                "add_equal_length": "pair_diverges",
                "increase_amplitude": "scope_boundary",
                "expose_length_sensor": "latent_difference",
            },
            initial_score=0.25,
        ),
    ]
