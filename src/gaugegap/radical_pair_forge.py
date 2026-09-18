"""Finite radical-pair spin-dynamics compass calculation.

The forge computes the singlet recombination yield of a photo-induced radical
pair as a function of the direction of a weak applied magnetic field.  This is
the spin-chemistry core of the cryptochrome magnetoreception hypothesis, reduced
to an exactly diagonalizable finite Hilbert space of two electron spins plus a
small, declared nuclear inventory.

It is deliberately hostile to the "quantum eye" reading of the mechanism.

Three results are STRUCTURAL: they follow from the form of the Hamiltonian and
hold for any hyperfine values.

1. The direction dependence vanishes identically when every hyperfine tensor is
   isotropic.  The compass comes from the anisotropy of a coupling tensor, not
   from the existence of entanglement in the pair.
2. The singlet yield obeys ``Phi_S(B) == Phi_S(-B)`` exactly.  Spin time
   reversal ``Theta`` is antiunitary with ``Theta S Theta^-1 = -S``, the
   hyperfine term is bilinear in spin and therefore even under ``Theta``, and
   the singlet projector is rotationally invariant, so ``Theta H(B) Theta^-1 =
   H(-B)`` leaves both the spectrum and ``|<m|P_S|n>|^2`` unchanged.  The
   mechanism carries inclination but no polarity information.  Note
   the antipode of a direction is ``(180 - theta, phi + 180)``: for a rhombic
   tensor the yield depends on azimuth too, so this is not a symmetry of the
   polar angle alone.
3. Fast recombination destroys the compass.  As ``k -> infinity`` the pair has no
   time to leave the singlet, the yield tends to one in every direction, and the
   anisotropy tends to zero.

One result is PARAMETER-DEPENDENT and is reported as a measurement of this
registry, not as a property of the mechanism:

4. Hyperfine coupling on the *second* radical suppresses the direction
   dependence, by ~8x for the illustrative ``trp-hbeta`` tensor used here.  This
   is a measurement of THIS registry and nothing more.  The code compares exactly
   two inventories, so it establishes neither the magnitude nor the sign for
   other partner tensors, magnitudes or orientations.  No theorem is offered, and
   the dependence is not even monotonic in the partner coupling strength, so do
   not generalize the direction of the effect either.

This model contains NO spin relaxation, so it establishes only the upper-rate
cutoff in (3).  It does not produce a lifetime window: the anisotropy is flat
or rising as ``k -> 0`` here, whereas a real pair is bounded at long lifetimes
by ``T2``.  Do not read a microsecond optimum out of this.

The Zeeman energy involved is recorded against ``k_B T`` at 300 K so no reader
can mistake the result for a thermal effect.

This is a finite spin-Hamiltonian calculation, not a measurement of
cryptochrome, not evidence that any animal uses this mechanism, and not a
magnetometer design.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field as dataclass_field
import math
from typing import Any, Iterable, Sequence

import numpy as np


CLAIM_BOUNDARY = (
    "finite radical-pair spin-Hamiltonian calculation under symmetric Haberkorn "
    "recombination only; reproduces the anisotropy, the polarity degeneracy and "
    "the fast-recombination cutoff of the radical-pair compass model, but not a "
    "lifetime window, because no spin relaxation is modelled; it is not a "
    "cryptochrome measurement, not evidence that any animal uses this mechanism, "
    "and not a magnetometer or sensor design"
)

# Physical constants (SI, CODATA-style values).
GYROMAGNETIC_RATIO_E = 2.0 * math.pi * 28.024951e9  # rad s^-1 T^-1
GEOMAGNETIC_FIELD_T = 50e-6                        # representative surface field
PLANCK_J_S = 6.62607015e-34
BOLTZMANN_J_PER_K = 1.380649e-23
MHZ_TO_RAD_PER_S = 2.0 * math.pi * 1e6

SOURCES = (
    {
        "kind": "literature_reference",
        "title": "Hore & Mouritsen, The Radical-Pair Mechanism of Magnetoreception",
        "identifier": "doi:10.1146/annurev-biophys-032116-094545",
        "scope": "mechanism review; this module reproduces none of its measurements",
    },
    {
        "kind": "literature_reference",
        "title": "Timmel et al., Effects of weak magnetic fields on free radical recombination reactions",
        "identifier": "Molecular Physics 95:71 (1998)",
        "scope": "source of the closed-form singlet yield expression implemented here",
    },
    {
        "kind": "literature_reference",
        "title": "Xu et al., Magnetic sensitivity of cryptochrome 4 from a migratory songbird",
        "identifier": "doi:10.1038/s41586-021-03618-9",
        "scope": (
            "in vitro magnetic sensitivity of ErCry4a; external context only, and "
            "not reproduced as a measurement here"
        ),
    },
)


@dataclass(frozen=True)
class HyperfineCoupling:
    """One nucleus, its principal hyperfine values, and which radical carries it."""

    name: str
    radical_index: int
    multiplicity: int
    principal_values_mhz: tuple[float, float, float]
    euler_deg: tuple[float, float, float] = (0.0, 0.0, 0.0)
    note: str = ""

    def __post_init__(self) -> None:
        if self.radical_index not in (0, 1):
            raise ValueError("radical_index must be 0 or 1")
        if self.multiplicity < 2:
            raise ValueError("multiplicity must be at least 2")

    @property
    def anisotropy_mhz(self) -> float:
        values = np.asarray(self.principal_values_mhz, dtype=float)
        return float(values.max() - values.min())

    def tensor_rad_per_s(self, *, isotropic: bool = False) -> np.ndarray:
        """Hyperfine tensor in the molecular frame, in rad/s.

        ``isotropic=True`` returns the trace-preserving isotropic control tensor,
        which is what makes the direction dependence vanish.
        """
        values = np.asarray(self.principal_values_mhz, dtype=float)
        if isotropic:
            values = np.full(3, values.mean())
        principal = np.diag(values) * MHZ_TO_RAD_PER_S
        rotation = _euler_zyz(*self.euler_deg)
        return rotation @ principal @ rotation.T

    def summary(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["principal_values_mhz"] = list(self.principal_values_mhz)
        payload["euler_deg"] = list(self.euler_deg)
        payload["anisotropy_mhz"] = self.anisotropy_mhz
        payload["nuclear_spin"] = (self.multiplicity - 1) / 2
        return payload


# Literature-style hyperfine values.  These are order-of-magnitude model inputs,
# not measurements reproduced by this repository, and the relative Euler
# orientations are illustrative.  The certified structural results (isotropy
# control, polarity degeneracy, fast-recombination collapse) do not depend on
# them.  The recorded numerical yields do, and so does the partner-suppression
# factor, which is a property of the trp-hbeta tensor below rather than of the
# mechanism.
HYPERFINE_REGISTRY: dict[str, HyperfineCoupling] = {
    "fad-n5": HyperfineCoupling(
        name="fad-n5",
        radical_index=0,
        multiplicity=3,
        principal_values_mhz=(-2.79, -2.79, 49.2),
        euler_deg=(0.0, 0.0, 0.0),
        note="FAD N5 14N, strongly axial; the dominant anisotropic coupling in the flavin radical",
    ),
    "fad-n10": HyperfineCoupling(
        name="fad-n10",
        radical_index=0,
        multiplicity=3,
        principal_values_mhz=(-0.36, -0.60, 16.0),
        euler_deg=(0.0, 30.0, 0.0),
        note="FAD N10 14N, secondary axial coupling on the same radical",
    ),
    "trp-hbeta": HyperfineCoupling(
        name="trp-hbeta",
        radical_index=1,
        multiplicity=2,
        principal_values_mhz=(-5.4, -21.6, -8.8),
        euler_deg=(0.0, 70.0, 25.0),
        note="tryptophan beta-proton, rhombic; loads the partner radical and suppresses the compass",
    ),
}

NUCLEAR_INVENTORIES: dict[str, tuple[str, ...]] = {
    # One anisotropically coupled nucleus on radical 1, nothing on radical 2.
    "spin-free-partner": ("fad-n5",),
    # Default: both radicals carry hyperfine coupling, as in a real flavin /
    # tryptophan pair.  This is the realistic case and the weaker compass.
    "cryptochrome-like": ("fad-n5", "trp-hbeta"),
    # A more loaded inventory; the compass degrades further.
    "loaded": ("fad-n5", "fad-n10", "trp-hbeta"),
}

# Stable slug per inventory. Used for benchmark_id and for the runner's default
# output directory, so a run is identified by the model it actually used.
INVENTORY_SLUGS: dict[str, str] = {
    "cryptochrome-like": "cryptochrome-compass",
    "spin-free-partner": "spin-free-partner",
    "loaded": "loaded",
}

DEFAULT_INVENTORY = "cryptochrome-like"
DEFAULT_RATE_PER_S = 1.0e6      # ~1 us radical-pair lifetime
FAST_RATE_PER_S = 1.0e10        # fast-recombination control
SYMMETRY_TOLERANCE = 1e-9
# The dense Liouvillian has side dim^2, so its memory and solve cost grow as
# dim^4 and dim^6.  Above this Hilbert dimension the cross-check falls back to a
# smaller fixed system rather than allocating gigabytes.
LIOUVILLIAN_DIM_LIMIT = 32
CROSS_CHECK_FALLBACK_INVENTORY = "cryptochrome-like"
# Rate points for the registered low-rate condition.  Held here, not taken from
# the caller's rate_points, so the condition is always evaluated.
LOW_RATE_PER_S = 1.0e3
LARMOR_COMPARABLE_RATE_PER_S = 1.0e6


PARTNER_PROBE_DIRECTIONS = 120
# Base partner tensor. The strength series below is generated as scalar multiples
# of this tuple, so the transverse-to-axial ratio -- the tensor SHAPE -- is held
# exactly fixed and only the magnitude varies. An earlier version of this probe
# hand-wrote each magnitude, which let shape drift from -0.057 to -0.100 across
# the series and confounded strength with shape, so its non-monotonicity result
# could not be attributed to coupling strength at all.
PARTNER_PROBE_BASE_MHZ = (-2.79, -2.79, 49.2)
PARTNER_PROBE_BASE_AXIAL_MHZ = 49.2
# Axial magnitudes in MHz, all at the base shape and orientation.
PARTNER_PROBE_STRENGTHS_MHZ = (49.2, 20.0, 5.0, 1.0, 0.2)
# Orientations in ZYZ Euler degrees, all at full base strength, so orientation is
# varied independently of magnitude.
PARTNER_PROBE_ORIENTATIONS_DEG = ((0.0, 90.0, 0.0),)


def _scaled_partner_tensor(axial_mhz: float) -> tuple[float, float, float]:
    """Scale the base tensor to a target axial magnitude, preserving its shape."""
    factor = axial_mhz / PARTNER_PROBE_BASE_AXIAL_MHZ
    return tuple(float(value * factor) for value in PARTNER_PROBE_BASE_MHZ)  # type: ignore[return-value]


def _euler_zyz(alpha_deg: float, beta_deg: float, gamma_deg: float) -> np.ndarray:
    """Rotation carrying a principal-axis frame into the molecular frame."""
    a, b, g = (math.radians(x) for x in (alpha_deg, beta_deg, gamma_deg))

    def rz(t: float) -> np.ndarray:
        return np.array([[math.cos(t), -math.sin(t), 0.0], [math.sin(t), math.cos(t), 0.0], [0.0, 0.0, 1.0]])

    def ry(t: float) -> np.ndarray:
        return np.array([[math.cos(t), 0.0, math.sin(t)], [0.0, 1.0, 0.0], [-math.sin(t), 0.0, math.cos(t)]])

    return rz(a) @ ry(b) @ rz(g)


def spin_operators(multiplicity: int) -> np.ndarray:
    """``(3, m, m)`` array of ``Sx, Sy, Sz`` for a spin of the given multiplicity."""
    if multiplicity < 2:
        raise ValueError("multiplicity must be at least 2")
    spin = (multiplicity - 1) / 2
    projections = np.arange(spin, -spin - 1, -1)
    s_z = np.diag(projections).astype(complex)
    ladder = np.sqrt(spin * (spin + 1) - projections[1:] * (projections[1:] + 1))
    s_plus = np.zeros((multiplicity, multiplicity), dtype=complex)
    s_plus[np.arange(multiplicity - 1), np.arange(1, multiplicity)] = ladder
    s_minus = s_plus.conj().T
    return np.array([(s_plus + s_minus) / 2, (s_plus - s_minus) / 2j, s_z])


def _embed(operator: np.ndarray, dims: Sequence[int], site: int) -> np.ndarray:
    out = np.array([[1.0 + 0.0j]])
    for index, dimension in enumerate(dims):
        factor = operator if index == site else np.eye(dimension, dtype=complex)
        out = np.kron(out, factor)
    return out


def hilbert_dims(couplings: Sequence[HyperfineCoupling]) -> tuple[int, ...]:
    """Two electron spins first, then one factor per nucleus."""
    return (2, 2, *(coupling.multiplicity for coupling in couplings))


def singlet_projector(dims: Sequence[int]) -> np.ndarray:
    """``|S><S|`` on the electron pair, tensored with the nuclear identity."""
    singlet = np.array([0.0, 1.0, -1.0, 0.0], dtype=complex) / math.sqrt(2.0)
    electronic = np.outer(singlet, singlet.conj())
    nuclear = int(np.prod(dims[2:])) if len(dims) > 2 else 1
    return np.kron(electronic, np.eye(nuclear, dtype=complex))


def build_hamiltonian(
    *,
    field_tesla: float,
    direction: Sequence[float],
    couplings: Sequence[HyperfineCoupling],
    isotropic: bool = False,
) -> np.ndarray:
    """``H = gamma_e B.(S1 + S2) + sum_n S_(radical) . A_n . I_n`` in rad/s."""
    dims = hilbert_dims(couplings)
    electron = {
        index: [_embed(op, dims, index) for op in spin_operators(2)]
        for index in (0, 1)
    }
    unit = np.asarray(direction, dtype=float)
    norm = float(np.linalg.norm(unit))
    if norm == 0.0:
        raise ValueError("direction must be a non-zero vector")
    unit = unit / norm
    larmor = GYROMAGNETIC_RATIO_E * float(field_tesla)
    hamiltonian = larmor * sum(
        unit[axis] * (electron[0][axis] + electron[1][axis]) for axis in range(3)
    )
    for offset, coupling in enumerate(couplings):
        nuclear = [_embed(op, dims, 2 + offset) for op in spin_operators(coupling.multiplicity)]
        tensor = coupling.tensor_rad_per_s(isotropic=isotropic)
        electron_ops = electron[coupling.radical_index]
        for i in range(3):
            for j in range(3):
                weight = tensor[i, j]
                if weight != 0.0:
                    hamiltonian = hamiltonian + weight * (electron_ops[i] @ nuclear[j])
    return hamiltonian


def singlet_yield_closed_form(
    hamiltonian: np.ndarray,
    projector: np.ndarray,
    rate_per_second: float,
) -> float:
    """Timmel-style yield for symmetric recombination ``k_S = k_T = k``.

    ``Phi_S = (1/Z) sum_mn |<m|P_S|n>|^2 k^2 / (k^2 + omega_mn^2)``, with
    ``Z = Tr P_S`` and ``omega_mn = E_m - E_n``.
    """
    if rate_per_second <= 0.0:
        raise ValueError("rate_per_second must be positive")
    energies, vectors = np.linalg.eigh(hamiltonian)
    overlaps = vectors.conj().T @ projector @ vectors
    gaps = energies[:, None] - energies[None, :]
    lorentzian = rate_per_second**2 / (rate_per_second**2 + gaps**2)
    partition = float(np.trace(projector).real)
    return float((np.abs(overlaps) ** 2 * lorentzian).sum() / partition)


def singlet_yield_liouvillian(
    hamiltonian: np.ndarray,
    projector: np.ndarray,
    singlet_rate: float,
    triplet_rate: float,
) -> float:
    """Exact yield from the Haberkorn master equation, allowing ``k_S != k_T``.

    Integrating ``drho/dt = -i[H, rho] - (1/2){k_S P_S + k_T P_T, rho}`` from
    zero to infinity is a linear solve, ``int rho dt = (-L)^-1 rho(0)``, so this
    needs no time stepping and is exact up to the linear solve.  No closed form
    exists for asymmetric rates, which is what makes it a real cross-check.
    """
    if singlet_rate <= 0.0 or triplet_rate <= 0.0:
        raise ValueError("recombination rates must be positive")
    dimension = hamiltonian.shape[0]
    identity = np.eye(dimension, dtype=complex)
    decay = singlet_rate * projector + triplet_rate * (identity - projector)
    liouvillian = -1j * (
        np.kron(identity, hamiltonian) - np.kron(hamiltonian.T, identity)
    ) - 0.5 * (np.kron(identity, decay) + np.kron(decay.T, identity))
    initial = projector / float(np.trace(projector).real)
    integrated = np.linalg.solve(-liouvillian, initial.flatten(order="F"))
    integrated = integrated.reshape(dimension, dimension, order="F")
    return float(singlet_rate * np.trace(projector @ integrated).real)


def fibonacci_directions(count: int) -> np.ndarray:
    """Deterministic, near-uniform unit vectors on the sphere."""
    if count < 2:
        raise ValueError("count must be at least 2")
    index = np.arange(count) + 0.5
    polar = np.arccos(1.0 - 2.0 * index / count)
    azimuth = math.pi * (1.0 + 5.0**0.5) * index
    return np.stack(
        [np.sin(polar) * np.cos(azimuth), np.sin(polar) * np.sin(azimuth), np.cos(polar)],
        axis=1,
    )


@dataclass(frozen=True)
class DirectionSample:
    index: int
    x: float
    y: float
    z: float
    polar_deg: float
    azimuth_deg: float
    singlet_yield: float
    # Yield at the true antipode (180 - theta, phi + 180).  Carried per sample so
    # the evidence bundle demonstrates the polarity degeneracy instead of merely
    # asserting it: the polar angle alone does not determine the yield.
    #
    # Deliberately REQUIRED, with no default.  A measured quantity that defaults
    # to 0.0 can be serialized unpopulated and read as a real measurement, which
    # is fabricated evidence; making it required means a code path that forgets
    # it fails loudly instead.
    antipodal_singlet_yield: float

    def summary(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DirectionSweep:
    inventory: str
    hilbert_dimension: int
    field_microtesla: float
    rate_per_second: float
    direction_count: int
    minimum_yield: float
    maximum_yield: float
    mean_yield: float
    anisotropy: float
    relative_contrast: float
    # NOTE: the isotropic-hyperfine control is deliberately NOT a field here.
    # It is a report-level comparison between two sweeps, computed once in
    # run_radical_pair_forge and published as
    # controls["isotropic_hyperfine_anisotropy"].  A per-sweep field would have
    # to be either recomputed on every call (the rate sweep alone runs eight) or
    # left unpopulated, and an unpopulated control field in an evidence bundle is
    # fabricated evidence.
    samples: tuple[DirectionSample, ...] = dataclass_field(default=(), repr=False)

    def summary(self, *, include_samples: bool = False) -> dict[str, Any]:
        payload = asdict(self)
        if include_samples:
            payload["samples"] = [sample.summary() for sample in self.samples]
        else:
            payload.pop("samples", None)
        return payload


@dataclass(frozen=True)
class RatePoint:
    rate_per_second: float
    anisotropy: float
    mean_yield: float

    def summary(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RadicalPairForgeReport:
    schema: str
    benchmark_id: str
    inventory: str
    hilbert_dimension: int
    field_microtesla: float
    larmor_frequency_mhz: float
    anisotropy: float
    relative_contrast: float
    passed: bool
    sweep: DirectionSweep
    rate_sweep: tuple[RatePoint, ...]
    couplings: tuple[HyperfineCoupling, ...]
    controls: dict[str, Any]
    claim_level: str
    claim_boundary: str
    exclusions: tuple[str, ...]

    def summary(self, *, include_samples: bool = False) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "benchmark_id": self.benchmark_id,
            "inventory": self.inventory,
            "hilbert_dimension": self.hilbert_dimension,
            "field_microtesla": self.field_microtesla,
            "larmor_frequency_mhz": self.larmor_frequency_mhz,
            "anisotropy": self.anisotropy,
            "relative_contrast": self.relative_contrast,
            "passed": self.passed,
            "sweep": self.sweep.summary(include_samples=include_samples),
            "rate_sweep": [point.summary() for point in self.rate_sweep],
            "couplings": [coupling.summary() for coupling in self.couplings],
            "controls": self.controls,
            "claim_level": self.claim_level,
            "claim_boundary": self.claim_boundary,
            "exclusions": list(self.exclusions),
        }


def resolve_inventory(inventory: str) -> tuple[HyperfineCoupling, ...]:
    if inventory not in NUCLEAR_INVENTORIES:
        known = ", ".join(sorted(NUCLEAR_INVENTORIES))
        raise ValueError(f"unknown inventory {inventory!r}; known inventories: {known}")
    return tuple(HYPERFINE_REGISTRY[name] for name in NUCLEAR_INVENTORIES[inventory])


def sweep_field_directions(
    *,
    couplings: Sequence[HyperfineCoupling],
    field_tesla: float = GEOMAGNETIC_FIELD_T,
    rate_per_second: float = DEFAULT_RATE_PER_S,
    direction_count: int = 200,
    isotropic: bool = False,
    keep_samples: bool = True,
    inventory: str = "custom",
) -> DirectionSweep:
    """Singlet yield over a deterministic sphere of field directions."""
    dims = hilbert_dims(couplings)
    projector = singlet_projector(dims)
    directions = fibonacci_directions(direction_count)
    yields = np.array(
        [
            singlet_yield_closed_form(
                build_hamiltonian(
                    field_tesla=field_tesla,
                    direction=direction,
                    couplings=couplings,
                    isotropic=isotropic,
                ),
                projector,
                rate_per_second,
            )
            for direction in directions
        ]
    )
    samples: tuple[DirectionSample, ...] = ()
    if keep_samples:
        antipodal = np.array(
            [
                singlet_yield_closed_form(
                    build_hamiltonian(
                        field_tesla=field_tesla,
                        direction=-direction,
                        couplings=couplings,
                        isotropic=isotropic,
                    ),
                    projector,
                    rate_per_second,
                )
                for direction in directions
            ]
        )
        samples = tuple(
            DirectionSample(
                index=index,
                x=float(direction[0]),
                y=float(direction[1]),
                z=float(direction[2]),
                polar_deg=float(math.degrees(math.acos(max(-1.0, min(1.0, direction[2]))))),
                azimuth_deg=float(math.degrees(math.atan2(direction[1], direction[0])) % 360.0),
                singlet_yield=float(value),
                antipodal_singlet_yield=float(mirrored),
            )
            for index, (direction, value, mirrored) in enumerate(
                zip(directions, yields, antipodal)
            )
        )
    mean_yield = float(yields.mean())
    anisotropy = float(yields.max() - yields.min())
    return DirectionSweep(
        inventory=inventory,
        hilbert_dimension=int(np.prod(dims)),
        field_microtesla=float(field_tesla * 1e6),
        rate_per_second=float(rate_per_second),
        direction_count=int(direction_count),
        minimum_yield=float(yields.min()),
        maximum_yield=float(yields.max()),
        mean_yield=mean_yield,
        anisotropy=anisotropy,
        relative_contrast=float(anisotropy / mean_yield) if mean_yield else 0.0,
        samples=samples,
    )


def polarity_residual(
    *,
    couplings: Sequence[HyperfineCoupling],
    field_tesla: float = GEOMAGNETIC_FIELD_T,
    rate_per_second: float = DEFAULT_RATE_PER_S,
    direction_count: int = 60,
) -> float:
    """``max |Phi_S(B) - Phi_S(-B)|``; exactly zero for this Hamiltonian."""
    projector = singlet_projector(hilbert_dims(couplings))

    def yield_for(direction: Iterable[float]) -> float:
        return singlet_yield_closed_form(
            build_hamiltonian(
                field_tesla=field_tesla, direction=direction, couplings=couplings
            ),
            projector,
            rate_per_second,
        )

    return max(
        abs(yield_for(direction) - yield_for(-direction))
        for direction in fibonacci_directions(direction_count)
    )


@dataclass(frozen=True)
class PartnerProbePoint:
    """One axial partner tensor and the anisotropy it leaves."""

    label: str
    # "strength" points vary magnitude at fixed shape and orientation;
    # "orientation" points vary orientation at fixed magnitude and shape.
    # Only the strength series supports a conclusion about coupling strength.
    axis: str
    principal_values_mhz: tuple[float, float, float]
    euler_deg: tuple[float, float, float]
    axial_mhz: float
    transverse_to_axial_ratio: float
    anisotropy: float
    ratio_to_spin_free: float
    increases_anisotropy: bool

    def summary(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["principal_values_mhz"] = list(self.principal_values_mhz)
        payload["euler_deg"] = list(self.euler_deg)
        return payload


def probe_partner_suppression(
    *,
    field_tesla: float = GEOMAGNETIC_FIELD_T,
    rate_per_second: float = DEFAULT_RATE_PER_S,
) -> tuple[PartnerProbePoint, ...]:
    """Measure what a range of partner tensors does to the anisotropy.

    The partner-suppression result is parameter-dependent, so the honest question
    is whether *any* partner coupling can increase the anisotropy rather than
    reduce it.  This probes that directly, and its output is recorded in the
    evidence bundle so the answer is reproducible rather than asserted: a claim
    about the direction of the effect has to be backed by the sweep that
    produced it.

    Uses a fixed direction count so the recorded numbers cannot drift from the
    prose that quotes them.
    """
    flavin = HYPERFINE_REGISTRY["fad-n5"]
    baseline = sweep_field_directions(
        couplings=(flavin,),
        field_tesla=field_tesla,
        rate_per_second=rate_per_second,
        direction_count=PARTNER_PROBE_DIRECTIONS,
        keep_samples=False,
        inventory="spin-free-partner",
    ).anisotropy

    specs: list[tuple[str, str, tuple[float, float, float], tuple[float, float, float]]] = [
        (
            f"strength-{magnitude:g}mhz",
            "strength",
            _scaled_partner_tensor(magnitude),
            (0.0, 0.0, 0.0),
        )
        for magnitude in PARTNER_PROBE_STRENGTHS_MHZ
    ]
    specs.extend(
        (
            f"orientation-beta{euler[1]:g}deg",
            "orientation",
            PARTNER_PROBE_BASE_MHZ,
            euler,
        )
        for euler in PARTNER_PROBE_ORIENTATIONS_DEG
    )

    points = []
    for label, axis, principal, euler in specs:
        partner = HyperfineCoupling(
            name=f"probe-{label}",
            radical_index=1,
            multiplicity=2,
            principal_values_mhz=principal,
            euler_deg=euler,
            note="synthetic probe tensor; not a literature value",
        )
        anisotropy = sweep_field_directions(
            couplings=(flavin, partner),
            field_tesla=field_tesla,
            rate_per_second=rate_per_second,
            direction_count=PARTNER_PROBE_DIRECTIONS,
            keep_samples=False,
            inventory=f"probe/{label}",
        ).anisotropy
        points.append(
            PartnerProbePoint(
                label=label,
                axis=axis,
                principal_values_mhz=principal,
                euler_deg=euler,
                axial_mhz=float(principal[2]),
                transverse_to_axial_ratio=float(principal[0] / principal[2]),
                anisotropy=anisotropy,
                ratio_to_spin_free=float(anisotropy / baseline) if baseline else 0.0,
                increases_anisotropy=anisotropy > baseline,
            )
        )
    return tuple(points)


def zeeman_thermal_ratio(field_tesla: float, temperature_k: float = 300.0) -> float:
    """Electron Zeeman quantum over ``k_B T``; ~2.2e-7 at 50 uT and 300 K."""
    energy = PLANCK_J_S * (GYROMAGNETIC_RATIO_E / (2.0 * math.pi)) * float(field_tesla)
    return float(energy / (BOLTZMANN_J_PER_K * float(temperature_k)))


def run_radical_pair_forge(
    *,
    inventory: str = DEFAULT_INVENTORY,
    field_tesla: float = GEOMAGNETIC_FIELD_T,
    rate_per_second: float = DEFAULT_RATE_PER_S,
    direction_count: int = 200,
    control_direction_count: int = 60,
    rate_points: Sequence[float] | None = None,
) -> RadicalPairForgeReport:
    if field_tesla <= 0.0:
        # field_microtesla, larmor_frequency_mhz and zeeman_thermal_ratio are all
        # published as magnitudes.  A negative field would serialize all three
        # negative while still passing every check, because the model is
        # polarity-invariant by construction.
        raise ValueError("field_tesla must be positive; it is reported as a magnitude")
    couplings = resolve_inventory(inventory)
    dims = hilbert_dims(couplings)
    projector = singlet_projector(dims)

    sweep = sweep_field_directions(
        couplings=couplings,
        field_tesla=field_tesla,
        rate_per_second=rate_per_second,
        direction_count=direction_count,
        inventory=inventory,
    )

    # Control 1 - isotropic hyperfine tensors must remove the compass entirely.
    isotropic = sweep_field_directions(
        couplings=couplings,
        field_tesla=field_tesla,
        rate_per_second=rate_per_second,
        direction_count=control_direction_count,
        isotropic=True,
        keep_samples=False,
        inventory=f"{inventory}/isotropic-control",
    )

    # Control 2 - no hyperfine coupling at all: H commutes with P_S, so the pair
    # never leaves the singlet and the yield is exactly one in every direction.
    bare = sweep_field_directions(
        couplings=(),
        field_tesla=field_tesla,
        rate_per_second=rate_per_second,
        direction_count=max(8, control_direction_count // 4),
        keep_samples=False,
        inventory="no-hyperfine-control",
    )

    # Control 3 - recombination far faster than precession erases the compass.
    fast = sweep_field_directions(
        couplings=couplings,
        field_tesla=field_tesla,
        rate_per_second=FAST_RATE_PER_S,
        direction_count=control_direction_count,
        keep_samples=False,
        inventory=f"{inventory}/fast-recombination-control",
    )

    # Control 4 - the cost of loading the partner radical.  This compares two
    # fixed inventories rather than the one under test, so the comparison stays
    # meaningful whichever inventory the caller selected.
    spin_free = sweep_field_directions(
        couplings=resolve_inventory("spin-free-partner"),
        field_tesla=field_tesla,
        rate_per_second=rate_per_second,
        direction_count=control_direction_count,
        keep_samples=False,
        inventory="spin-free-partner",
    )
    loaded_partner = sweep_field_directions(
        couplings=resolve_inventory("cryptochrome-like"),
        field_tesla=field_tesla,
        rate_per_second=rate_per_second,
        direction_count=control_direction_count,
        keep_samples=False,
        inventory="cryptochrome-like",
    )

    # Cross-check - closed form against the exact Liouvillian solve, including an
    # asymmetric-rate point where the closed form does not apply.
    #
    # The Liouvillian is dense and of side dim^2, so its cost grows as dim^6: the
    # dim-72 "loaded" inventory would need ~1.6 GiB of temporaries and a
    # 5184-square LU solve.  Above the threshold the cross-check runs on a fixed
    # smaller reference system instead, and the report records which was used --
    # the cross-check validates the closed-form expression, which is
    # inventory-independent, so a smaller system tests it just as well.
    if int(np.prod(dims)) <= LIOUVILLIAN_DIM_LIMIT:
        cross_check_couplings = couplings
        cross_check_inventory = inventory
    else:
        cross_check_couplings = resolve_inventory(CROSS_CHECK_FALLBACK_INVENTORY)
        cross_check_inventory = CROSS_CHECK_FALLBACK_INVENTORY
    cross_check_projector = singlet_projector(hilbert_dims(cross_check_couplings))
    reference = build_hamiltonian(
        field_tesla=field_tesla,
        direction=(0.0, 0.0, 1.0),
        couplings=cross_check_couplings,
    )
    closed = singlet_yield_closed_form(reference, cross_check_projector, rate_per_second)
    liouville = singlet_yield_liouvillian(
        reference, cross_check_projector, rate_per_second, rate_per_second
    )
    asymmetric = singlet_yield_liouvillian(
        reference, cross_check_projector, 2.0 * rate_per_second, rate_per_second
    )
    cross_check_residual = abs(closed - liouville)

    # Exact limits: instantaneous recombination traps the pair in the singlet.
    # Closed form only, so this always runs on the selected inventory.
    selected_reference = build_hamiltonian(
        field_tesla=field_tesla, direction=(0.0, 0.0, 1.0), couplings=couplings
    )
    prompt_limit = singlet_yield_closed_form(selected_reference, projector, 1e14)

    partner_probe = probe_partner_suppression(
        field_tesla=field_tesla, rate_per_second=rate_per_second
    )

    residual = polarity_residual(
        couplings=couplings,
        field_tesla=field_tesla,
        rate_per_second=rate_per_second,
        direction_count=control_direction_count,
    )

    if rate_points is None:
        rate_points = tuple(10.0**exponent for exponent in range(3, 11))
    rate_sweep = tuple(
        RatePoint(
            rate_per_second=float(rate),
            anisotropy=point.anisotropy,
            mean_yield=point.mean_yield,
        )
        for rate, point in (
            (
                rate,
                sweep_field_directions(
                    couplings=couplings,
                    field_tesla=field_tesla,
                    rate_per_second=rate,
                    direction_count=control_direction_count,
                    keep_samples=False,
                    inventory=inventory,
                ),
            )
            for rate in rate_points
        )
    )

    # The low-rate comparison is computed here, from its own rate points, rather
    # than read out of `rate_sweep`.  A caller passing rate_points=(1e6,) would
    # otherwise leave this registered condition unevaluated while the report
    # still reported passed.
    low_rate = sweep_field_directions(
        couplings=couplings,
        field_tesla=field_tesla,
        rate_per_second=LOW_RATE_PER_S,
        direction_count=control_direction_count,
        keep_samples=False,
        inventory=inventory,
    )
    larmor_rate = sweep_field_directions(
        couplings=couplings,
        field_tesla=field_tesla,
        rate_per_second=LARMOR_COMPARABLE_RATE_PER_S,
        direction_count=control_direction_count,
        keep_samples=False,
        inventory=inventory,
    )

    # Keys here MUST match hypotheses/radicalpair-0001.yaml validation.required
    # exactly.  test_every_declared_validation_is_implemented asserts set
    # equality in both directions, so the registry cannot claim a condition the
    # code never evaluates, and the code cannot gate on an unregistered one.
    checks = {
        "singlet_yield_anisotropy_positive_at_geomagnetic_field": sweep.anisotropy > 1e-6,
        "isotropic_hyperfine_control_anisotropy_below_tolerance": (
            isotropic.anisotropy < SYMMETRY_TOLERANCE
        ),
        "polarity_residual_below_tolerance": residual < SYMMETRY_TOLERANCE,
        "no_hyperfine_control_yield_is_unity_and_field_independent": (
            bare.anisotropy < SYMMETRY_TOLERANCE
            and abs(bare.mean_yield - 1.0) < SYMMETRY_TOLERANCE
        ),
        "fast_recombination_control_anisotropy_below_tolerance": fast.anisotropy < 1e-6,
        "spin_free_partner_anisotropy_exceeds_loaded_partner_anisotropy": (
            spin_free.anisotropy > loaded_partner.anisotropy
        ),
        "closed_form_and_liouvillian_yields_agree": cross_check_residual < 1e-9,
        "asymmetric_rates_have_no_closed_form_and_must_differ": (
            abs(asymmetric - closed) > 1e-6
        ),
        "prompt_recombination_limit_equals_one": abs(prompt_limit - 1.0) < 1e-6,
        "zeeman_thermal_ratio_recorded": 0.0 < zeeman_thermal_ratio(field_tesla) < 1e-3,
        "antipodal_yield_recorded_per_sampled_direction": bool(sweep.samples) and all(
            abs(sample.singlet_yield - sample.antipodal_singlet_yield) < SYMMETRY_TOLERANCE
            for sample in sweep.samples
        ),
        "anisotropy_at_low_rate_is_not_suppressed_relative_to_the_larmor_rate": (
            low_rate.anisotropy >= larmor_rate.anisotropy
        ),
    }

    controls: dict[str, Any] = {
        "checks": dict(checks),
        "symmetry_tolerance": SYMMETRY_TOLERANCE,
        "isotropic_hyperfine_anisotropy": isotropic.anisotropy,
        "isotropic_hyperfine_mean_yield": isotropic.mean_yield,
        "polarity_residual": residual,
        "no_hyperfine_anisotropy": bare.anisotropy,
        "no_hyperfine_mean_yield": bare.mean_yield,
        "fast_recombination_rate_per_second": FAST_RATE_PER_S,
        "fast_recombination_anisotropy": fast.anisotropy,
        "partner_probe": [point.summary() for point in partner_probe],
        "partner_probe_directions": PARTNER_PROBE_DIRECTIONS,
        "partner_probe_any_increase": any(p.increases_anisotropy for p in partner_probe),
        "partner_probe_note": (
            "Synthetic axial partner tensors spanning magnitude and orientation. No "
            "probe point increases the anisotropy, but the dependence is not monotonic "
            "in partner coupling strength, so no general claim about the direction of "
            "the effect is made."
        ),
        "spin_free_partner_anisotropy": spin_free.anisotropy,
        "loaded_partner_anisotropy": loaded_partner.anisotropy,
        "second_radical_suppression_factor": (
            float(spin_free.anisotropy / loaded_partner.anisotropy)
            if loaded_partner.anisotropy
            else 0.0
        ),
        "closed_form_yield": closed,
        "liouvillian_yield": liouville,
        "closed_form_vs_liouvillian_residual": cross_check_residual,
        "cross_check_inventory": cross_check_inventory,
        "cross_check_hilbert_dimension": int(np.prod(hilbert_dims(cross_check_couplings))),
        "liouvillian_dim_limit": LIOUVILLIAN_DIM_LIMIT,
        "asymmetric_rate_yield": asymmetric,
        "prompt_recombination_limit": prompt_limit,
        "low_rate_per_second": LOW_RATE_PER_S,
        "low_rate_anisotropy": low_rate.anisotropy,
        "larmor_comparable_rate_per_second": LARMOR_COMPARABLE_RATE_PER_S,
        "larmor_comparable_anisotropy": larmor_rate.anisotropy,
        "zeeman_thermal_ratio_300k": zeeman_thermal_ratio(field_tesla),
        "zeeman_thermal_ratio_300k_at_5mt": zeeman_thermal_ratio(5e-3),
        "fridge_magnet_note": (
            "A 5 mT magnet raises the Zeeman quantum by only two orders of magnitude "
            "and is still ~1e-5 of k_B T at 300 K.  Neither field can drive a thermal "
            "population change, and neither saturates this model, so the weak-field "
            "result is not explained by field strength alone."
        ),
        "relaxation_note": (
            "No spin relaxation is modelled, so the long-lifetime side of the rate "
            "window is not reproduced: anisotropy persists as k -> 0 here, whereas a "
            "real pair is limited by T2 of order microseconds."
        ),
    }

    return RadicalPairForgeReport(
        schema="gaugegap.radical_pair_forge.v1",
        benchmark_id=f"radicalpair-0001-{INVENTORY_SLUGS[inventory]}",
        inventory=inventory,
        hilbert_dimension=int(np.prod(dims)),
        field_microtesla=float(field_tesla * 1e6),
        larmor_frequency_mhz=float(GYROMAGNETIC_RATIO_E * field_tesla / (2.0 * math.pi) / 1e6),
        anisotropy=sweep.anisotropy,
        relative_contrast=sweep.relative_contrast,
        passed=all(checks.values()),
        sweep=sweep,
        rate_sweep=rate_sweep,
        couplings=couplings,
        controls=controls,
        claim_level="reproducible_finite_result",
        claim_boundary=CLAIM_BOUNDARY,
        exclusions=(
            "does not measure cryptochrome, flavin, or any protein",
            "does not show that any bird, insect, or other animal uses this mechanism",
            "does not demonstrate quantum coherence in living tissue",
            "does not model spin relaxation, exchange, or dipolar coupling",
            "does not model protein orientational ordering, which the compass hypothesis requires",
            "is not a magnetometer, sensor, or device design, and gives no sensitivity figure",
            "does not support any claim that entanglement carries information or acts at a distance",
        ),
    )
