"""Data sonification and the sampling limit: the honest core behind "LHC sounds like
Saturn's rings".

Sonification (CERN's LHCsound, NASA's Chandra/Cassini) maps data to audio: a real,
useful technique for outreach and accessibility. But it is a *mapping*, not physics --
two unrelated datasets can be made to sound alike by the choice of mapping and the
shared audio band, so auditory similarity is NOT evidence of a shared physical source.

The rigorous, certifiable content is the **Nyquist-Shannon sampling limit** (the
time<->frequency currency of the physical-limits web): a signal sampled at rate f_s
faithfully represents only frequencies below the Nyquist frequency f_s/2; a tone above
it *folds* (aliases) to a unique in-band impostor, irreversibly. We certify the
aliasing fold: for f_s/2 < f < f_s, the alias is f_s - f, and 0 < f_s - f < f_s/2.

This module also quantifies "spurious similarity": two independent random datasets,
sonified with the same band-limited mapping, score high spectral similarity even
though their raw data are uncorrelated -- a controllable false positive that explains
the "sounds identical" claim without any shared physics.

CLAIM BOUNDARY: a finite, exact signal-processing demonstration. Sonification is a
data-to-audio mapping; auditory similarity is not physical correspondence; the LHC and
Saturn share no special link here. The sampling/aliasing statements are exact theorems
of Fourier analysis. Dependency-light (numpy). Not a continuum/Millennium claim.

References: Shannon (1949), "Communication in the Presence of Noise"; Nyquist (1928);
CERN LHCsound; NASA Chandra/Cassini sonification.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np


def nyquist_frequency(sample_rate: float) -> float:
    """The Nyquist frequency f_s / 2 -- the highest faithfully representable freq."""
    return float(sample_rate) / 2.0


def alias_frequency(f: float, sample_rate: float) -> float:
    """Apparent frequency after sampling at ``sample_rate`` (folded into [0, f_s/2])."""
    fs = float(sample_rate)
    m = round(f / fs)
    return float(abs(f - m * fs))


def nyquist_rate(f_max: float) -> float:
    """Minimum sampling rate to faithfully represent content up to ``f_max``: 2 f_max."""
    return 2.0 * float(f_max)


def sonify(data, *, sample_rate: float = 8000.0, f_min: float = 200.0,
           f_max: float = 2000.0, dur_per_point: float = 0.03) -> np.ndarray:
    """Map a data series to an audio waveform: each value -> a tone whose pitch is the
    (min-max normalized) value mapped into [f_min, f_max]. A deterministic mapping."""
    d = np.asarray(data, dtype=float)
    if d.size == 0:
        return np.zeros(0)
    lo, hi = float(d.min()), float(d.max())
    norm = (d - lo) / (hi - lo) if hi > lo else np.zeros_like(d)
    freqs = f_min + norm * (f_max - f_min)
    n_per = max(1, int(sample_rate * dur_per_point))
    t = np.arange(n_per) / sample_rate
    return np.concatenate([np.sin(2 * np.pi * fr * t) for fr in freqs])


def power_spectrum(signal, sample_rate: float) -> Tuple[np.ndarray, np.ndarray]:
    """One-sided power spectrum (freqs in Hz, power) via rFFT."""
    sig = np.asarray(signal, dtype=float)
    n = sig.size
    p = np.abs(np.fft.rfft(sig)) ** 2
    freqs = np.fft.rfftfreq(n, d=1.0 / sample_rate)
    return freqs, p


def spectral_similarity(sig_a, sig_b, sample_rate: float) -> float:
    """Cosine similarity in [0,1] of the two power spectra (a mapping-level measure)."""
    _, pa = power_spectrum(sig_a, sample_rate)
    _, pb = power_spectrum(sig_b, sample_rate)
    n = min(pa.size, pb.size)
    pa, pb = pa[:n], pb[:n]
    na, nb = np.linalg.norm(pa), np.linalg.norm(pb)
    if na < 1e-15 or nb < 1e-15:
        return 0.0
    return float(np.dot(pa, pb) / (na * nb))


def demo_datasets(seed: int = 0, n: int = 48):
    """Two INDEPENDENT random series (uncorrelated raw data) -- stand-ins for two
    unrelated sources (e.g. 'LHC' and 'Saturn')."""
    rng = np.random.default_rng(seed)
    a = np.cumsum(rng.standard_normal(n))
    b = np.cumsum(rng.standard_normal(n))
    return a, b


def emit_nyquist_certificate(label: str, sample_rate: float, f: float):
    """Discharged Lean 4 / Coq proof of the aliasing fold: for f_s/2 < f < f_s, the
    alias f_s - f lies strictly inside the band, 0 < f_s - f < f_s/2."""
    base = "".join(ch for ch in label.title() if ch.isalnum()) or "Nyq"
    ns = base if not base[0].isdigit() else "N" + base
    lean = f"""import Mathlib.Tactic

