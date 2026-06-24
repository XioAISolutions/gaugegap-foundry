"""Survivorship bias, reduced to its exactly-computable core (Wald's bombers).

Abraham Wald's WWII problem (Statistical Research Group, 1943) as a toy model.  Bombers
return from missions covered in bullet holes; the holes are *not* uniform.  The naive
proposal is to armor the regions where the *returning* planes show the most holes.  That
is exactly backwards: a region with few holes among survivors is one where a hit tends to
*down* the plane, so the hit planes never came back to be counted.  Wald's correction is
to armor the regions with the *fewest* holes among survivors (highest lethality).

The toy model.  Each region has a hit rate (probability a sortie takes a hit there) and a
lethality (probability that hit downs the plane).  Among *survivors*, the (unnormalized,
per-region under independence) chance a returning plane was hit in a region is

    survivor_hit_rate = hit_rate * (1 - kill_prob).

A region's lethality suppresses its survivor hole count below its true hit rate; the gap

    gap = hit_rate - survivor_hit_rate = hit_rate * kill_prob

is exactly the lethality-weighted hit mass.  With equal exposure (every region hit at the
same rate) the naive policy picks the *least* lethal region (most surviving holes) while
Wald's policy picks the region with the largest gap -- the *most* lethal region -- which
is the correct place to add armor.

CLAIM BOUNDARY: a toy illustration of the Wald survivorship correction (Statistical
Research Group, 1943); the real analysis used hit-density data, and this is NOT a
historical reconstruction.  Verified by exact arithmetic (not Monte-Carlo, not
Coq-discharged).  This is NOT a physical bound and is deliberately NOT a member of the
physical-limits web.  This is exactly why a research repo should retain negative / failed
results rather than condition on survivors.  Dependency-light (numpy only).

Reference: A. Wald, "A method of estimating plane vulnerability based on damage of
survivors" (SRG memoranda, 1943; reprinted CRC 432, 1980).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Equal exposure (every region hit at the same rate), differing lethality, so the
# naive choice lands on a low-lethality region and Wald's choice lands on "engine".
BOMBER_REGIONS = {
    "engine": (0.3, 0.8),
    "fuselage": (0.3, 0.1),
    "wings": (0.3, 0.2),
    "tail": (0.3, 0.05),
}


def survivor_hit_rate(hit_rate: float, kill_prob: float) -> float:
    """Probability a *survivor* was hit in a region = hit_rate * (1 - kill_prob)."""
    if not (0.0 <= hit_rate <= 1.0):
        raise ValueError("hit_rate must be in [0, 1]")
    if not (0.0 <= kill_prob <= 1.0):
        raise ValueError("kill_prob must be in [0, 1]")
    return float(hit_rate * (1.0 - kill_prob))


def survivor_hit_rates(regions) -> dict:
    """Map region name -> survivor_hit_rate."""
    return {name: survivor_hit_rate(hr, kp) for name, (hr, kp) in regions.items()}


def naive_armor_choice(regions) -> str:
    """Naive (wrong) policy: armor the region with the MOST observed survivor holes."""
    if not regions:
        raise ValueError("regions must be nonempty")
    rates = survivor_hit_rates(regions)
    return max(rates, key=rates.get)


def wald_armor_choice(regions) -> str:
    """Wald's (correct) policy: armor the region with the LARGEST true-vs-survivor gap.

    gap = hit_rate - survivor_hit_rate = hit_rate * kill_prob, i.e. highest lethality.
    """
    if not regions:
        raise ValueError("regions must be nonempty")
    gaps = {name: hr - survivor_hit_rate(hr, kp) for name, (hr, kp) in regions.items()}
    return max(gaps, key=gaps.get)


@dataclass
class SurvivorshipResult:
    regions: dict
    survivor_hit_rates: dict
    naive_choice: str
    wald_choice: str
    naive_is_wrong: bool

    def to_dict(self) -> dict:
        return {
            "kind": "survivorship_bias",
            "regions": self.regions,
            "survivor_hit_rates": self.survivor_hit_rates,
            "naive_choice": self.naive_choice,
            "wald_choice": self.wald_choice,
            "naive_is_wrong": self.naive_is_wrong,
            "claim_boundary": ("toy illustration of the Wald survivorship correction "
                               "(Statistical Research Group, 1943); the real analysis "
                               "used hit-density data and this is NOT a historical "
                               "reconstruction; NOT a physical bound, NOT a member of the "
                               "physical-limits web; this is exactly why a research repo "
                               "should retain negative/failed results rather than "
                               "condition on survivors"),
        }


def analyze_survivorship(regions=BOMBER_REGIONS) -> SurvivorshipResult:
    """Run the exact naive-vs-Wald armor comparison on the supplied regions."""
    naive = naive_armor_choice(regions)
    wald = wald_armor_choice(regions)
    return SurvivorshipResult(
        regions=dict(regions),
        survivor_hit_rates=survivor_hit_rates(regions),
        naive_choice=naive,
        wald_choice=wald,
        naive_is_wrong=bool(naive != wald),
    )


# Numerical self-check: on the canonical regions Wald armors the engine and the naive
# policy disagrees with it.
assert wald_armor_choice(BOMBER_REGIONS) == "engine"
assert naive_armor_choice(BOMBER_REGIONS) != wald_armor_choice(BOMBER_REGIONS)
assert np.isclose(survivor_hit_rate(0.3, 0.8), 0.3 * 0.2)
