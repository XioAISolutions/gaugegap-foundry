"""Temporal double-slit (time diffraction): interference in the frequency spectrum.

The spatial double slit produces fringes in space with spacing set by 1/(slit
separation). Its temporal twin (Tirole, Vezzoli et al., Nature Physics 2023) opens
two "time slits" -- two short windows in time, separation Delta_t -- and the probe
interferes in the FREQUENCY spectrum, with fringe spacing

    Delta_omega = 2 pi / Delta_t.

This is exact time-frequency Fourier duality: the field from two slits at +-Dt/2 is
E(omega) = 2 E_slit(omega) cos(omega Dt / 2), so the intensity carries a cos^2(omega
Dt/2) fringe pattern whose period in omega is 2 pi / Dt. A single time slit of
(Gaussian) width sigma_t sets the spectral envelope, obeying the time-bandwidth
uncertainty sigma_t sigma_omega >= 1/2 -- the Fourier-dual sibling of the
Mandelstam-Tamm quantum speed limit (which is the time<->energy currency of the
physical-limits web).

This module builds the time-domain probe, computes the spectrum by FFT, recovers the
slit separation from the fringe pattern, and emits a discharged Lean 4 / Coq
certificate of the time-bandwidth bound.

CLAIM BOUNDARY: a finite, exact classical-field / Fourier simulation of the
time-diffraction PRINCIPLE. It is NOT a reproduction of the ITO thin-film experiment,
its material response, or its specific numbers; the time-bandwidth inequality is an
exact theorem of Fourier analysis. Dependency-light (numpy). Not a continuum/
Millennium claim.

References: Tirole, Vezzoli et al., Nat. Phys. 19 (2023) 999 ("Double-slit time
diffraction at optical frequencies"); Gabor (1946) (time-bandwidth limit).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

_TWO_PI = float(2.0 * np.pi)


def time_slits(times: np.ndarray, dt: float, tau: float, n_slits: int = 2
               ) -> np.ndarray:
    """Time-domain probe: ``n_slits`` Gaussian windows of width ``tau`` centred to
    span separation ``dt`` (two slits at +-dt/2)."""
    t = np.asarray(times, dtype=float)
    if n_slits == 2:
        centers = [-dt / 2.0, dt / 2.0]
    else:
        centers = list(np.linspace(-dt / 2.0, dt / 2.0, n_slits))
    field = np.zeros_like(t, dtype=complex)
    for c in centers:
        field += np.exp(-((t - c) ** 2) / (2.0 * tau ** 2))
    return field


def spectrum(times: np.ndarray, field: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Power spectrum |E(omega)|^2 vs angular frequency omega (sorted)."""
    t = np.asarray(times, dtype=float)
    n = t.size
    dt_samp = float(t[1] - t[0])
    E = np.fft.fftshift(np.fft.fft(np.asarray(field, dtype=complex)))
    omega = np.fft.fftshift(np.fft.fftfreq(n, d=dt_samp)) * _TWO_PI
    return omega, np.abs(E) ** 2


def fringe_spacing_theory(dt: float) -> float:
    """Predicted frequency fringe spacing: Delta_omega = 2 pi / Delta_t."""
    return _TWO_PI / dt


def recover_separation(omega: np.ndarray, power: np.ndarray,
                       min_separation: float = 0.0) -> float:
    """Recover the time-slit separation Delta_t from the fringe pattern.

    The spectrum carries a cos(omega Dt) modulation; Fourier-transforming the
    spectrum over omega peaks at the conjugate "time" = Dt (the temporal analog of
    reading slit separation off spatial fringes). ``min_separation`` skips the broad
    single-slit envelope lobe near the origin (set it to a few times the slit width).
    """
    omega = np.asarray(omega, dtype=float)
    power = np.asarray(power, dtype=float)
    d_omega = float(omega[1] - omega[0])
    n = omega.size
    spec_of_spec = np.abs(np.fft.rfft(power - power.mean()))
    conj_t = np.fft.rfftfreq(n, d=d_omega / _TWO_PI)   # conjugate variable to omega
    lo = int(np.searchsorted(conj_t, max(min_separation, conj_t[1])))
    lo = max(lo, 1)
    peak = lo + int(np.argmax(spec_of_spec[lo:]))
    return float(conj_t[peak])


def time_bandwidth_product(sigma_t: float, sigma_omega: float) -> float:
    """sigma_t * sigma_omega (>= 1/2 by the Fourier uncertainty bound)."""
    return float(sigma_t * sigma_omega)


def spectral_std(omega: np.ndarray, power: np.ndarray) -> float:
    """Standard deviation of the (normalized) power spectrum -- the bandwidth."""
    omega = np.asarray(omega, dtype=float)
    p = np.asarray(power, dtype=float)
    p = p / p.sum()
    mean = float(np.sum(omega * p))
    var = float(np.sum((omega - mean) ** 2 * p))
    return float(np.sqrt(max(var, 0.0)))


def temporal_std(times: np.ndarray, field: np.ndarray) -> float:
    """Standard deviation of the (normalized) intensity |E(t)|^2 in time.

    Paired with ``spectral_std``, a Gaussian slit saturates sigma_t sigma_omega = 1/2.
    """
    t = np.asarray(times, dtype=float)
    p = np.abs(np.asarray(field, dtype=complex)) ** 2
    p = p / p.sum()
    mean = float(np.sum(t * p))
    var = float(np.sum((t - mean) ** 2 * p))
    return float(np.sqrt(max(var, 0.0)))


