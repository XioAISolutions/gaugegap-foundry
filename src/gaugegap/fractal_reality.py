"""Finite Mandelbrot/Julia experiments and a transparent BrainSNN-style bridge.

The module deliberately separates three layers:

* demonstrated mathematics computed from finite orbits;
* structural analogies represented by explicit feature vectors;
* philosophical interpretations that are never promoted to evidence.

It is an educational finite experiment. It does not establish that the
Mandelbrot set is a literal physical code of reality or that a spiking surrogate
is a biological brain model.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import math
from typing import Iterable, Mapping, Sequence

import numpy as np

SCHEMA = "gaugegap.fractal_reality.v1"
CLAIM_BOUNDARY = (
    "Finite orbit, image, sonification, feature-comparison, and deterministic "
    "spiking-surrogate experiment. Visual resemblance is not proof of a shared "
    "physical mechanism; the Mandelbrot set is not claimed to be a literal code "
    "of reality; the BrainSNN view is an inspectable encoding, not a biological model."
)


@dataclass(frozen=True)
class OrbitReport:
    c_real: float
    c_imag: float
    max_iterations: int
    escape_radius: float
    escaped: bool
    escape_iteration: int
    orbit: tuple[tuple[float, float], ...]
    features: Mapping[str, float]

    def summary(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class ComparisonReport:
    target: str
    evidence_layer: str
    measured_similarity: float
    user_prediction: float
    gauge_gap: float
    strongest_match: str
    weakest_match: str
    shared_mechanism: str
    boundary: str

    def summary(self) -> dict[str, object]:
        return asdict(self)


def mandelbrot_orbit(
    c: complex,
    *,
    max_iterations: int = 256,
    escape_radius: float = 2.0,
) -> tuple[list[complex], bool, int]:
    """Return the finite orbit z[n+1] = z[n]^2 + c from z[0] = 0."""
    if max_iterations < 1:
        raise ValueError("max_iterations must be positive")
    if escape_radius <= 1.0:
        raise ValueError("escape_radius must be greater than 1")

    z = 0j
    orbit: list[complex] = [z]
    for index in range(1, max_iterations + 1):
        z = z * z + c
        orbit.append(z)
        if abs(z) > escape_radius:
            return orbit, True, index
    return orbit, False, max_iterations


def julia_escape_grid(
    c: complex,
    *,
    width: int = 160,
    height: int = 120,
    max_iterations: int = 96,
    bounds: tuple[float, float, float, float] = (-1.8, 1.8, -1.35, 1.35),
) -> np.ndarray:
    """Compute a finite Julia escape-time grid without external rendering deps."""
    if width < 2 or height < 2:
        raise ValueError("width and height must be at least 2")
    xmin, xmax, ymin, ymax = bounds
    xs = np.linspace(xmin, xmax, width, dtype=float)
    ys = np.linspace(ymin, ymax, height, dtype=float)
    z = xs[None, :] + 1j * ys[:, None]
    escaped = np.zeros((height, width), dtype=bool)
    counts = np.full((height, width), max_iterations, dtype=np.int32)

    for iteration in range(max_iterations):
        active = ~escaped
        z[active] = z[active] * z[active] + c
        newly = active & (np.abs(z) > 2.0)
        counts[newly] = iteration + 1
        escaped |= newly
        if escaped.all():
            break
    return counts


def _normalized_entropy(values: np.ndarray, bins: int = 16) -> float:
    finite = values[np.isfinite(values)]
    if finite.size < 2:
        return 0.0
    histogram, _ = np.histogram(finite, bins=bins)
    probability = histogram.astype(float)
    total = float(probability.sum())
    if total <= 0.0:
        return 0.0
    probability = probability[probability > 0.0] / total
    entropy = float(-(probability * np.log(probability)).sum())
    return float(entropy / math.log(bins)) if bins > 1 else 0.0


def _spectral_structure(signal: np.ndarray) -> tuple[float, float]:
    if signal.size < 4:
        return 0.0, 0.0
    centered = signal - signal.mean()
    spectrum = np.abs(np.fft.rfft(centered)) ** 2
    if spectrum.size <= 1 or float(spectrum.sum()) <= 1e-15:
        return 0.0, 1.0
    spectrum = spectrum[1:]
    probability = spectrum / spectrum.sum()
    dominant = float(probability.max())
    geometric = float(np.exp(np.mean(np.log(spectrum + 1e-15))))
    arithmetic = float(np.mean(spectrum) + 1e-15)
    flatness = min(1.0, max(0.0, geometric / arithmetic))
    return dominant, flatness


def extract_orbit_features(
    orbit: Sequence[complex],
    *,
    escaped: bool,
    escape_iteration: int,
    max_iterations: int,
) -> dict[str, float]:
    """Extract bounded, documented features used by UI and comparisons."""
    if not orbit:
        raise ValueError("orbit must not be empty")
    values = np.asarray(orbit, dtype=np.complex128)
    magnitudes = np.abs(values)
    angles = np.unwrap(np.angle(values + 1e-15))
    deltas = np.abs(np.diff(values))

    tail = values[max(0, len(values) // 2) :]
    periodicity = 0.0
    if tail.size >= 6:
        candidates: list[float] = []
        scale = max(1.0, float(np.median(np.abs(tail))))
        for lag in range(1, min(24, tail.size // 2) + 1):
            distance = float(np.mean(np.abs(tail[lag:] - tail[:-lag]))) / scale
            candidates.append(math.exp(-4.0 * distance))
        periodicity = max(candidates, default=0.0)

    derivative = np.maximum(2.0 * magnitudes[1:], 1e-12)
    lyapunov_proxy = float(np.mean(np.log(derivative))) if derivative.size else 0.0
    lyapunov_scaled = 1.0 / (1.0 + math.exp(-lyapunov_proxy))
    dominant, flatness = _spectral_structure(magnitudes)

    finite_deltas = deltas[np.isfinite(deltas)]
    instability = 0.0
    if finite_deltas.size:
        p50 = float(np.percentile(finite_deltas, 50))
        p90 = float(np.percentile(finite_deltas, 90))
        instability = min(1.0, p90 / (p50 + p90 + 1e-12))

    boundedness = 0.0 if escaped else 1.0
    escape_speed = 1.0 - min(1.0, escape_iteration / max_iterations) if escaped else 0.0
    angular_turning = min(1.0, float(np.mean(np.abs(np.diff(angles)))) / math.pi) if angles.size > 1 else 0.0

    return {
        "boundedness": boundedness,
        "escape_speed": escape_speed,
        "periodicity": min(1.0, max(0.0, periodicity)),
        "orbit_entropy": min(1.0, max(0.0, _normalized_entropy(np.log1p(magnitudes)))),
        "spectral_concentration": min(1.0, max(0.0, dominant)),
        "spectral_flatness": flatness,
        "instability": instability,
        "angular_turning": angular_turning,
        "lyapunov_proxy": min(1.0, max(0.0, lyapunov_scaled)),
    }


def analyze_point(
    c_real: float,
    c_imag: float,
    *,
    max_iterations: int = 256,
    escape_radius: float = 2.0,
) -> OrbitReport:
    c = complex(float(c_real), float(c_imag))
    orbit, escaped, escape_iteration = mandelbrot_orbit(
        c,
        max_iterations=max_iterations,
        escape_radius=escape_radius,
    )
    features = extract_orbit_features(
        orbit,
        escaped=escaped,
        escape_iteration=escape_iteration,
        max_iterations=max_iterations,
    )
    serializable = tuple((float(z.real), float(z.imag)) for z in orbit)
    return OrbitReport(
        c_real=float(c_real),
        c_imag=float(c_imag),
        max_iterations=max_iterations,
        escape_radius=float(escape_radius),
        escaped=escaped,
        escape_iteration=escape_iteration,
        orbit=serializable,
        features=features,
    )


def sonification_events(
    report: OrbitReport,
    *,
    sample_limit: int = 96,
    base_frequency: float = 110.0,
) -> list[dict[str, float]]:
    """Map mathematical orbit properties to transparent WebAudio-style events."""
    if sample_limit < 1:
        raise ValueError("sample_limit must be positive")
    orbit = [complex(real, imag) for real, imag in report.orbit]
    if len(orbit) > sample_limit:
        indices = np.linspace(0, len(orbit) - 1, sample_limit, dtype=int)
        orbit = [orbit[int(index)] for index in indices]

    events: list[dict[str, float]] = []
    for index, z in enumerate(orbit):
        radius = abs(z)
        angle = math.atan2(z.imag, z.real)
        octave = min(5.0, math.log2(1.0 + radius))
        harmonic = 1.0 + 0.5 * (1.0 + math.sin(angle * 3.0))
        frequency = base_frequency * (2.0 ** octave) * harmonic
        events.append(
            {
                "time": index * 0.055,
                "frequency": float(min(4000.0, max(45.0, frequency))),
                "pan": float(max(-1.0, min(1.0, math.tanh(z.real)))),
                "gain": float(max(0.025, min(0.22, 0.16 / (1.0 + 0.35 * radius)))),
                "duration": float(0.045 + 0.08 * report.features["periodicity"]),
            }
        )
    return events


REGIONS = (
    "thalamic_input",
    "orbit_memory",
    "periodicity",
    "boundary_salience",
    "symmetry",
    "novelty",
    "integration",
)


def encode_brainsnn(report: OrbitReport, *, steps: int = 96) -> dict[str, object]:
    """Deterministic leaky-integrate-and-fire visualization surrogate.

    The output is explicitly an inspectable feature-to-spike encoding, not a
    claim about biological cortical organization.
    """
    if steps < 8:
        raise ValueError("steps must be at least 8")
    f = report.features
    drives = np.array(
        [
            0.20 + 0.75 * f["escape_speed"],
            0.15 + 0.70 * f["boundedness"],
            0.10 + 0.90 * f["periodicity"],
            0.18 + 0.82 * f["instability"],
            0.12 + 0.70 * f["angular_turning"],
            0.12 + 0.85 * f["orbit_entropy"],
            0.10 + 0.45 * f["spectral_concentration"] + 0.35 * f["lyapunov_proxy"],
        ],
        dtype=float,
    )
    weights = np.array(
        [
            [0, .25, .15, .35, .10, .20, .15],
            [.15, 0, .35, .10, .20, .12, .30],
            [.12, .20, 0, .08, .30, .10, .28],
            [.30, .08, .05, 0, .10, .35, .22],
            [.10, .18, .25, .10, 0, .12, .32],
            [.20, .10, .08, .28, .12, 0, .35],
            [.12, .22, .24, .20, .20, .26, 0],
        ],
        dtype=float,
    )
    membrane = np.zeros(len(REGIONS), dtype=float)
    refractory = np.zeros(len(REGIONS), dtype=int)
    spikes: dict[str, list[int]] = {name: [] for name in REGIONS}
    activations = np.zeros(len(REGIONS), dtype=float)
    previous = np.zeros(len(REGIONS), dtype=float)

    for step in range(steps):
        phase = np.sin((step + 1) * (0.17 + np.arange(len(REGIONS)) * 0.031))
        recurrent = weights.T @ previous
        input_current = drives * (0.72 + 0.18 * phase) + 0.22 * recurrent
        membrane = 0.84 * membrane + input_current
        membrane[refractory > 0] *= 0.45
        refractory = np.maximum(0, refractory - 1)
        fired = membrane >= 1.0
        for index in np.flatnonzero(fired):
            spikes[REGIONS[int(index)]].append(step)
        membrane[fired] = 0.0
        refractory[fired] = 2
        previous = fired.astype(float)
        activations += fired.astype(float)

    activation_map = {
        region: float(activations[index] / max(1, steps))
        for index, region in enumerate(REGIONS)
    }
    return {
        "schema": "gaugegap.brainsnn_encoding.v1",
        "regions": list(REGIONS),
        "spikes": spikes,
        "activation": activation_map,
        "weights": weights.round(6).tolist(),
        "claim_boundary": (
            "Deterministic visualization surrogate mapping finite orbit features to "
            "spikes; not a trained biological model or evidence of consciousness."
        ),
    }


ANALOGUE_LIBRARY: dict[str, dict[str, object]] = {
    "neuron_branching": {
        "label": "Neuron branching",
        "layer": "structural_analogy",
        "mechanism": "recursive branching and transport constraints, not Mandelbrot iteration",
        "features": {"boundedness": .72, "escape_speed": .18, "periodicity": .24, "orbit_entropy": .70, "spectral_concentration": .30, "spectral_flatness": .62, "instability": .51, "angular_turning": .73, "lyapunov_proxy": .48},
    },
    "lightning": {
        "label": "Lightning channel",
        "layer": "structural_analogy",
        "mechanism": "dielectric breakdown and branching instability",
        "features": {"boundedness": .14, "escape_speed": .81, "periodicity": .09, "orbit_entropy": .82, "spectral_concentration": .20, "spectral_flatness": .79, "instability": .91, "angular_turning": .68, "lyapunov_proxy": .78},
    },
    "river_delta": {
        "label": "River delta",
        "layer": "structural_analogy",
        "mechanism": "erosion, sediment transport, and flow optimization",
        "features": {"boundedness": .68, "escape_speed": .26, "periodicity": .18, "orbit_entropy": .66, "spectral_concentration": .33, "spectral_flatness": .58, "instability": .47, "angular_turning": .61, "lyapunov_proxy": .42},
    },
    "tree": {
        "label": "Tree branching",
        "layer": "structural_analogy",
        "mechanism": "growth, resource transport, and mechanical loading",
        "features": {"boundedness": .83, "escape_speed": .10, "periodicity": .36, "orbit_entropy": .59, "spectral_concentration": .45, "spectral_flatness": .44, "instability": .35, "angular_turning": .67, "lyapunov_proxy": .34},
    },
    "optical_caustic": {
        "label": "Coffee-cup optical caustic",
        "layer": "demonstrated_connection",
        "mechanism": "ray-envelope geometry produces a nephroid-like caustic; resemblance to the Mandelbrot cardioid is limited",
        "features": {"boundedness": .92, "escape_speed": .05, "periodicity": .76, "orbit_entropy": .31, "spectral_concentration": .76, "spectral_flatness": .19, "instability": .21, "angular_turning": .88, "lyapunov_proxy": .24},
    },
    "cardioid_microphone": {
        "label": "Cardioid microphone response",
        "layer": "demonstrated_connection",
        "mechanism": "polar response r(theta)=1+cos(theta); same named curve family, different system",
        "features": {"boundedness": .98, "escape_speed": .02, "periodicity": .92, "orbit_entropy": .22, "spectral_concentration": .91, "spectral_flatness": .08, "instability": .08, "angular_turning": .93, "lyapunov_proxy": .12},
    },
    "rose_window": {
        "label": "Gothic rose window",
        "layer": "structural_analogy",
        "mechanism": "designed radial symmetry and repeated motifs",
        "features": {"boundedness": .99, "escape_speed": .01, "periodicity": .96, "orbit_entropy": .42, "spectral_concentration": .85, "spectral_flatness": .11, "instability": .05, "angular_turning": .95, "lyapunov_proxy": .08},
    },
    "antenna_interference": {
        "label": "Wave interference lens",
        "layer": "demonstrated_connection",
        "mechanism": "superposition and phase interference; visual lotus resemblance is interpretive",
        "features": {"boundedness": .88, "escape_speed": .08, "periodicity": .89, "orbit_entropy": .38, "spectral_concentration": .82, "spectral_flatness": .16, "instability": .19, "angular_turning": .84, "lyapunov_proxy": .21},
    },
    "mandelbulb": {
        "label": "Mandelbulb",
        "layer": "demonstrated_connection",
        "mechanism": "a 3D fractal construction inspired by Mandelbrot-style iteration, not a unique canonical 3D extension",
        "features": {"boundedness": .62, "escape_speed": .30, "periodicity": .55, "orbit_entropy": .80, "spectral_concentration": .39, "spectral_flatness": .64, "instability": .73, "angular_turning": .78, "lyapunov_proxy": .68},
    },
    "eiffel_tower": {
        "label": "Eiffel Tower",
        "layer": "philosophical_interpretation",
        "mechanism": "tapered lattice engineering; calling it a 3D Mandelbrot tower is metaphor, not established derivation",
        "features": {"boundedness": .96, "escape_speed": .04, "periodicity": .70, "orbit_entropy": .49, "spectral_concentration": .63, "spectral_flatness": .29, "instability": .18, "angular_turning": .74, "lyapunov_proxy": .18},
    },
}


def compare_to_analogue(
    report: OrbitReport,
    target: str,
    *,
    user_prediction: float = 0.75,
) -> ComparisonReport:
    """Compare normalized feature vectors while preserving the evidence boundary."""
    if target not in ANALOGUE_LIBRARY:
        raise KeyError(f"unknown analogue: {target}")
    if not 0.0 <= user_prediction <= 1.0:
        raise ValueError("user_prediction must be in [0, 1]")
    item = ANALOGUE_LIBRARY[target]
    analogue = item["features"]
    names = sorted(set(report.features) & set(analogue))
    left = np.array([float(report.features[name]) for name in names], dtype=float)
    right = np.array([float(analogue[name]) for name in names], dtype=float)
    distance = np.abs(left - right)
    similarity = float(max(0.0, 1.0 - np.sqrt(np.mean(distance * distance))))
    strongest = names[int(np.argmin(distance))]
    weakest = names[int(np.argmax(distance))]
    return ComparisonReport(
        target=str(item["label"]),
        evidence_layer=str(item["layer"]),
        measured_similarity=similarity,
        user_prediction=float(user_prediction),
        gauge_gap=abs(float(user_prediction) - similarity),
        strongest_match=strongest,
        weakest_match=weakest,
        shared_mechanism=str(item["mechanism"]),
        boundary=(
            "Feature similarity is a finite descriptive comparison. It does not show "
            "that both systems obey the Mandelbrot recurrence or share a cause."
        ),
    )


def _hash_payload(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def build_fractal_reality_manifest(
    points: Iterable[tuple[str, float, float]] | None = None,
    *,
    max_iterations: int = 256,
) -> dict[str, object]:
    """Build a deterministic public handoff manifest for the browser experience."""
    selected = list(points or (
        ("cardioid_core", 0.0, 0.0),
        ("seahorse_valley", -0.743643887037151, 0.13182590420533),
        ("boundary_probe", -0.1011, 0.9563),
        ("escaping_control", 0.5, 0.5),
    ))
    experiments: list[dict[str, object]] = []
    for name, real, imag in selected:
        report = analyze_point(real, imag, max_iterations=max_iterations)
        comparisons = {
            key: compare_to_analogue(report, key, user_prediction=0.70).summary()
            for key in ANALOGUE_LIBRARY
        }
        experiments.append(
            {
                "id": name,
                "orbit": report.summary(),
                "sonification": sonification_events(report),
                "brainsnn": encode_brainsnn(report),
                "comparisons": comparisons,
            }
        )

    payload: dict[str, object] = {
        "schema": SCHEMA,
        "title": "Fractal Reality Lab",
        "equation": "z[n+1] = z[n]^2 + c, z[0] = 0",
        "positioning": (
            "An interactive GaugeGap experiment testing where Mandelbrot/Julia "
            "mathematics, sonification, natural-form analogies, and BrainSNN-style "
            "pattern encoding genuinely connect—and where they do not."
        ),
        "truth_layers": {
            "demonstrated_connection": "finite mathematics or a documented equation-level connection",
            "structural_analogy": "measurable resemblance without a demonstrated shared generator",
            "philosophical_interpretation": "meaningful metaphor or worldview, not scientific evidence",
        },
        "analogues": ANALOGUE_LIBRARY,
        "experiments": experiments,
        "claim_boundary": CLAIM_BOUNDARY,
        "do_not_claim": [
            "the Mandelbrot set is proven to be the literal code of physical reality",
            "all visually similar forms share the same generating equation",
            "coordinate sonification reveals an objective hidden cosmic harmony",
            "the Eiffel Tower is mathematically derived from a 3D Mandelbrot set",
            "the BrainSNN visualization is a biological or conscious neural system",
        ],
    }
    payload["content_sha256"] = _hash_payload(payload)
    return payload
