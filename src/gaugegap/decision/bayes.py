"""Exact Bayesian updating and the base-rate fallacy, reduced to closed forms.

Bayes' theorem for a binary hypothesis ``H`` tested by an imperfect binary test.  Let
``prior = P(H)`` be the base rate, ``sensitivity = P(+|H)`` the true-positive rate, and
``specificity = P(-|not H)`` the true-negative rate.  After a *positive* test,

    P(H | +) = P(+|H) P(H) / P(+)
             = (prior * sensitivity)
               / (prior * sensitivity + (1 - prior) * (1 - specificity)),

i.e. ``tp / (tp + fp)`` with ``tp = prior*sensitivity`` and
``fp = (1 - prior)*(1 - specificity)``.  After a *negative* test,

    P(H | -) = prior*(1 - sensitivity)
               / (prior*(1 - sensitivity) + (1 - prior)*specificity).

The **base-rate fallacy** is the well-documented intuition that a positive result from a
99%-accurate test means a ~99% chance of having the (rare) condition.  When the base rate
is tiny, that intuition is wildly wrong: with ``prior = 0.001``, ``sensitivity = 0.99``,
``specificity = 0.95`` the true posterior is only ``0.001*0.99 / (0.001*0.99 +
0.999*0.05) = 0.00099/0.05094 ~= 0.0194`` -- about 1.94%, not 99%.  The gap between the
naive intuition (which simply equals ``sensitivity``) and the correct posterior is the
fallacy made explicit.

``sequential_update`` shows evidence accumulation: feeding each step's posterior in as the
next step's prior, repeated independent positive tests drive the posterior monotonically
upward toward (but never reaching) 1.

CLAIM BOUNDARY: this is exact Bayesian arithmetic -- closed-form, verified by exact
computation (not Monte-Carlo, not Coq-discharged).  The output is only as good as the
input rates: garbage-in / garbage-out, since real-world ``prior``/``sensitivity``/
``specificity`` are themselves estimates.  This formalizes the base-rate lesson and is
deliberately NOT a physical bound and NOT a member of the physical-limits web; it is NOT
medical or diagnostic advice.  Note that the repo already uses Bayesian inference inside
iterative quantum phase estimation (``gaugegap.quantum.advanced_qpe``); this module makes
the base-rate discipline behind such updating explicit.  Dependency-light (numpy only).

References: Kahneman & Tversky (1973) on base-rate neglect; standard Bayes' theorem.
"""
from __future__ import annotations

from dataclasses import dataclass


def bayes_posterior(prior: float, sensitivity: float, specificity: float) -> float:
    """P(H | positive test) for base rate ``prior`` and an imperfect binary test.

    tp = prior * sensitivity                  (true positives)
    fp = (1 - prior) * (1 - specificity)      (false positives)
    return tp / (tp + fp)                     (exact posterior given a positive result)
    """
    _check_rate("prior", prior)
    _check_rate("sensitivity", sensitivity)
    _check_rate("specificity", specificity)
    tp = prior * sensitivity
    fp = (1.0 - prior) * (1.0 - specificity)
    denom = tp + fp
    if denom == 0.0:
        raise ValueError("positive test has zero probability under these rates")
    return float(tp / denom)


def bayes_posterior_negative(prior: float, sensitivity: float,
                             specificity: float) -> float:
    """P(H | negative test) = prior*(1-sensitivity) / [prior*(1-sensitivity)
    + (1-prior)*specificity]  (exact posterior given a negative result)."""
    _check_rate("prior", prior)
    _check_rate("sensitivity", sensitivity)
    _check_rate("specificity", specificity)
    fn = prior * (1.0 - sensitivity)               # false negatives
    tn = (1.0 - prior) * specificity               # true negatives
    denom = fn + tn
    if denom == 0.0:
        raise ValueError("negative test has zero probability under these rates")
    return float(fn / denom)


def sequential_update(prior: float, updates) -> float:
    """Apply a list of ``(sensitivity, specificity)`` positive-test updates in sequence.

    Each step's posterior becomes the next step's prior, demonstrating evidence
    accumulation across repeated independent positive results.  Returns the final
    posterior.
    """
    posterior = prior
    for sensitivity, specificity in updates:
        posterior = bayes_posterior(posterior, sensitivity, specificity)
    return float(posterior)


def base_rate_fallacy_gap(prior: float, sensitivity: float,
                          specificity: float):
    """Return ``(naive, correct)``.

    The naive intuition typically equals ``sensitivity`` (people ignore the base rate);
    the correct value is ``bayes_posterior(...)``.  Returning both makes the gap explicit.
    """
    naive = float(sensitivity)
    correct = bayes_posterior(prior, sensitivity, specificity)
    return naive, correct


def _check_rate(name: str, value: float) -> None:
    """Probabilities/rates must lie in [0, 1]."""
    if not (0.0 <= value <= 1.0):
        raise ValueError(f"{name} must be in [0, 1], got {value!r}")


@dataclass
class BayesResult:
    prior: float
    sensitivity: float
    specificity: float
    posterior_positive: float        # P(H | +), the famously small correct value
    posterior_negative: float        # P(H | -)
    naive_intuition: float           # = sensitivity (the fallacy: ignore the base rate)
    base_rate_fallacy_gap: float     # sensitivity - posterior_positive

    def to_dict(self) -> dict:
        return {
            "kind": "bayes_base_rate_fallacy",
            "prior": self.prior,
            "sensitivity": self.sensitivity,
            "specificity": self.specificity,
            "posterior_positive": self.posterior_positive,
            "posterior_negative": self.posterior_negative,
            "naive_intuition": self.naive_intuition,
            "base_rate_fallacy_gap": self.base_rate_fallacy_gap,
            "claim_boundary": ("exact Bayesian arithmetic (closed form): a positive result "
                               "from an accurate test of a rare condition gives a small "
                               "posterior, not ~sensitivity; output is only as good as the "
                               "input rates (garbage-in/garbage-out); formalizes the "
                               "base-rate lesson; NOT a physical bound, NOT a member of the "
                               "physical-limits web, NOT medical/diagnostic advice"),
        }


def analyze_bayes(prior: float = 0.001, sensitivity: float = 0.99,
                  specificity: float = 0.95) -> BayesResult:
    """Run the base-rate fallacy demonstration.

    With the defaults, ``posterior_positive ~= 0.0194`` (about 1.94%) despite a 99%
    sensitivity -- the famously counter-intuitive result.
    """
    post_pos = bayes_posterior(prior, sensitivity, specificity)
    post_neg = bayes_posterior_negative(prior, sensitivity, specificity)
    return BayesResult(
        prior=float(prior),
        sensitivity=float(sensitivity),
        specificity=float(specificity),
        posterior_positive=post_pos,
        posterior_negative=post_neg,
        naive_intuition=float(sensitivity),
        base_rate_fallacy_gap=float(sensitivity - post_pos),
    )
