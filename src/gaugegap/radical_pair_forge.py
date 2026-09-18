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

from dataclasses import asdict, dataclass, field as dataclass_field, fields
import math
import sys
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

# Bounds on accepted numeric inputs, DERIVED from the largest finite double and
# the factor each input is multiplied by before it reaches an operator, not
# chosen.  Finiteness of the input is not enough: a positive finite value can
# overflow the operator built from it, and that overflow does not always raise.
# At k = 1e308 the direct Liouvillian solve returned nan, which would serialize
# as a measured yield; at B = 1e308 T the Hamiltonian went non-finite and died
# inside eigh.  The registry's kill criteria cover both cases.
#
# The factor of 4 is headroom for the terms that land in the same matrix entry:
# the Zeeman and hyperfine terms add into one Hamiltonian, and the two decay
# Kronecker terms add into one Liouvillian.
_DOUBLE_MAX = float(np.finfo(float).max)
MAX_FIELD_TESLA = _DOUBLE_MAX / GYROMAGNETIC_RATIO_E / 4.0
MAX_RATE_PER_S = _DOUBLE_MAX / 4.0
MAX_HYPERFINE_MHZ = _DOUBLE_MAX / MHZ_TO_RAD_PER_S / 4.0

# Counts are bounded by what they allocate, for the same reason magnitudes are
# bounded by what they overflow.  An accepted count that dies in an allocation
# is the same defect as an accepted rate that dies in a solve -- and it need not
# even be loud: on numpy 2.4.6, `--direction-count 9223372036854775808`
# overflows int64 inside np.arange and returns an EMPTY grid, so the sweep ran
# on zero directions and failed later in a reduction, several frames from the
# argument that caused it.
#
# Both caps are arithmetic on a declared budget rather than chosen numbers. The
# budgets are deliberately generous: 2.1e6 directions is four orders of
# magnitude past any meaningful angular resolution on a sphere, and dimension
# 2048 is nearly thirty times the largest registered inventory.
DIRECTION_GRID_BUDGET_BYTES = 64 * 1024 * 1024
OPERATOR_BUDGET_BYTES = 64 * 1024 * 1024
_BYTES_PER_COMPLEX = 16
MAX_HILBERT_DIMENSION = math.isqrt(OPERATOR_BUDGET_BYTES // _BYTES_PER_COMPLEX)


def _require_positive_finite(
    name: str,
    value: float,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    """Reject non-finite, non-positive, and operator-breaking values.

    A bare ``value <= 0.0`` test admits nan (all comparisons false) and inf.
    Either then propagates into the Hamiltonian or the Lorentzian and surfaces
    as an opaque LinAlgError or a NaN serialized into the evidence bundle.  A
    finite value above ``maximum`` does the same one step later, when the
    operator built from it overflows -- and one below ``minimum`` does it at the
    other end, by underflowing to zero inside that operator.  Used at every
    numeric boundary rather than only the one a finding names.
    """
    numeric = float(value)
    if not math.isfinite(numeric) or numeric <= 0.0:
        raise ValueError(
            f"{name} must be a positive finite value; got {value!r}"
        )
    if maximum is not None and numeric > maximum:
        raise ValueError(
            f"{name} must be at most {maximum:.6e} so the operators built from it "
            f"stay finite; got {value!r}"
        )
    if minimum is not None and numeric < minimum:
        raise ValueError(
            f"{name} must be at least {minimum:.6e} so the operators built from it "
            f"keep their relative coefficients; got {value!r}"
        )
    return numeric


def _require_finite_magnitude(
    name: str, value: float, maximum: float | None = None
) -> float:
    """Same guard for a signed quantity, where zero and negatives are legitimate.

    Hyperfine principal values are routinely negative, so they cannot go through
    the positivity check, but they reach the same matrices and overflow them the
    same way.
    """
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"{name} must be finite; got {value!r}")
    if maximum is not None and abs(numeric) > maximum:
        raise ValueError(
            f"{name} must have magnitude at most {maximum:.6e} so the operators "
            f"built from it stay finite; got {value!r}"
        )
    return numeric


def _require_three_vector(name: str, value: Any) -> np.ndarray:
    """Convert to a finite ``(3,)`` float array, or say exactly what was wrong.

    A ``Sequence[float]`` annotation is not a shape check.  A four-component
    direction was normalized using all four components while the Zeeman sum used
    the first three, so the requested field contribution came out a factor of
    sqrt(2) small with nothing raised; a two-component one failed later with an
    IndexError from inside the sum; and a hyperfine tuple of the wrong length
    could be stored in a registry and only fail when a tensor was built from it,
    with a matmul dimension error naming neither the coupling nor the field.
    """
    array = np.asarray(value, dtype=float)
    if array.shape != (3,):
        raise ValueError(
            f"{name} must have exactly three components; got shape "
            f"{array.shape} from {value!r}"
        )
    for index, component in enumerate(array):
        _require_finite_magnitude(f"{name}[{index}]", float(component))
    return array


def validate_field_tesla(name: str, field_tesla: float) -> float:
    """Public form of the field check, so callers apply it rather than copy it.

    The CLI takes microtesla and has to validate the value it will actually
    pass: the conversion is not order-preserving at the bottom, where 5e-324 uT
    becomes exactly 0.0 tesla.
    """
    return _require_positive_finite(name, field_tesla, maximum=MAX_FIELD_TESLA)


def _require_finite_output(name: str, value: Any) -> Any:
    """Backstop: no non-finite computed quantity may be used or published.

    The per-input bounds above give a clear error naming the offending input.
    This catches whatever they do not -- a combination of inputs, an
    intermediate that underflows, or a term added later -- because
    np.linalg.solve returns nan rather than raising, and a nan yield is
    fabricated evidence, not a crash.  Applies to scalars as well as operators:
    the same defect shows up as an inf ratio as readily as an inf matrix.
    """
    if not np.isfinite(value).all():
        raise ValueError(
            f"{name} is not finite; the inputs are within their individual bounds "
            "but overflow or underflow in combination"
        )
    return value


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
        if self.multiplicity > MAX_HILBERT_DIMENSION:
            raise ValueError(
                f"{self.name}.multiplicity must be at most {MAX_HILBERT_DIMENSION}; "
                f"got {self.multiplicity}"
            )
        principal = _require_three_vector(
            f"{self.name}.principal_values_mhz", self.principal_values_mhz
        )
        for index, value in enumerate(principal):
            _require_finite_magnitude(
                f"{self.name}.principal_values_mhz[{index}]", value, MAX_HYPERFINE_MHZ
            )
        # No magnitude bound on the angles: any finite angle is meaningful. An
        # infinite one gives nan through cos/sin and a silently non-finite tensor.
        _require_three_vector(f"{self.name}.euler_deg", self.euler_deg)

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
# Field magnitudes for the no-hyperfine control. The registered condition claims
# the yield is FIELD-independent, which cannot be shown from a single magnitude
# however many directions it sweeps, so the control is evaluated at two decades.
NO_HYPERFINE_CONTROL_FIELDS_T = (GEOMAGNETIC_FIELD_T, 5.0e-3)
# Relative tolerance for deciding whether a caller is already at a registered
# parameter. Exact float equality is wrong here: the CLI computes 50.0 * 1e-6 =
# 4.9999999999999996e-05, which is not == 50e-6, so an exact test silently sends
# the default path down the recompute branch and puts two values for the same
# quantity in one bundle.
REGISTERED_PARAMETER_RTOL = 1e-9
# Angular resolution the hypothesis registers. Anisotropy is the sampled maximum
# minus minimum, so the grid size is part of the measured value: a 40-direction
# run and a 200-direction run do not measure the same quantity. The registered
# conditions are therefore a field, a rate AND a resolution.
REGISTERED_DIRECTION_COUNT = 200
# Rate for the k -> infinity limit check.  Named rather than inlined so the
# report can publish the rate the limit was taken at.
PROMPT_RATE_PER_S = 1.0e14
# Largest |omega/k| carried into the Lorentzian.  Its square, 1e300, is still
# finite in double precision, and 1/(1 + 1e300) is below 1e-300, so clipping
# here changes no representable yield while keeping a denormal-small rate from
# overflowing the ratio to inf.
LORENTZIAN_RATIO_CLIP = 1.0e150


def _at_registered_conditions(
    field_tesla: float, rate_per_second: float, direction_count: int
) -> bool:
    """True when field, rate and resolution all match the registered conditions."""
    return (
        math.isclose(field_tesla, GEOMAGNETIC_FIELD_T, rel_tol=REGISTERED_PARAMETER_RTOL)
        and math.isclose(
            rate_per_second, DEFAULT_RATE_PER_S, rel_tol=REGISTERED_PARAMETER_RTOL
        )
        and int(direction_count) == REGISTERED_DIRECTION_COUNT
    )


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
    # Bounded as well as positive: multiplicity 2**20 asks for an 8 TiB operator
    # and dies in numpy's allocator, with nothing naming the multiplicity.
    if multiplicity > MAX_HILBERT_DIMENSION:
        raise ValueError(
            f"multiplicity must be at most {MAX_HILBERT_DIMENSION} so its "
            f"operators fit the declared budget; got {multiplicity}"
        )
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
    dims = (2, 2, *(coupling.multiplicity for coupling in couplings))
    # Each multiplicity is bounded on its own, but the Hilbert space is their
    # PRODUCT: enough legal couplings still asks for an operator no budget
    # covers, and the failure would land in an allocator rather than here.
    dimension = 1
    for factor in dims:
        dimension *= int(factor)
    if dimension > MAX_HILBERT_DIMENSION:
        raise ValueError(
            f"nuclear inventory gives Hilbert dimension {dimension}, above the "
            f"declared budget of {MAX_HILBERT_DIMENSION}"
        )
    return dims


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
    # Shape first: the sum below reads exactly three components, so a longer
    # vector would be normalized using components the Hamiltonian never sees.
    unit = _require_three_vector("direction", direction)
    # Scale by the largest component before taking the norm.  For (1e308, 0, 0)
    # every component is finite but the norm overflows to inf, and dividing by
    # it gives exactly (0, 0, 0): the Zeeman term vanishes and the Hamiltonian
    # stays finite, so nothing downstream notices that the requested direction
    # was silently discarded.  After scaling, no component exceeds 1 and the
    # norm lies in [1, sqrt(3)].
    largest = float(np.abs(unit).max())
    if largest == 0.0:
        raise ValueError("direction must be a non-zero vector")
    unit = unit / largest
    unit = _require_finite_output("direction", unit / float(np.linalg.norm(unit)))
    # Bounded, not merely finite: 1e308 T is a positive finite input whose
    # Larmor term overflows, and the non-finite Hamiltonian then dies inside
    # eigh with "Eigenvalues did not converge".
    _require_positive_finite("field_tesla", field_tesla, maximum=MAX_FIELD_TESLA)
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
    return _require_finite_output("hamiltonian", hamiltonian)


def singlet_yield_closed_form(
    hamiltonian: np.ndarray,
    projector: np.ndarray,
    rate_per_second: float,
) -> float:
    """Timmel-style yield for symmetric recombination ``k_S = k_T = k``.

    ``Phi_S = (1/Z) sum_mn |<m|P_S|n>|^2 k^2 / (k^2 + omega_mn^2)``, with
    ``Z = Tr P_S`` and ``omega_mn = E_m - E_n``.
    """
    _require_positive_finite("rate_per_second", rate_per_second, maximum=MAX_RATE_PER_S)
    energies, vectors = np.linalg.eigh(hamiltonian)
    overlaps = vectors.conj().T @ projector @ vectors
    gaps = energies[:, None] - energies[None, :]
    # Scaled form of k^2 / (k^2 + omega^2).  The unscaled numerator is a Python
    # float squaring, so any rate above ~1.34e154 raises OverflowError and
    # aborts the run instead of saturating to the k -> infinity limit; the ratio
    # itself overflows to inf for a denormal-small rate.  Clipping the ratio
    # magnitude removes both failure modes without changing a representable
    # yield.
    with np.errstate(over="ignore"):
        ratio = np.minimum(np.abs(gaps) / rate_per_second, LORENTZIAN_RATIO_CLIP)
    lorentzian = 1.0 / (1.0 + ratio**2)
    partition = float(np.trace(projector).real)
    return float((np.abs(overlaps) ** 2 * lorentzian).sum() / partition)


def _build_liouvillian(
    hamiltonian: np.ndarray,
    projector: np.ndarray,
    singlet_rate: float,
    triplet_rate: float,
) -> np.ndarray:
    """``L`` for ``drho/dt = -i[H, rho] - (1/2){k_S P_S + k_T P_T, rho}``.

    Shared by both solvers.  They had a copy each, so a bound added to one would
    have left the other accepting a rate that overflows the decay term -- and
    the direct solve does not raise on a non-finite matrix, it returns nan.
    """
    dimension = hamiltonian.shape[0]
    identity = np.eye(dimension, dtype=complex)
    complement = identity - projector
    # A positive finite rate can still vanish from the decay operator.  The
    # singlet projector's nonzero entries are 0.5, so k = 5e-324 multiplies to
    # exactly zero: the singlet block disappears, L is singular, and BOTH
    # solvers then return nan without raising.  The floor is derived from the
    # smallest nonzero entry the rate actually multiplies, so it follows the
    # projector rather than assuming this one.
    weights = np.concatenate([np.abs(projector).ravel(), np.abs(complement).ravel()])
    positive = weights[weights > 0.0]
    minimum_rate = float(np.finfo(float).tiny) / float(positive.min()) if positive.size else None
    _require_positive_finite(
        "singlet_rate", singlet_rate, minimum=minimum_rate, maximum=MAX_RATE_PER_S
    )
    _require_positive_finite(
        "triplet_rate", triplet_rate, minimum=minimum_rate, maximum=MAX_RATE_PER_S
    )
    decay = singlet_rate * projector + triplet_rate * complement
    liouvillian = -1j * (
        np.kron(identity, hamiltonian) - np.kron(hamiltonian.T, identity)
    ) - 0.5 * (np.kron(identity, decay) + np.kron(decay.T, identity))
    return _require_finite_output("liouvillian", liouvillian)


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
    liouvillian = _build_liouvillian(hamiltonian, projector, singlet_rate, triplet_rate)
    dimension = hamiltonian.shape[0]
    initial = projector / float(np.trace(projector).real)
    integrated = np.linalg.solve(-liouvillian, initial.flatten(order="F"))
    integrated = integrated.reshape(dimension, dimension, order="F")
    # The rate floor above cannot predict every degenerate case: at 4.5e-308 the
    # rate is normal and the decay operator is populated, but L is singular to
    # working precision and np.linalg.solve returns nan rather than raising.
    return float(
        _require_finite_output(
            "singlet_yield_liouvillian", singlet_rate * np.trace(projector @ integrated).real
        )
    )


def singlet_yield_liouvillian_eigen(
    hamiltonian: np.ndarray,
    projector: np.ndarray,
    singlet_rate: float,
    triplet_rate: float,
) -> float:
    """Same yield as ``singlet_yield_liouvillian`` by an independent algorithm.

    Both compute ``int rho dt = (-L)^-1 rho(0)``, but this one diagonalizes the
    Liouvillian and inverts its eigenvalues rather than running a direct LU solve
    on ``L``.  That makes it a real cross-check of the asymmetric-rate
    calculation, which has no closed form to compare against.

    It replaces an earlier gate that merely required the asymmetric yield to
    DIFFER from the symmetric closed form.  That requirement is false in general:
    with no hyperfine coupling the Hamiltonian preserves the initial singlet and
    both symmetric and asymmetric recombination give unit yield, so the two agree
    exactly and the gate would have failed a perfectly correct calculation.

    Unlike the direct solve, this route has a lower rate limit.  Inverting the
    eigenvalues of a non-Hermitian Liouvillian whose spectrum spans ``|H|`` down
    to ``k`` carries a relative error of order ``eps * |H| / k``, so it silently
    loses accuracy as the rate falls: for the spin-free-partner system at 50 uT
    it agrees with the closed form to ten digits at ``k = 1e3`` and returns
    0.1667 against a true 0.4958 at ``k = 1e-10``, with nothing raised.  It
    therefore refuses below ``sqrt(eps) * |H|``, where that error is at most
    ``sqrt(eps)``.  The direct solve matches the closed form at every rate tested
    down to 1e-20 and has no such limit.
    """
    liouvillian = _build_liouvillian(hamiltonian, projector, singlet_rate, triplet_rate)
    # Derived from machine epsilon and the Hamiltonian's own scale, so it tracks
    # the system rather than naming a rate.
    conditioning_floor = math.sqrt(float(np.finfo(float).eps)) * float(
        np.abs(hamiltonian).max()
    )
    for name, rate in (("singlet_rate", singlet_rate), ("triplet_rate", triplet_rate)):
        if float(rate) < conditioning_floor:
            raise ValueError(
                f"{name} must be at least {conditioning_floor:.6e} for the "
                "eigendecomposition route, whose relative error grows as "
                "eps * |H| / k; use singlet_yield_liouvillian, which is accurate "
                f"at any representable rate. Got {rate!r}"
            )
    dimension = hamiltonian.shape[0]
    eigenvalues, eigenvectors = np.linalg.eig(liouvillian)
    initial = (projector / float(np.trace(projector).real)).flatten(order="F")
    coefficients = np.linalg.solve(eigenvectors, initial)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        integrated = (eigenvectors @ (coefficients / (-eigenvalues))).reshape(
            dimension, dimension, order="F"
        )
    # Same backstop as the direct route: inverting an eigenvalue of a singular
    # Liouvillian gives inf, and the trace of it nan, with nothing raised.
    return float(
        _require_finite_output(
            "singlet_yield_liouvillian_eigen",
            singlet_rate * np.trace(projector @ integrated).real,
        )
    )


def fibonacci_directions(count: int) -> np.ndarray:
    """Deterministic, near-uniform unit vectors on the sphere."""
    if count < 2:
        raise ValueError("count must be at least 2")
    # Upper bound too, and for a reason worse than cost: 2**63 overflows int64
    # inside np.arange, which returns an EMPTY grid rather than raising, so the
    # sweep silently ran on zero directions.
    if count > MAX_DIRECTION_COUNT:
        raise ValueError(
            f"count must be at most {MAX_DIRECTION_COUNT} so the direction grid "
            f"fits the declared budget; got {count}"
        )
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


# Per direction, at peak, the sweep holds:
#   - the (count, 3) grid and its construction temporaries -- index, polar,
#     azimuth, three coordinate arrays and the stacked result -- which is nine
#     float64 values;
#   - one retained DirectionSample when samples are kept, whose real cost is the
#     object, its __dict__ and its boxed floats, MEASURED here from an instance
#     rather than assumed.  The first version of this constant counted four
#     float64 values, 32 bytes, against an actual 556: a cap advertised as
#     fitting a 64 MiB budget would have needed about 1.1 GiB.
_GRID_BYTES_PER_DIRECTION = 9 * 8
_SAMPLE_TEMPLATE = DirectionSample(
    index=0,
    x=0.0,
    y=0.0,
    z=1.0,
    polar_deg=0.0,
    azimuth_deg=0.0,
    singlet_yield=0.0,
    antipodal_singlet_yield=0.0,
)
_SAMPLE_DICT = getattr(_SAMPLE_TEMPLATE, "__dict__", None)
_SAMPLE_BYTES = (
    sys.getsizeof(_SAMPLE_TEMPLATE)
    + (sys.getsizeof(_SAMPLE_DICT) if _SAMPLE_DICT is not None else 0)
    + len(fields(_SAMPLE_TEMPLATE)) * sys.getsizeof(0.5)
    + 8  # the list slot that holds it
)
BYTES_PER_DIRECTION = _GRID_BYTES_PER_DIRECTION + _SAMPLE_BYTES
MAX_DIRECTION_COUNT = DIRECTION_GRID_BUDGET_BYTES // BYTES_PER_DIRECTION


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
    # Angular resolution this point was computed at. Recorded because a rate
    # series evaluated at a different resolution from the headline sweep would
    # otherwise put two unexplained values for the same quantity in one bundle.
    direction_count: int

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
    prose that quotes them.  Callers are expected to pass the registered field
    and rate: the probe's non-monotonicity result is a statement about the
    registered conditions, and at 0.5 T the same tensors give ratios an order of
    magnitude different.
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
    # temperature_k reaches a division: 0.0 raised ZeroDivisionError and a
    # negative value returned a negative "ratio" that the gate reads as failing.
    _require_positive_finite("field_tesla", field_tesla, maximum=MAX_FIELD_TESLA)
    _require_positive_finite("temperature_k", temperature_k)
    # Positive and finite is not enough at the bottom either: k_B * 1e-320
    # underflows to exactly zero and the division raises ZeroDivisionError, and
    # a denominator one decade larger returns a ratio of 1e295 that means
    # nothing.  The bound that matters is on the computed denominator, not on a
    # temperature picked in advance.
    denominator = BOLTZMANN_J_PER_K * float(temperature_k)
    if denominator <= 0.0:
        raise ValueError(
            "temperature_k must be large enough that k_B * T is representable; "
            f"got {temperature_k!r}"
        )
    # Constants first, field last.  Multiplying the energy out before dividing
    # underflows the NUMERATOR for a small field -- at 1e-310 T the energy
    # rounds to zero and the function published 0.0, although the ratio itself,
    # 4.48e-313, is perfectly representable.  A fabricated zero is worse than an
    # error, so the reordered result is also required to be non-zero.
    coefficient = PLANCK_J_S * (GYROMAGNETIC_RATIO_E / (2.0 * math.pi)) / denominator
    ratio = coefficient * float(field_tesla)
    if ratio <= 0.0:
        raise ValueError(
            "field_tesla is too small for a representable Zeeman/kT ratio at "
            f"{temperature_k!r} K; got {field_tesla!r}"
        )
    return float(_require_finite_output("zeeman_thermal_ratio", ratio))


def run_radical_pair_forge(
    *,
    inventory: str = DEFAULT_INVENTORY,
    field_tesla: float = GEOMAGNETIC_FIELD_T,
    rate_per_second: float = DEFAULT_RATE_PER_S,
    direction_count: int = 200,
    rate_points: Sequence[float] | None = None,
) -> RadicalPairForgeReport:
    # field_microtesla, larmor_frequency_mhz and zeeman_thermal_ratio are all
    # published as magnitudes, so a negative field would serialize all three
    # negative while still passing every check (the model is polarity-invariant
    # by construction). Non-finite values pass a bare positivity test and then
    # fail opaquely inside eigh, so every numeric input goes through the shared
    # validator rather than an inline comparison against zero.
    _require_positive_finite("field_tesla", field_tesla, maximum=MAX_FIELD_TESLA)
    _require_positive_finite("rate_per_second", rate_per_second, maximum=MAX_RATE_PER_S)
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

    # Every registered control below goes through this helper, so a control can
    # never silently inherit a caller's field, rate or resolution. Five of them
    # did, and each was found separately by review; the helper exists so there
    # is no sixth.
    def registered_sweep(
        *,
        control_couplings: Sequence[HyperfineCoupling] = couplings,
        control_field: float = GEOMAGNETIC_FIELD_T,
        control_rate: float = DEFAULT_RATE_PER_S,
        isotropic_tensors: bool = False,
        keep_samples: bool = False,
        label: str = inventory,
    ) -> DirectionSweep:
        return sweep_field_directions(
            couplings=control_couplings,
            field_tesla=control_field,
            rate_per_second=control_rate,
            direction_count=REGISTERED_DIRECTION_COUNT,
            isotropic=isotropic_tensors,
            keep_samples=keep_samples,
            inventory=label,
        )

    # Control 1 - isotropic hyperfine tensors must remove the compass entirely.
    isotropic = registered_sweep(
        isotropic_tensors=True, label=f"{inventory}/isotropic-control"
    )

    # Control 2 - no hyperfine coupling at all: H commutes with P_S, so the pair
    # never leaves the singlet and the yield is exactly one in every direction.
    # Evaluated at two field magnitudes, because the registered condition claims
    # field-independence and one magnitude cannot establish that.
    bare_sweeps = tuple(
        registered_sweep(
            control_couplings=(),
            control_field=control_field,
            label="no-hyperfine-control",
        )
        for control_field in NO_HYPERFINE_CONTROL_FIELDS_T
    )
    bare = bare_sweeps[0]

    # Control 3 - recombination far faster than precession erases the compass.
    fast = registered_sweep(
        control_rate=FAST_RATE_PER_S,
        label=f"{inventory}/fast-recombination-control",
    )

    # Control 4 - the cost of loading the partner radical.  This compares two
    # fixed inventories rather than the one under test, so the comparison stays
    # meaningful whichever inventory the caller selected.
    spin_free = registered_sweep(
        control_couplings=resolve_inventory("spin-free-partner"),
        label="spin-free-partner",
    )
    loaded_partner = registered_sweep(
        control_couplings=resolve_inventory("cryptochrome-like"),
        label="cryptochrome-like",
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
    # Evaluated at the registered field and rate, not the caller's.  Both routes
    # are exact expressions, but their numerical agreement degrades with the
    # energy scale: the asymmetric residual is 1.4e-16 at 50 uT, 1.1e-10 at
    # 0.5 T and 2.0e-9 at 5 T, so a caller's field alone would fail a registered
    # gate on solve conditioning rather than on anything about the model.  The
    # field dependence of the agreement is asserted in the test suite with a
    # scale-aware tolerance instead, where it belongs.
    cross_check_projector = singlet_projector(hilbert_dims(cross_check_couplings))
    reference = build_hamiltonian(
        field_tesla=GEOMAGNETIC_FIELD_T,
        direction=(0.0, 0.0, 1.0),
        couplings=cross_check_couplings,
    )
    closed = singlet_yield_closed_form(reference, cross_check_projector, DEFAULT_RATE_PER_S)
    liouville = singlet_yield_liouvillian(
        reference, cross_check_projector, DEFAULT_RATE_PER_S, DEFAULT_RATE_PER_S
    )
    asymmetric = singlet_yield_liouvillian(
        reference, cross_check_projector, 2.0 * DEFAULT_RATE_PER_S, DEFAULT_RATE_PER_S
    )
    # Independent route to the same asymmetric quantity: eigendecomposition of
    # the Liouvillian rather than a direct solve. This is what validates the
    # asymmetric path, which has no closed form to compare against.
    asymmetric_independent = singlet_yield_liouvillian_eigen(
        reference, cross_check_projector, 2.0 * DEFAULT_RATE_PER_S, DEFAULT_RATE_PER_S
    )
    asymmetric_residual = abs(asymmetric - asymmetric_independent)
    cross_check_residual = abs(closed - liouville)

    # Exact limits: instantaneous recombination traps the pair in the singlet.
    # Closed form only, so this always runs on the selected inventory.
    # At the registered field for the same reason as the cross-check: the limit
    # is exact for any Hamiltonian, but how close PROMPT_RATE_PER_S gets to it
    # depends on the energy scale it is compared against (3.5e-12 short of unity
    # at 0.5 T against 5.6e-16 at 50 uT), so a fixed tolerance evaluated at the
    # caller's field would be a field-dependent gate.
    selected_reference = build_hamiltonian(
        field_tesla=GEOMAGNETIC_FIELD_T, direction=(0.0, 0.0, 1.0), couplings=couplings
    )
    prompt_limit = singlet_yield_closed_form(
        selected_reference, projector, PROMPT_RATE_PER_S
    )

    # The probe's recorded conclusion ("no probe point increases the anisotropy,
    # and the dependence is not monotonic") is a property of the registered
    # conditions, so it is computed there rather than at the caller's field and
    # rate.  At 0.5 T the same tensors give ratio_to_spin_free an order of
    # magnitude different, which would leave the note describing data the bundle
    # does not contain.
    partner_probe = probe_partner_suppression(
        field_tesla=GEOMAGNETIC_FIELD_T, rate_per_second=DEFAULT_RATE_PER_S
    )

    # Field and rate were pinned here already; the resolution was not, so the
    # smoke command decided this registered gate from 20 directions while the
    # hypothesis registers 200.  The residual is a sampled maximum, so the grid
    # size is part of the quantity: all three are registered conditions.
    residual = polarity_residual(
        couplings=couplings,
        field_tesla=GEOMAGNETIC_FIELD_T,
        rate_per_second=DEFAULT_RATE_PER_S,
        direction_count=REGISTERED_DIRECTION_COUNT,
    )

    if rate_points is None:
        rate_points = tuple(10.0**exponent for exponent in range(3, 11))
    # Every rate in the sweep, not just the primary one: an inf rate yields
    # inf/inf in the Lorentzian and serializes NaN into the bundle, and `passed`
    # does not inspect rate_sweep.
    rate_points = tuple(
        _require_positive_finite(f"rate_points[{index}]", rate, maximum=MAX_RATE_PER_S)
        for index, rate in enumerate(rate_points)
    )
    rate_sweep = tuple(
        RatePoint(
            rate_per_second=float(rate),
            anisotropy=point.anisotropy,
            mean_yield=point.mean_yield,
            direction_count=point.direction_count,
        )
        for rate, point in (
            (
                rate,
                sweep_field_directions(
                    couplings=couplings,
                    field_tesla=field_tesla,
                    rate_per_second=rate,
                    direction_count=direction_count,
                    keep_samples=False,
                    inventory=inventory,
                ),
            )
            for rate in rate_points
        )
    )

    # The registered condition is stated at the geomagnetic field, so it must be
    # evaluated there whatever field the caller asked for. Otherwise a run at, say,
    # 60 uT reports the geomagnetic condition true -- and `passed` certifies it --
    # without any 50 uT sweep having been computed. Reuse the primary sweep when
    # the caller is already at the registered field.
    # The condition is registered at BOTH a field and a rate, so both must be
    # honoured: a custom-rate run would otherwise decide it from the wrong rate.
    geomagnetic_reused = _at_registered_conditions(
        field_tesla, rate_per_second, direction_count
    )
    if geomagnetic_reused:
        geomagnetic = sweep
    else:
        # Samples kept: the antipodal condition below is decided from this
        # sweep's per-direction pairs, and it is registered at 200 directions.
        geomagnetic = registered_sweep(keep_samples=True)

    def antipodal_residual(target: DirectionSweep) -> float:
        """``max |Phi(B) - Phi(-B)|`` over a sweep's own recorded samples."""
        if not target.samples:
            return math.inf
        return max(
            abs(sample.singlet_yield - sample.antipodal_singlet_yield)
            for sample in target.samples
        )

    # The gate reads the registered sweep; the primary sweep's residual is
    # recorded beside it as caller-specific output. Gating on the primary sweep
    # would decide a registered condition from the caller's field, rate and
    # resolution -- a 12-direction run would certify it from 12 samples -- which
    # is the kill criterion this track already registers. The primary residual
    # is asserted in the test suite instead, where it runs on every commit.
    registered_antipodal_residual = antipodal_residual(geomagnetic)
    primary_antipodal_residual = antipodal_residual(sweep)

    # The low-rate comparison is computed here, from its own rate points, rather
    # than read out of `rate_sweep`.  A caller passing rate_points=(1e6,) would
    # otherwise leave this registered condition unevaluated while the report
    # still reported passed.
    # Both sides at the registered field and resolution: the inequality is
    # field-dependent, so a custom-field run would otherwise decide the
    # registered condition without ever evaluating it there.
    low_rate = registered_sweep(control_rate=LOW_RATE_PER_S)
    larmor_rate = registered_sweep(control_rate=LARMOR_COMPARABLE_RATE_PER_S)

    # Keys here MUST match hypotheses/radicalpair-0001.yaml validation.required
    # exactly.  test_every_declared_validation_is_implemented asserts set
    # equality in both directions, so the registry cannot claim a condition the
    # code never evaluates, and the code cannot gate on an unregistered one.
    checks = {
        "singlet_yield_anisotropy_positive_at_geomagnetic_field": geomagnetic.anisotropy > 1e-6,
        "isotropic_hyperfine_control_anisotropy_below_tolerance": (
            isotropic.anisotropy < SYMMETRY_TOLERANCE
        ),
        "polarity_residual_below_tolerance": residual < SYMMETRY_TOLERANCE,
        "no_hyperfine_control_yield_is_unity_and_field_independent": all(
            point.anisotropy < SYMMETRY_TOLERANCE
            and abs(point.mean_yield - 1.0) < SYMMETRY_TOLERANCE
            for point in bare_sweeps
        )
        and max(point.mean_yield for point in bare_sweeps)
        - min(point.mean_yield for point in bare_sweeps)
        < SYMMETRY_TOLERANCE,
        "fast_recombination_control_anisotropy_below_tolerance": fast.anisotropy < 1e-6,
        "spin_free_partner_anisotropy_exceeds_loaded_partner_anisotropy": (
            spin_free.anisotropy > loaded_partner.anisotropy
        ),
        "closed_form_and_liouvillian_yields_agree": cross_check_residual < 1e-9,
        "asymmetric_liouvillian_agrees_with_an_independent_solve": (
            asymmetric_residual < 1e-9
        ),
        "prompt_recombination_limit_equals_one": abs(prompt_limit - 1.0) < 1e-6,
        # At the registered field, not the caller's: field_tesla=0.5 would fail
        # this registered condition solely because a half-tesla Zeeman quantum
        # exceeds 1e-3 of k_B T -- a true statement about that run, but not the
        # condition the hypothesis registers, which is about the geomagnetic
        # field.  The caller's own ratio is recorded below either way.
        "zeeman_thermal_ratio_recorded": (
            0.0 < zeeman_thermal_ratio(GEOMAGNETIC_FIELD_T) < 1e-3
        ),
        "antipodal_yield_recorded_per_sampled_direction": (
            bool(geomagnetic.samples)
            and registered_antipodal_residual < SYMMETRY_TOLERANCE
        ),
        "anisotropy_at_low_rate_is_not_suppressed_relative_to_the_larmor_rate": (
            low_rate.anisotropy >= larmor_rate.anisotropy
        ),
    }

    controls: dict[str, Any] = {
        "checks": dict(checks),
        "symmetry_tolerance": SYMMETRY_TOLERANCE,
        "max_field_tesla": MAX_FIELD_TESLA,
        "max_rate_per_second": MAX_RATE_PER_S,
        "max_hyperfine_mhz": MAX_HYPERFINE_MHZ,
        "registered_direction_count": REGISTERED_DIRECTION_COUNT,
        "geomagnetic_field_microtesla": float(GEOMAGNETIC_FIELD_T * 1e6),
        "geomagnetic_direction_count": geomagnetic.direction_count,
        "low_rate_field_microtesla": float(GEOMAGNETIC_FIELD_T * 1e6),
        "low_rate_direction_count": low_rate.direction_count,
        "geomagnetic_anisotropy": geomagnetic.anisotropy,
        "registered_antipodal_residual": registered_antipodal_residual,
        "primary_antipodal_residual": primary_antipodal_residual,
        "geomagnetic_rate_per_second": float(DEFAULT_RATE_PER_S),
        "geomagnetic_sweep_reused_primary": geomagnetic_reused,
        "primary_direction_count": int(direction_count),
        "isotropic_hyperfine_anisotropy": isotropic.anisotropy,
        "isotropic_hyperfine_mean_yield": isotropic.mean_yield,
        "polarity_residual": residual,
        "polarity_direction_count": REGISTERED_DIRECTION_COUNT,
        "polarity_field_microtesla": float(GEOMAGNETIC_FIELD_T * 1e6),
        "polarity_rate_per_second": float(DEFAULT_RATE_PER_S),
        "no_hyperfine_anisotropy": bare.anisotropy,
        "no_hyperfine_mean_yield": bare.mean_yield,
        "no_hyperfine_control_fields_microtesla": [
            float(value * 1e6) for value in NO_HYPERFINE_CONTROL_FIELDS_T
        ],
        "no_hyperfine_mean_yield_per_field": [point.mean_yield for point in bare_sweeps],
        "no_hyperfine_field_spread": float(
            max(point.mean_yield for point in bare_sweeps)
            - min(point.mean_yield for point in bare_sweeps)
        ),
        "fast_recombination_rate_per_second": FAST_RATE_PER_S,
        "fast_recombination_anisotropy": fast.anisotropy,
        "partner_probe": [point.summary() for point in partner_probe],
        "partner_probe_directions": PARTNER_PROBE_DIRECTIONS,
        "partner_probe_field_microtesla": float(GEOMAGNETIC_FIELD_T * 1e6),
        "partner_probe_rate_per_second": float(DEFAULT_RATE_PER_S),
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
        "cross_check_field_microtesla": float(GEOMAGNETIC_FIELD_T * 1e6),
        "cross_check_rate_per_second": float(DEFAULT_RATE_PER_S),
        "cross_check_hilbert_dimension": int(np.prod(hilbert_dims(cross_check_couplings))),
        "liouvillian_dim_limit": LIOUVILLIAN_DIM_LIMIT,
        "asymmetric_rate_yield": asymmetric,
        "asymmetric_rate_yield_independent": asymmetric_independent,
        "asymmetric_solve_residual": asymmetric_residual,
        "asymmetric_gate_note": (
            "Validated against an independent eigendecomposition route, not against "
            "the symmetric closed form. Requiring the asymmetric yield to DIFFER "
            "from the symmetric one is false in general: with no hyperfine coupling "
            "both give unit yield."
        ),
        "prompt_recombination_limit": prompt_limit,
        "prompt_recombination_rate_per_second": float(PROMPT_RATE_PER_S),
        "prompt_recombination_field_microtesla": float(GEOMAGNETIC_FIELD_T * 1e6),
        "low_rate_per_second": LOW_RATE_PER_S,
        "low_rate_anisotropy": low_rate.anisotropy,
        "larmor_comparable_rate_per_second": LARMOR_COMPARABLE_RATE_PER_S,
        "larmor_comparable_anisotropy": larmor_rate.anisotropy,
        "zeeman_thermal_ratio_300k": zeeman_thermal_ratio(field_tesla),
        "zeeman_thermal_ratio_300k_at_geomagnetic_field": zeeman_thermal_ratio(
            GEOMAGNETIC_FIELD_T
        ),
        "zeeman_gate_field_microtesla": float(GEOMAGNETIC_FIELD_T * 1e6),
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
