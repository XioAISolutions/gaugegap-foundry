"""Exact rational Standard Model gauge-anomaly checks."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

CLAIM_BOUNDARY = (
    "Exact coefficients for a declared finite chiral field inventory only; "
    "no continuum construction or Millennium Prize claim."
)


def f(value: Fraction | int | str) -> Fraction:
    return value if isinstance(value, Fraction) else Fraction(value)


def q(value: Fraction) -> str:
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


@dataclass(frozen=True)
class Hypercharges:
    colors: int = 3
    generations: int = 3
    y_q: Fraction = Fraction(1, 6)
    y_u: Fraction = Fraction(2, 3)
    y_d: Fraction = Fraction(-1, 3)
    y_l: Fraction = Fraction(-1, 2)
    y_e: Fraction = Fraction(-1)
    y_nu: Fraction | None = None
    y_h: Fraction = Fraction(1, 2)

    def __post_init__(self) -> None:
        if self.colors < 1 or self.generations < 1:
            raise ValueError("colors and generations must be positive")
        for name in ("y_q", "y_u", "y_d", "y_l", "y_e", "y_h"):
            object.__setattr__(self, name, f(getattr(self, name)))
        if self.y_nu is not None:
            object.__setattr__(self, "y_nu", f(self.y_nu))

    def summary(self) -> dict[str, object]:
        charges = {
            "u": self.y_q + Fraction(1, 2),
            "d": self.y_q - Fraction(1, 2),
            "electron": self.y_l - Fraction(1, 2),
            "neutrino": self.y_l + Fraction(1, 2),
        }
        return {
            "colors": self.colors,
            "generations": self.generations,
            "hypercharges": {
                "Q_L": q(self.y_q), "u_R": q(self.y_u), "d_R": q(self.y_d),
                "L_L": q(self.y_l), "e_R": q(self.y_e),
                "nu_R": None if self.y_nu is None else q(self.y_nu), "H": q(self.y_h),
            },
            "electric_charges": {name: q(value) for name, value in charges.items()},
        }


@dataclass(frozen=True)
class Anomalies:
    su3_u1: Fraction
    su2_u1: Fraction
    u1_cubed: Fraction
    gravity_u1: Fraction
    weak_doublets: int

    @property
    def local_pass(self) -> bool:
        return self.su3_u1 == self.su2_u1 == self.u1_cubed == self.gravity_u1 == 0

    @property
    def global_su2_pass(self) -> bool:
        return self.weak_doublets % 2 == 0

    @property
    def passes(self) -> bool:
        return self.local_pass and self.global_su2_pass

    def summary(self) -> dict[str, object]:
        exact = {
            "SU(3)^2-U(1)": q(self.su3_u1),
            "SU(2)^2-U(1)": q(self.su2_u1),
            "U(1)^3": q(self.u1_cubed),
            "gravity^2-U(1)": q(self.gravity_u1),
        }
        return {
            "exact": exact,
            "numeric": {
                "SU(3)^2-U(1)": float(self.su3_u1),
                "SU(2)^2-U(1)": float(self.su2_u1),
                "U(1)^3": float(self.u1_cubed),
                "gravity^2-U(1)": float(self.gravity_u1),
            },
            "weak_doublets": self.weak_doublets,
            "global_su2_pass": self.global_su2_pass,
            "local_pass": self.local_pass,
            "passes": self.passes,
        }


def audit(h: Hypercharges) -> Anomalies:
    n, g = h.colors, h.generations
    yn = h.y_nu if h.y_nu is not None else Fraction(0)
    has_nu = h.y_nu is not None
    return Anomalies(
        g * (2 * h.y_q - h.y_u - h.y_d),
        g * (n * h.y_q + h.y_l),
        g * (2*n*h.y_q**3 - n*h.y_u**3 - n*h.y_d**3 + 2*h.y_l**3 - h.y_e**3 - (yn**3 if has_nu else 0)),
        g * (2*n*h.y_q - n*h.y_u - n*h.y_d + 2*h.y_l - h.y_e - (yn if has_nu else 0)),
        g * (n + 1),
    )


def proton_charge(h: Hypercharges) -> Fraction:
    return 3 * h.y_q + Fraction(1, 2)


def neutron_charge(h: Hypercharges) -> Fraction:
    return 3 * h.y_q - Fraction(1, 2)


def payload(h: Hypercharges) -> dict[str, object]:
    return {
        "assignment": h.summary(),
        "anomalies": audit(h).summary(),
        "composites": {"proton": q(proton_charge(h)), "neutron": q(neutron_charge(h))},
        "claim_boundary": CLAIM_BOUNDARY,
    }
