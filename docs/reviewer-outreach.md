# Outreach note: request for independent review

*A template letter to accompany the reviewer packet (`make reviewer-packet`)
when contacting a domain expert. Fill in the bracketed fields. Keep the framing
exactly as honest as below — the value of this request depends on it.*

---

**Subject:** Request for independent review — certified finite-system numerical bounds (no proof claims)

Dear Dr. [NAME],

I'm reaching out to ask whether you would be willing to review a small,
self-contained computational artifact, or point me to someone better placed to.

**What it is.** GaugeGap Foundry is a *verification-first* software platform for
finite-system numerical benchmarks. Every headline number is one of: a
machine-checked **certified bound** computed in directed-rounding interval
arithmetic; an **exactly-solvable** finite system pinned to a known closed-form
answer; or a reproducible measurement with a separated error budget. The whole
repository is fenced by an automatically-audited *claim boundary*.

**What it is NOT.** It does **not** claim to resolve the Yang–Mills mass-gap
problem, the Riemann Hypothesis, or any Millennium Prize problem; it asserts no
continuum or first-principles result. I want to be unambiguous about that up
front, because the area attracts overclaims and I am specifically trying not to
add to them.

**What I'd value your eyes on** (any subset):

1. **Certified spectral screening** of Hilbert–Pólya candidate operators
   (Berry–Keating `xp`, etc.): finite-truncation separation bounds from the
   low-lying Riemann zeros, computed as certified interval enclosures and
   independently cross-checked against a second arbitrary-precision library
   (Arb). The question is whether the *verification obligations* I list (trust
   chain, directed rounding, enclosure disjointness) are complete and correctly
   discharged.

2. **Certified variational bounds for the quartic anharmonic oscillator**
   (`H = ½p² + ½x² + λx⁴`): rigorous Rayleigh–Ritz *upper bounds* on the true
   (infinite-dimensional) energy levels. This is the cleanest example of a
   genuinely rigorous, one-sided, infinite-dimensional statement in the repo —
   I'd value a check that the variational logic and the interval implementation
   are sound.

3. **The claim-boundary discipline itself:** is the boundary drawn in the right
   place, and is the language throughout appropriately scoped?

**How to verify without trusting me.** Everything reproduces from a fresh clone:

```bash
pip install -e ".[dev]"
pytest -q                       # full known-answer + certified suite
python scripts/verify_proofpack.py   # deterministic-result digest
python scripts/run_anharmonic.py     # the certified variational bounds
```

The attached reviewer packet (`INDEX.md` first) collects the trust chains, the
audit status, provenance, and a reviewer checklist.

**What would help most:** a candid assessment of whether the certified claims are
sound and whether anything is overclaimed or under-justified — including "this is
correct but not novel/useful," which is itself useful to know. I'm not seeking
endorsement; I'm seeking error-finding.

Thank you for considering it.

[YOUR NAME]
[AFFILIATION / CONTACT]

---

### Suggested recipients (by topic)

- Rigorous/verified numerics & interval arithmetic (the methodology).
- Spectral theory / Hilbert–Pólya program (the CurveRank screening scope).
- Lattice gauge theory (the finite Z₂/U(1)/SU(3) benchmarks and their boundary).

Reproducibility note: the packet's audit reports and provenance are generated at
build time; regenerate with `make reviewer-packet`.
