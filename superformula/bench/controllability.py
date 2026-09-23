"""Read superformula parameters back out of silhouettes — the benchmark's ruler.

The superformula track conditions a generator on a shape whose parameters are
known exactly at every frame. That makes an objective controllability test
possible: generate, recover the parameters from the output, compare with what
was commanded. No human rating, no model judge.

A ruler has to be checked before it measures anything. This module recovers two
quantities from binary silhouettes, and `calibrate.py` measures how well it
does that on *clean renders*, where the true answer is known and nothing has
been through a generator. Only after that is it meaningful to point it at depth
estimated from generated video (see PROTOCOL.md — not yet run).

Recovered quantities
--------------------
* **symmetry order m** — the lobe count, from the angular radius profile of the
  silhouette about its centroid. With n2 == n3 the superformula has period
  2*pi/m, so an m-lobed outline puts its energy into harmonics m, 2m, 3m, ...
* **rotation per frame** — from the phase of harmonic m across frames. At pitch
  0 yaw is an exact image-plane rotation; at other pitches it is approximate,
  and calibrate.py reports how approximate.

Limits, stated before any result: m is searched in [3, MAX_ORDER]; m = 1 and 2
are indistinguishable from an off-centre or foreshortened ellipse. Rotation is
only recoverable below pi/m per frame — faster than that, lobes alias onto their
neighbours and the sign of the motion is lost.
"""

from __future__ import annotations

import numpy as np

MAX_ORDER = 24
BINS = 720
HARMONICS = 4

#: Fraction of the outline's non-DC energy (harmonics 3..MAX_ORDER) that the
#: chosen harmonic family must explain before the ruler commits to an answer.
#: Below it, `symmetry_order` abstains rather than guessing. Chosen on the
#: calibration split in calibrate.py and frozen there; see its output.
DEFAULT_MIN_CONFIDENCE = 0.5

#: A fundamental is accepted only if its own power is at least this fraction of
#: the strongest harmonic, which stops a 6-lobed outline being read as 3.
FUNDAMENTAL_RATIO = 0.25


def angular_profile(mask: np.ndarray, bins: int = BINS, whiten: bool = True) -> np.ndarray | None:
    """Outer radius of the silhouette per angle bin, about its centroid.

    With `whiten`, pixel coordinates are first mapped through the inverse square
    root of their covariance. Any outline with 3-fold or higher rotational
    symmetry has isotropic second moments, so this undoes every *linear*
    stretch of the view exactly — pitch foreshortening, per-axis normalisation,
    a square map resized to a portrait latent — while leaving a rotation a
    rotation: a fixed view distortion A gives covariance proportional to A A^T
    in every frame, and (A A^T)^(-1/2) A is orthogonal, so frame-to-frame phase
    steps survive. It cannot undo the non-linear part of a steep view, where the
    solid's sides enter the outline; calibrate.py measures where that starts.

    Returns None for an empty mask. Empty bins are filled by circular linear
    interpolation so a thin gap does not register as a lobe.
    """
    ys, xs = np.nonzero(mask)
    if ys.size == 0:
        return None
    dy, dx = ys - ys.mean(), xs - xs.mean()
    if whiten and ys.size >= 3:
        cov = np.cov(np.stack([dx, dy]))
        vals, vecs = np.linalg.eigh(cov)
        if vals.min() > 1e-12:
            w = vecs @ np.diag(vals ** -0.5) @ vecs.T * np.sqrt(vals.mean())
            dx, dy = w @ np.stack([dx, dy])
    angle = np.arctan2(dy, dx)
    radius = np.hypot(dy, dx)
    idx = np.minimum(((angle + np.pi) / (2 * np.pi) * bins).astype(np.int64), bins - 1)
    profile = np.full(bins, -1.0)
    np.maximum.at(profile, idx, radius)
    have = profile >= 0
    if not have.any():
        return None
    if not have.all():
        pos = np.arange(bins)
        known = pos[have]
        profile = np.interp(pos, np.concatenate([known - bins, known, known + bins]),
                            np.tile(profile[have], 3))
    return profile


def _spectrum(profile: np.ndarray) -> np.ndarray:
    centred = profile - profile.mean()
    return np.abs(np.fft.rfft(centred)) ** 2


def symmetry_order(mask: np.ndarray, min_confidence: float = DEFAULT_MIN_CONFIDENCE,
                   max_order: int = MAX_ORDER) -> dict:
    """Estimate the lobe count m of a silhouette, or abstain.

    Returns {"m": int | None, "confidence": float, "reason": str}. `m` is None
    when the ruler abstains — an abstention is a result, not a failure, and the
    calibration reports how often it happens.
    """
    profile = angular_profile(mask)
    if profile is None:
        return {"m": None, "confidence": 0.0, "reason": "empty silhouette"}
    if profile.std() < 1e-3 * max(profile.mean(), 1e-9):
        return {"m": None, "confidence": 0.0, "reason": "no angular structure (round outline)"}

    power = _spectrum(profile)
    band = np.arange(3, min(max_order, power.size - 1) + 1)
    band_energy = power[3:].sum()
    if band_energy <= 0:
        return {"m": None, "confidence": 0.0, "reason": "no energy above harmonic 2"}

    strongest = power[band].max()
    candidates = [k for k in band if power[k] >= FUNDAMENTAL_RATIO * strongest]
    m = int(candidates[0])
    family = sum(power[h * m] for h in range(1, HARMONICS + 1) if h * m < power.size)
    confidence = float(family / band_energy)
    if confidence < min_confidence:
        return {"m": None, "confidence": confidence,
                "reason": f"harmonic family of {m} explains only {confidence:.2f} of the outline"}
    return {"m": m, "confidence": confidence, "reason": "ok"}


def rotation_per_frame(masks, m: int) -> dict:
    """Mean image-plane rotation per frame (degrees) from the phase of harmonic m.

    Positive is counter-clockwise in image (x right, y down the array rows),
    which matches positive yaw in the renderer. Returns {"deg_per_frame",
    "residual_deg", "aliasing_limit_deg"}: `residual_deg` is the RMS departure
    of the per-frame steps from their mean, so a steady rotation scores near 0
    and a jittering one does not.
    """
    phases = []
    for mask in masks:
        profile = angular_profile(mask)
        if profile is None:
            raise ValueError("empty silhouette in sequence")
        phases.append(np.angle(np.fft.rfft(profile - profile.mean())[m]))
    steps = np.diff(np.unwrap(np.array(phases)))
    # A rotation by +a shifts the profile by +a, which moves harmonic m's phase
    # by -m*a.
    deg = -np.degrees(steps) / m
    return {
        "deg_per_frame": float(deg.mean()) if deg.size else 0.0,
        "residual_deg": float(np.sqrt(np.mean((deg - deg.mean()) ** 2))) if deg.size else 0.0,
        "aliasing_limit_deg": 180.0 / m,
    }