namespace Nyquist.{ns}

/-- Sampling rate fs and a tone frequency f (abstract reals). -/
axiom fs : ℝ
axiom f : ℝ

/-- TRUST INPUT 1 -- the tone is above the Nyquist frequency: f > fs/2. -/
axiom over_nyquist : f > fs / 2
/-- TRUST INPUT 2 -- but below the sampling rate: f < fs. -/
axiom below_rate : f < fs

/-- The alias folds strictly into the band: 0 < fs - f < fs/2 (no holes). -/
theorem aliasing_fold : 0 < fs - f ∧ fs - f < fs / 2 := by
  constructor
  · linarith [below_rate]
  · linarith [over_nyquist]

end Nyquist.{ns}
"""
    coq = f"""Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section Nyquist_{ns}.

Variable fs f : R.

(* TRUST INPUT 1: tone above the Nyquist frequency. *)
Hypothesis over_nyquist : f > fs / 2.
(* TRUST INPUT 2: but below the sampling rate. *)
Hypothesis below_rate : f < fs.

Theorem aliasing_fold : 0 < fs - f /\\ fs - f < fs / 2.
Proof. split; lra. Qed.

End Nyquist_{ns}.
"""
    return lean, coq


@dataclass
class SonificationResult:
    sample_rate: float
    nyquist: float
    f_max_used: float
    within_band: bool                 # f_max_used <= nyquist (no aliasing)
    alias_example_freq: float         # an over-Nyquist tone...
    alias_example_alias: float        # ...and the impostor it folds to
    self_similarity: float            # a signal vs itself (control, = 1)
    unrelated_similarity: float       # two INDEPENDENT datasets' sonifications
    similarity_is_spurious: bool      # unrelated similarity is non-negligible
    lean4: str
    coq: str

    def to_dict(self) -> dict:
        return {
            "kind": "sonification_sampling_limit",
            "sample_rate": self.sample_rate, "nyquist": self.nyquist,
            "f_max_used": self.f_max_used, "within_band": self.within_band,
            "alias_example_freq": self.alias_example_freq,
            "alias_example_alias": self.alias_example_alias,
            "self_similarity": self.self_similarity,
            "unrelated_similarity": self.unrelated_similarity,
            "similarity_is_spurious": self.similarity_is_spurious,
            "claim_boundary": ("finite exact signal-processing demo; sonification is a "
                               "data-to-audio mapping and auditory similarity is not "
                               "physical correspondence (independent datasets already "
                               "score high spectral similarity; no LHC<->Saturn link); "
                               "the sampling/aliasing statements are exact Fourier "
                               "theorems; not a continuum/Millennium claim"),
        }


def analyze_sonification(data_a=None, data_b=None, *, sample_rate: float = 8000.0,
                         f_min: float = 200.0, f_max: float = 2000.0,
                         seed: int = 0) -> SonificationResult:
    """Sonify two INDEPENDENT datasets and show their spectra are already non-trivially
    similar (so "they sound alike" is not evidence of a shared source), and certify the
    Nyquist aliasing fold."""
    if data_a is None or data_b is None:
        data_a, data_b = demo_datasets(seed=seed)
    nyq = nyquist_frequency(sample_rate)

    son_a = sonify(data_a, sample_rate=sample_rate, f_min=f_min, f_max=f_max)
    son_b = sonify(data_b, sample_rate=sample_rate, f_min=f_min, f_max=f_max)
    self_sim = spectral_similarity(son_a, son_a, sample_rate)          # control = 1
    unrelated_sim = spectral_similarity(son_a, son_b, sample_rate)     # spurious

    # an over-Nyquist tone aliases to an in-band impostor
    over = nyq + 0.3 * nyq
    alias = alias_frequency(over, sample_rate)

    lean, coq = emit_nyquist_certificate("alias", sample_rate, over)
    return SonificationResult(
        sample_rate=float(sample_rate), nyquist=float(nyq), f_max_used=float(f_max),
        within_band=bool(f_max <= nyq),
        alias_example_freq=float(over), alias_example_alias=float(alias),
        self_similarity=float(self_sim), unrelated_similarity=float(unrelated_sim),
        similarity_is_spurious=bool(unrelated_sim > 0.1),
        lean4=lean, coq=coq,
    )