def emit_time_bandwidth_certificate(label: str, sigma_t: float, sigma_omega: float):
    """Discharged Lean 4 / Coq proof of the time-bandwidth bound sigma_t sigma_omega
    >= 1/2.

    Trust input (Fourier uncertainty theorem), with the denominator cleared:
    sigma_omega * (2 sigma_t) >= 1; the assistant discharges sigma_t sigma_omega >=
    1/2 with nlinarith / nra.
    """
    base = "".join(ch for ch in label.title() if ch.isalnum()) or "Tb"
    ns = base if not base[0].isdigit() else "T" + base
    lean = f"""import Mathlib.Tactic

namespace TimeBandwidth.{ns}

/-- Temporal width sigma_t and spectral width sigma_omega (abstract reals). -/
axiom sigma_t : ℝ
axiom sigma_omega : ℝ

/-- TRUST INPUT -- Fourier uncertainty (Gabor), denominator cleared:
    sigma_omega * (2 * sigma_t) >= 1  (i.e. sigma_omega >= 1 / (2 sigma_t)). -/
axiom fourier_uncertainty : sigma_omega * (2 * sigma_t) ≥ 1

/-- The time-bandwidth product respects the 1/2 floor (no holes). -/
theorem time_bandwidth : sigma_t * sigma_omega ≥ 1 / 2 := by
  nlinarith [fourier_uncertainty]

end TimeBandwidth.{ns}
"""
    coq = f"""Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section TimeBandwidth_{ns}.

(* Temporal width st and spectral width sw. *)
Variable st sw : R.

(* TRUST INPUT: Fourier uncertainty (Gabor), denominator cleared:
   sw * (2 * st) >= 1  (i.e. sw >= 1 / (2 st)). *)
Hypothesis fourier_uncertainty : sw * (2 * st) >= 1.

Theorem time_bandwidth : st * sw >= 1 / 2.
Proof. nra. Qed.

End TimeBandwidth_{ns}.
"""
    return lean, coq


@dataclass
class TimeDiffractionResult:
    dt: float
    tau: float
    fringe_spacing_theory: float
    separation_recovered: float
    fringe_spacing_recovered: float
    fringe_relative_error: float
    sigma_t: float
    sigma_omega: float
    time_bandwidth_product: float
    uncertainty_respected: bool       # sigma_t sigma_omega >= 1/2
    lean4: str
    coq: str

    def to_dict(self) -> dict:
        return {
            "kind": "temporal_double_slit",
            "dt": self.dt, "tau": self.tau,
            "fringe_spacing_theory": self.fringe_spacing_theory,
            "separation_recovered": self.separation_recovered,
            "fringe_spacing_recovered": self.fringe_spacing_recovered,
            "fringe_relative_error": self.fringe_relative_error,
            "sigma_t": self.sigma_t, "sigma_omega": self.sigma_omega,
            "time_bandwidth_product": self.time_bandwidth_product,
            "uncertainty_respected": self.uncertainty_respected,
            "claim_boundary": ("finite exact Fourier simulation of the time-diffraction "
                               "principle (time<->frequency duality); NOT a reproduction "
                               "of the ITO thin-film experiment or its numbers; the "
                               "time-bandwidth bound is an exact Fourier theorem; not a "
                               "continuum/Millennium claim"),
        }


def analyze_time_diffraction(dt: float = 8.0, tau: float = 0.6,
                             t_max: float = 40.0, n: int = 8192
                             ) -> TimeDiffractionResult:
    """Build the two-time-slit probe, compute its spectrum, recover the separation
    from the fringes, and certify the time-bandwidth bound."""
    times = np.linspace(-t_max, t_max, n)
    field = time_slits(times, dt, tau)
    omega, power = spectrum(times, field)

    theory = fringe_spacing_theory(dt)
    sep = recover_separation(omega, power, min_separation=3.0 * tau)
    fringe_meas = fringe_spacing_theory(sep) if sep > 0 else float("inf")
    rel_err = abs(fringe_meas - theory) / theory

    # single time slit -> intensity std in time and frequency; both are stds of the
    # normalized intensity, so a Gaussian slit saturates sigma_t sigma_omega = 1/2
    single = time_slits(times, 0.0, tau, n_slits=1)
    omega_env, env_power = spectrum(times, single)
    sigma_omega = spectral_std(omega_env, env_power)
    sigma_t = temporal_std(times, single)
    prod = time_bandwidth_product(sigma_t, sigma_omega)
    lean, coq = emit_time_bandwidth_certificate("tb", sigma_t, sigma_omega)
    return TimeDiffractionResult(
        dt=dt, tau=tau, fringe_spacing_theory=theory,
        separation_recovered=sep, fringe_spacing_recovered=fringe_meas,
        fringe_relative_error=rel_err, sigma_t=sigma_t, sigma_omega=sigma_omega,
        time_bandwidth_product=prod,
        uncertainty_respected=bool(prod >= 0.5 - 1e-9),
        lean4=lean, coq=coq,
    )
