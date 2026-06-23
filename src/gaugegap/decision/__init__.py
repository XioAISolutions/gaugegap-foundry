"""Decision-theory & statistical-inference vignettes: viral "mind-bender" puzzles and
classic inference traps, each reduced to an exact, bounded, certifiable core.

This is the companion to the physical-limits web. Where that web reduces viral *physics*
reels to certified inequalities, these modules do the same for *decision theory and
statistics* — the "web of inference traps." They split into two families:

  * **Heavy-tail / mean traps** — when the average is the wrong summary:
    ``st_petersburg`` (divergent EV vs. finite bounded value), ``power_law``
    (scale-free tails, divergent moments).
  * **Selection / conditioning traps** — when conditioning on the wrong thing flips the
    conclusion: ``survivorship_bias`` (Wald's bombers), ``berksons_paradox``
    (collider-induced correlation), ``simpsons_paradox`` (trend reversal),
    ``regression_to_mean`` (imperfect correlation), with ``bayes`` as the correct
    updating framework.

These are deliberately NOT members of the physical-limits web (they are not physical
bounds). Each carries an explicit claim boundary. See
``docs/inference-traps.md`` and ``docs/epistemics-and-claim-boundaries.md``.
"""
