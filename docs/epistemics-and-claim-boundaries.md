# Epistemics & claim boundaries: where this repo draws the line

This project is **verification-first**. Every headline result is paired with a
machine-checkable certificate (a discharged Lean 4 / Coq inequality, an interval
enclosure, or an SMT cross-check) and an explicit *claim boundary* stating what is and
is **not** being asserted. Two pieces of tooling enforce this:

- `scripts/research_maturity_audit.py` — flags maturity/placeholder language and fails
  on unbounded high-severity findings.
- `scripts/claim_boundary_audit.py` — checks that headline claims carry an explicit
  boundary.

This note explains the *epistemic stance* behind that tooling, using a well-known
foresight diagram as the map.

## The futures cone

Voros's **futures cone** (extending Hancock & Bezold) sorts statements about what could
happen into nested bands, widening as they get less disciplined:

| Band | Gloss | In this repo |
|---|---|---|
| **Projected** | the single "business-as-usual" extrapolation | the certified value itself |
| **Probable** | "likely to happen" — current trends | bracketed/enclosed results with error bars |
| **Plausible** | "could happen" — consistent with current knowledge | conjectures we *state but do not certify* |
| **Possible** | "might happen" — requires new knowledge | explicitly flagged as out of scope |
| **Preposterous** | "impossible / will never happen" | **rejected** — fails the claim-boundary audit |
| **Preferable** | "should happen" — value judgement | roadmap / work orders (kept separate from claims) |

The discipline is simply: **never let a result drift outward from the band its evidence
supports.** A machine-checked inequality is *projected/probable*. A finite-system
demonstration of an established bound is *plausible-made-concrete* — and we say so in
its claim boundary ("finite-system / semiclassical demonstration … not a continuum or
Millennium claim"). Anything we cannot bound, enclose, or discharge stays a labelled
conjecture; it does not get to wear the certificate.

```
        Now ───────────────► time
              · projected   (the certified number)
            ·· probable     (bracketed, error-bounded)
          ···· plausible    (stated conjecture, uncertified)
        ······ possible     (flagged out of scope)
      ········ PREPOSTEROUS  (rejected by the audit)
```

## A worked example of the outer band

Speculative "theory-of-everything" infographics are a useful negative control. Take a
representative one: a *"consciousness emerges in the fold"* poster proposing a
**"consciousness coefficient" `C = S × R × τ`** (state-complexity × a "recursion
factor" × a "torsion" term), with qualia identified as the geometric torsion of a
self-referential spiral.

It is visually compelling and uses real vocabulary (torsion, recursion, strange loops),
but measured against this repo's bar it sits squarely in the **preposterous** band:

- **No falsifiable inequality.** `C = S × R × τ` defines a product of undefined
  quantities; there is no statement that could be machine-checked, bracketed, or
  refuted.
- **No certificate, and none possible.** There is nothing for Lean/Coq/z3 to discharge
  and no interval to enclose — the opposite of every member of the
  [physical-limits web](physical-limits.md), each of which reduces to a single
  checkable inequality.
- **It would fail the audits on contact.** Unbounded universal claims with no claim
  boundary are exactly what `claim_boundary_audit.py` and
  `research_maturity_audit.py` are built to stop.

This is **not** a statement about consciousness research; it is a statement about
*evidence discipline*. The same reduction we apply to "mind-blowing physics" reels —
strip the claim down to the one thing that can be exactly computed and certified — finds
nothing certifiable here, so the honest output is "out of scope," not a fabricated
coefficient. That refusal is the system working as designed.

## The rule, in one line

> If it can be bracketed, enclosed, or discharged, certify it and state its boundary.
> If it cannot, label it a conjecture and leave it in the band its evidence earns —
> never in the certified core.
