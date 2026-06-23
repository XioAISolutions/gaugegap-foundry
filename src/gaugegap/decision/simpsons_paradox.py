"""Simpson's paradox, reduced to its exactly-computable core.

A subgroup-vs-aggregate trend reversal: a treatment can win *every* subgroup yet
lose on the pooled (aggregate) data.  The canonical illustration is the kidney-stone
study (Charig et al., 1986), reproduced here as illustrative data:

  * Treatment A: small stones 81/87, large stones 192/263 (aggregate 273/350).
  * Treatment B: small stones 234/270, large stones 55/80 (aggregate 289/350).

Treatment A wins *both* subgroups (81/87 ~= .931 > 234/270 ~= .867 on small stones;
192/263 ~= .730 > 55/80 ~= .688 on large stones), yet B wins the *aggregate*
(289/350 ~= .826 > 273/350 ~= .780).  The reversal is pure arithmetic of weighted
averages: A's patients are concentrated in the harder subgroup (large stones), so its
favourable per-group rates are diluted in the pool, while B's patients are concentrated
in the easier subgroup (small stones), inflating its pooled rate.  The group-size
imbalance is the confounder.

The honest resolution is to *condition on the confounder* (here, stone size) rather
than trust the pooled rate: per-subgroup, A dominates.  This is a decision-theory
illustration of the epistemics the repo enforces elsewhere -- an aggregate statistic
is not a safe decision rule when the groups are imbalanced on a lurking variable.

CLAIM BOUNDARY: exact arithmetic of weighted averages under a confounding group-size
imbalance; the resolution is to condition on the confounder (here, stone size).  The
numbers are illustrative data, verified by exact rational/float arithmetic (not
Monte-Carlo, not Coq-discharged).  This is NOT a physical bound and is deliberately
NOT a member of the physical-limits web; it is NOT medical advice.  Dependency-light
(numpy only).

Reference: C. R. Charig et al., "Comparison of treatment of renal calculi...",
Br. Med. J. 292 (1986) 879.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# Illustrative kidney-stone data as subgroup (success, total) pairs, ordered
# (small stones, large stones).
KIDNEY_STONE_A = [(81, 87), (192, 263)]
KIDNEY_STONE_B = [(234, 270), (55, 80)]


def rate(success: int, total: int) -> float:
    """Success rate ``success / total`` (exact division)."""
    if total <= 0:
        raise ValueError("total must be positive")
    if not (0 <= success <= total):
        raise ValueError("success must satisfy 0 <= success <= total")
    return float(success) / float(total)


def aggregate_rate(pairs) -> float:
    """Pooled success rate: sum of successes over sum of totals (exact)."""
    successes = sum(s for s, _ in pairs)
    totals = sum(t for _, t in pairs)
    if totals <= 0:
        raise ValueError("aggregate total must be positive")
    return float(successes) / float(totals)


def subgroup_rates(pairs) -> list:
    """Per-subgroup success rates, in the order given."""
    return [rate(s, t) for s, t in pairs]


def is_simpsons_reversal(a_pairs, b_pairs) -> bool:
    """True iff one treatment wins *every* subgroup while the other wins the aggregate.

    Requires aligned subgroups (same count, same order).  The reversal is the exact
    statement that the subgroup-dominant treatment is the aggregate-loser.
    """
    a_sub = subgroup_rates(a_pairs)
    b_sub = subgroup_rates(b_pairs)
    if len(a_sub) != len(b_sub) or not a_sub:
        raise ValueError("treatments must have the same nonempty subgroup structure")

    a_wins_all = all(ra > rb for ra, rb in zip(a_sub, b_sub))
    b_wins_all = all(rb > ra for ra, rb in zip(a_sub, b_sub))
    a_agg = aggregate_rate(a_pairs)
    b_agg = aggregate_rate(b_pairs)

    # Reversal: subgroup winner is the aggregate loser, for whichever direction holds.
    if a_wins_all and b_agg > a_agg:
        return True
    if b_wins_all and a_agg > b_agg:
        return True
    return False


@dataclass
class SimpsonsResult:
    a_aggregate: float
    b_aggregate: float
    a_subgroup_rates: list
    b_subgroup_rates: list
    aggregate_winner: str               # "A" or "B"
    subgroup_winner: str                # "A" or "B" (wins every subgroup), or "none"
    reversal: bool

    def to_dict(self) -> dict:
        return {
            "kind": "simpsons_paradox",
            "a_aggregate": self.a_aggregate,
            "b_aggregate": self.b_aggregate,
            "a_subgroup_rates": self.a_subgroup_rates,
            "b_subgroup_rates": self.b_subgroup_rates,
            "aggregate_winner": self.aggregate_winner,
            "subgroup_winner": self.subgroup_winner,
            "reversal": self.reversal,
            "claim_boundary": ("exact arithmetic of weighted averages under a "
                               "confounding group-size imbalance; the resolution is to "
                               "condition on the confounder (here, stone size); "
                               "illustrative data, NOT a physical bound, NOT a member of "
                               "the physical-limits web, NOT medical advice"),
        }


def analyze_simpsons(a_pairs=KIDNEY_STONE_A, b_pairs=KIDNEY_STONE_B) -> SimpsonsResult:
    """Run the exact subgroup-vs-aggregate comparison on the supplied data."""
    a_sub = subgroup_rates(a_pairs)
    b_sub = subgroup_rates(b_pairs)
    a_agg = aggregate_rate(a_pairs)
    b_agg = aggregate_rate(b_pairs)

    aggregate_winner = "A" if a_agg > b_agg else "B"
    if all(ra > rb for ra, rb in zip(a_sub, b_sub)):
        subgroup_winner = "A"
    elif all(rb > ra for ra, rb in zip(a_sub, b_sub)):
        subgroup_winner = "B"
    else:
        subgroup_winner = "none"

    return SimpsonsResult(
        a_aggregate=a_agg,
        b_aggregate=b_agg,
        a_subgroup_rates=a_sub,
        b_subgroup_rates=b_sub,
        aggregate_winner=aggregate_winner,
        subgroup_winner=subgroup_winner,
        reversal=bool(is_simpsons_reversal(a_pairs, b_pairs)),
    )


# Numerical self-check: the canonical data is an exact reversal.
assert bool(is_simpsons_reversal(KIDNEY_STONE_A, KIDNEY_STONE_B)) is True
assert np.isclose(aggregate_rate(KIDNEY_STONE_A), 273.0 / 350.0)
assert np.isclose(aggregate_rate(KIDNEY_STONE_B), 289.0 / 350.0)
