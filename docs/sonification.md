# Sonification & the sampling limit

The honest core behind the viral *"LHC data sounds almost identical to Saturn's
rings"* reel — extending the **time ↔ frequency** currency of the
[physical-limits web](physical-limits-web.md).

Sonification (CERN's LHCsound, NASA's Chandra/Cassini) maps data to audio. It is a
genuinely useful technique — for outreach and for accessibility (blind scientists
"hearing" data) — but it is a **mapping**, not physics. Two unrelated datasets can be
made to sound alike by the choice of mapping and the shared audio band, so **auditory
similarity is not evidence of a shared physical source**.

## Two honest results

**1. Spurious similarity.** Two *independent* random datasets, sonified with the same
band-limited mapping, score a high spectral cosine similarity (≈ 0.33 in the demo,
versus the self-similarity control of 1.0). Cosine similarity of nonnegative spectra
confined to a shared band is biased high by construction — so a "match" between two
sonifications proves nothing about their sources.

**2. The Nyquist–Shannon sampling limit** (the certifiable content). A signal sampled
at rate `f_s` faithfully represents only frequencies below the Nyquist frequency
`f_s/2`. A tone above it *folds* (aliases) to a unique in-band impostor — e.g. a
5200 Hz tone sampled at 8000 Hz appears as 2800 Hz, irreversibly. We certify the
aliasing fold with a discharged Lean 4 / Coq proof:

```
f_s/2 < f < f_s   ⟹   0 < f_s − f < f_s/2.
```

This schema is also added to the [SMT verifier](certificate-verification.md) (z3
proves it valid over the reals).

`gaugegap.quantum.sonification`:
- `sonify`, `power_spectrum`, `spectral_similarity` — the mapping and its analysis.
- `nyquist_frequency`, `nyquist_rate`, `alias_frequency` — the sampling limit.
- `analyze_sonification(...)` — quantifies the spurious similarity and emits the
  aliasing-fold certificate.

```bash
make sonification
python scripts/run_sonification.py --sample-rate 8000 --f-max 2000
```

## Claim boundary

A finite, exact signal-processing demonstration. Sonification is a data-to-audio
mapping; auditory similarity is not physical correspondence; there is **no** special
LHC ↔ Saturn link, and nothing here supports the reel's conspiracy framing. The
sampling/aliasing statements are exact theorems of Fourier analysis. The LHC magnet
fact (≈ 8.3 T dipoles, ~100,000× Earth's field) is real but mundane. Dependency-light
(numpy). Not a continuum/Millennium claim.

References: Shannon (1949); Nyquist (1928); CERN LHCsound; NASA Chandra/Cassini
sonification.
