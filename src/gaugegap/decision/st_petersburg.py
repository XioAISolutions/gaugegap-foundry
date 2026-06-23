"""The St. Petersburg paradox, reduced to its exactly-computable core.

A viral "ragebait" probability puzzle (Nicolas Bernoulli, 1713; analysed by Daniel
Bernoulli, 1738).  Flip a fair coin until the first tails; if that happens on flip
``k`` you win ``2**k`` dollars.  The naive expected value is

    EV = sum_{k>=1} (1/2^k) * 2^k = sum_{k>=1} 1 = +infinity,

so "you should pay any finite price to play" -- yet nobody would.  That tension is the
paradox.  Like the physical-limits web, the honest move is to strip the clickbait to the
statements that are *exactly computable* and bound them:

  1. **The divergence is real.**  The truncated EV after ``n`` terms is exactly ``n``
     (each term contributes exactly $1), so it grows without bound -- this is a genuine
     mathematical fact, not a trick.
  2. **Bounded utility gives a finite, exact value.**  Under logarithmic utility the
     certainty-equivalent payoff is the *geometric mean* of the payoffs,
     ``prod_k (2^k)^(1/2^k) = 2^(sum_k k/2^k) = 2^2 = $4`` exactly (Bernoulli's own
     resolution).
  3. **A finite bankroll gives a finite, exact EV.**  If the house can pay at most
     ``2^N`` (it caps the payout at round ``N``), the EV is exactly ``N + 1`` dollars.

So the paradox is precisely the gap between *unbounded naive EV* and *every realistic
regularization being finite and exactly computable*.  This is a decision-theory
illustration of the epistemics the repo enforces elsewhere (see
``docs/epistemics-and-claim-boundaries.md``): naive expected value is not a safe
decision rule for unbounded, heavy-tailed payoffs.

CLAIM BOUNDARY: a self-contained, closed-form decision-theory demonstration.  The
divergence and the resolutions are standard textbook results, verified here by exact
closed forms (not Monte-Carlo, not Coq-discharged).  This is NOT a physical bound and is
deliberately NOT a member of the physical-limits web; it is NOT financial advice or a
claim about real markets.  Dependency-light (numpy only).

References: D. Bernoulli, "Specimen Theoriae Novae de Mensura Sortis" (1738);
Menger (1934) on bounded utility.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def naive_truncated_ev(n: int) -> float:
    """Expected value of the game truncated at ``n`` rounds.

    Each round contributes exactly (1/2^k) * 2^k = $1, so the truncated EV is exactly
    ``n`` -- it diverges linearly as n -> infinity.  This is the certifiable core of the
    "infinite expected value" claim.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    return float(sum((1.0 / 2.0**k) * 2.0**k for k in range(1, n + 1)))


def log_utility_certainty_equivalent() -> float:
    """Certainty-equivalent payoff under logarithmic utility = the geometric mean.

    CE = prod_k (2^k)^(1/2^k) = 2^(sum_k k / 2^k) = 2^2 = 4 dollars (exact).
    """
    # sum_{k>=1} k / 2^k = 2 in closed form; CE = 2 ** that sum = 4 exactly.
    return float(2.0 ** _sum_k_over_2k())


def log_utility_expected_utility() -> float:
    """Expected log-utility E[ln(payoff)] = (sum_k k/2^k) * ln 2 = 2 ln 2 (exact)."""
    return float(_sum_k_over_2k() * np.log(2.0))


def bounded_bankroll_ev(max_payout_exponent: int) -> float:
    """EV when the house caps the payout at ``2^N`` (it cannot pay beyond round N).

    Rounds 1..N each contribute $1; the entire tail (game lasting > N) pays the cap
    ``2^N`` with probability ``1/2^N``, contributing exactly $1 more.  Total = N + 1
    dollars (exact, finite).
    """
    N = int(max_payout_exponent)
    if N < 0:
        raise ValueError("max_payout_exponent must be non-negative")
    rounds = sum((1.0 / 2.0**k) * 2.0**k for k in range(1, N + 1))
    tail = (1.0 / 2.0**N) * 2.0**N  # P(survive past N) * capped payout = 1
    return float(rounds + tail)


def _sum_k_over_2k(terms: int = 200) -> float:
    """sum_{k=1}^{terms} k / 2^k  (-> 2 as terms -> infinity; double precision by ~k=55)."""
    return float(sum(k / 2.0**k for k in range(1, terms + 1)))


@dataclass
class StPetersburgResult:
    naive_ev_diverges: bool             # truncated EV is unbounded (grows like n)
    truncated_ev_sample: dict           # n -> truncated EV (each equals n)
    log_utility_certainty_equivalent: float   # exactly $4
    log_utility_expected_utility: float       # exactly 2 ln 2
    bounded_bankroll_ev: dict           # N -> finite EV (each equals N+1)

    def to_dict(self) -> dict:
        return {
            "kind": "st_petersburg_paradox",
            "naive_ev_diverges": self.naive_ev_diverges,
            "truncated_ev_sample": self.truncated_ev_sample,
            "log_utility_certainty_equivalent": self.log_utility_certainty_equivalent,
            "log_utility_expected_utility": self.log_utility_expected_utility,
            "bounded_bankroll_ev": self.bounded_bankroll_ev,
            "claim_boundary": ("closed-form decision-theory demonstration: the naive EV "
                               "genuinely diverges (truncated EV = n), while bounded "
                               "utility (CE = $4) and a finite bankroll (EV = N+1) give "
                               "finite exact values; NOT a physical bound, NOT a member "
                               "of the physical-limits web, NOT financial advice"),
        }


def analyze_st_petersburg(ns=(5, 10, 20, 40),
                          bankroll_exponents=(5, 10, 20)) -> StPetersburgResult:
    """Run the three exactly-computable views of the paradox."""
    trunc = {int(n): naive_truncated_ev(n) for n in ns}
    diverges = all(abs(trunc[n] - n) < 1e-9 for n in trunc) and max(trunc) >= max(ns)
    bankroll = {int(N): bounded_bankroll_ev(N) for N in bankroll_exponents}
    return StPetersburgResult(
        naive_ev_diverges=bool(diverges),
        truncated_ev_sample=trunc,
        log_utility_certainty_equivalent=log_utility_certainty_equivalent(),
        log_utility_expected_utility=log_utility_expected_utility(),
        bounded_bankroll_ev=bankroll,
    )
