"""Certified Eightfold-Way / Gell-Mann-Okubo finite benchmark.

The Eightfold Way classifies hadrons into SU(3)-flavor multiplets (the baryon
octet and decuplet) and turns the symmetry *breaking* into the Gell-Mann-Okubo
(GMO) mass relations.  Its mathematical content is an effective mass operator on
a multiplet,

    M = a * 1  +  b * Y  +  c * ( I(I+1) - Y^2 / 4 ),

i.e. an SU(3)-flavor singlet term plus a term transforming like the hypercharge
(``T_8``) component of an octet.  This module realises that operator as a
*certified interval matrix* and runs it through the rigorous residual-enclosure
eigensolver (``gaugegap.rigorous``), so the resulting multiplet structure and
mass relations are machine-checked finite-system bounds rather than
floating-point estimates.

Three certified pieces:

  (A) ``certified_octet_spectrum`` / ``certified_levels`` -- certified eigenvalue
      enclosures of the octet mass operator; certified count of *distinct* mass
      levels (disjoint enclosures) shows the symmetry breaking lifting the
      degeneracy.
  (B) ``certified_gmo_residual_model`` -- the GMO combination
      ``2(M_N + M_Xi) - 3 M_Lambda - M_Sigma`` evaluated in interval arithmetic
      on the operator's own levels; it is certified to enclose 0 (the relation is
      exact for an octet-transforming breaking term).
  (C) ``gmo_residual_from_masses`` and ``certified_omega_prediction`` -- certified
      enclosures from measured masses-with-uncertainties: the (small, nonzero)
      empirical GMO residual and the famous decuplet equal-spacing prediction of
      the Omega^- mass.

CLAIM BOUNDARY:
This is a finite-dimensional *effective* SU(3)-flavor mass-operator model -- the
Gell-Mann-Okubo phenomenology -- made rigorous with interval arithmetic.  It is
NOT a dynamical lattice-QCD computation: it does not derive hadron masses from a
gauge+matter path integral, and it makes no continuum or first-principles claim.
The certified statements are about the finite model operator and about linear
relations among input masses.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from gaugegap.rigorous.interval_arithmetic import (
    Interval,
    IntervalMatrix,
    verified_hermitian_eigenvalues,
)


@dataclass(frozen=True)
class FlavorState:
    """A flavor basis state with its SU(3) quantum numbers."""

    name: str
    multiplet: str  # isospin-multiplet label, e.g. "N", "Sigma", "Lambda", "Xi"
    iso: float      # total isospin I
    iso3: float     # third component I3
    hyper: float    # hypercharge Y = B + S


# Baryon octet (J^P = 1/2+), ordered by (Y desc, I3 desc).
OCTET: Tuple[FlavorState, ...] = (
    FlavorState("p", "N", 0.5, 0.5, 1.0),
    FlavorState("n", "N", 0.5, -0.5, 1.0),
    FlavorState("Sigma+", "Sigma", 1.0, 1.0, 0.0),
    FlavorState("Sigma0", "Sigma", 1.0, 0.0, 0.0),
    FlavorState("Sigma-", "Sigma", 1.0, -1.0, 0.0),
    FlavorState("Lambda", "Lambda", 0.0, 0.0, 0.0),
    FlavorState("Xi0", "Xi", 0.5, 0.5, -1.0),
    FlavorState("Xi-", "Xi", 0.5, -0.5, -1.0),
)

# Index of the Sigma0 and Lambda states (the only I3 = 0, Y = 0 pair; they mix
# under isospin breaking, giving a genuine off-diagonal 2x2 block).
_SIGMA0_IDX = 3
_LAMBDA_IDX = 5


@dataclass
class OctetModel:
    """Coefficients of the octet mass operator (in arbitrary mass units).

    M = a*1 + b*Y + c*(I(I+1) - Y^2/4) + iso_break*I3 + lam_sigma_mix*(Lambda<->Sigma0)
    """

    a: float = 1150.0          # SU(3) singlet mass
    b: float = -190.0          # hypercharge (octet) term
    c: float = 40.0            # isospin-Casimir (octet) term
    iso_break: float = 0.0     # I3 (electromagnetic/up-down) breaking
    lam_sigma_mix: float = 0.0  # Lambda-Sigma0 mixing strength

    def _diag(self, s: FlavorState) -> float:
        return (
            self.a
            + self.b * s.hyper
            + self.c * (s.iso * (s.iso + 1.0) - s.hyper * s.hyper / 4.0)
            + self.iso_break * s.iso3
        )

    def interval_matrix(self) -> IntervalMatrix:
        """Build the mass operator as a real-symmetric interval matrix."""
        n = len(OCTET)
        entries = [
            [Interval.from_float(0.0) for _ in range(n)] for _ in range(n)
        ]
        for i, s in enumerate(OCTET):
            entries[i][i] = Interval.from_float(self._diag(s))
        if self.lam_sigma_mix != 0.0:
            mix = Interval.from_float(self.lam_sigma_mix)
            entries[_SIGMA0_IDX][_LAMBDA_IDX] = mix
            entries[_LAMBDA_IDX][_SIGMA0_IDX] = mix
        return IntervalMatrix(entries)

    def level_intervals(self) -> Dict[str, Interval]:
        """Certified mass interval for each isospin multiplet (no I3/mixing).

        These are exact (zero-width) intervals built from the operator
        coefficients; used for the GMO relation, which is defined on the
        isospin-averaged multiplet masses.
        """
        reps = {s.multiplet: s for s in OCTET}
        return {name: Interval.from_float(self._diag(s)) for name, s in reps.items()}


def certified_octet_spectrum(model: OctetModel) -> List[Interval]:
    """Certified eigenvalue enclosures of the octet mass operator."""
    return verified_hermitian_eigenvalues(model.interval_matrix())


def certified_distinct_levels(enclosures: List[Interval]) -> List[List[Interval]]:
    """Group enclosures into certified-distinct clusters.

    Two enclosures that are disjoint correspond to *certifiably distinct*
    eigenvalues.  Sweeping the midpoint-sorted enclosures, we start a new cluster
    whenever the next enclosure is disjoint from the running cluster's upper
    edge.  The number of clusters is a rigorous lower bound on the number of
    distinct mass levels; cluster sizes are the multiplicities consistent with
    the enclosures (overlap means "not certified distinct", not "proven equal").
    """
    ordered = sorted(enclosures, key=lambda iv: iv.midpoint())
    clusters: List[List[Interval]] = []
    for iv in ordered:
        if clusters and not (iv.lower > clusters[-1][-1].upper):
            clusters[-1].append(iv)
        else:
            clusters.append([iv])
    return clusters


def certified_gmo_residual(
    m_N: Interval, m_Sigma: Interval, m_Lambda: Interval, m_Xi: Interval
) -> Interval:
    """Certified enclosure of the GMO residual ``2(N+Xi) - 3*Lambda - Sigma``.

    For the octet mass operator this is exactly 0; for measured masses it is the
    (small) certified GMO discrepancy.
    """
    two = Interval.from_float(2.0)
    three = Interval.from_float(3.0)
    return two * (m_N + m_Xi) - three * m_Lambda - m_Sigma


def certified_gmo_residual_model(model: OctetModel) -> Interval:
    """GMO residual evaluated on the model operator's own multiplet levels."""
    lv = model.level_intervals()
    return certified_gmo_residual(lv["N"], lv["Sigma"], lv["Lambda"], lv["Xi"])


# ---------------------------------------------------------------------------
# Empirical (data-driven) certified checks.
# ---------------------------------------------------------------------------

def _iv(value: float, error: float) -> Interval:
    return Interval.from_float(value, error)


def gmo_residual_from_masses(
    m_N: Tuple[float, float],
    m_Sigma: Tuple[float, float],
    m_Lambda: Tuple[float, float],
    m_Xi: Tuple[float, float],
) -> Interval:
    """Certified GMO residual from isospin-averaged masses ``(value, error)``."""
    return certified_gmo_residual(_iv(*m_N), _iv(*m_Sigma), _iv(*m_Lambda), _iv(*m_Xi))


def certified_omega_prediction(
    m_Sigma_star: Tuple[float, float], m_Xi_star: Tuple[float, float]
) -> Interval:
    """Certified decuplet equal-spacing prediction of the Omega^- mass.

    Equal spacing in hypercharge gives ``M_Omega = 2*M_Xi* - M_Sigma*`` from the
    two heavier known decuplet members.
    """
    two = Interval.from_float(2.0)
    return two * _iv(*m_Xi_star) - _iv(*m_Sigma_star)


# Particle Data Group isospin-averaged masses (MeV), with representative
# uncertainties; used by the empirical certified checks and the runner script.
PDG_OCTET: Dict[str, Tuple[float, float]] = {
    "N": (938.919, 0.001),
    "Sigma": (1193.153, 0.05),
    "Lambda": (1115.683, 0.006),
    "Xi": (1318.285, 0.05),
}
PDG_DECUPLET: Dict[str, Tuple[float, float]] = {
    "Delta": (1232.0, 1.0),
    "Sigma_star": (1383.7, 1.0),
    "Xi_star": (1531.8, 0.4),
    "Omega": (1672.45, 0.29),
}

# Individual charged-state masses (MeV, PDG), for isospin/EM mass-splitting
# relations such as Coleman-Glashow.
PDG_OCTET_STATES: Dict[str, Tuple[float, float]] = {
    "p": (938.272, 0.0003),
    "n": (939.565, 0.0005),
    "Sigma+": (1189.37, 0.07),
    "Sigma0": (1192.642, 0.024),
    "Sigma-": (1197.449, 0.030),
    "Lambda": (1115.683, 0.006),
    "Xi0": (1314.86, 0.20),
    "Xi-": (1321.71, 0.07),
}

# Pseudoscalar meson nonet (MeV). Meson GMO is quadratic in the mass.
PDG_PSEUDOSCALAR: Dict[str, Tuple[float, float]] = {
    "pi+": (139.570, 0.0002),
    "pi0": (134.977, 0.0005),
    "K+": (493.677, 0.016),
    "K0": (497.611, 0.013),
    "eta": (547.862, 0.017),
    "eta_prime": (957.78, 0.06),
}

# Vector meson nonet (MeV).
PDG_VECTOR: Dict[str, Tuple[float, float]] = {
    "rho": (775.26, 0.23),
    "K_star": (891.67, 0.26),
    "omega": (782.66, 0.13),
    "phi": (1019.461, 0.016),
}


# ===========================================================================
# Certified relations battery: each standard SU(3)-flavor mass relation as a
# certified residual interval propagated from the input masses-with-errors.
# ===========================================================================

@dataclass
class RelationResult:
    """Outcome of one certified SU(3) mass relation."""

    name: str
    residual: Interval     # certified enclosure of the relation's residual
    scale: float           # characteristic scale (for a relative size)
    note: str = ""

    @property
    def encloses_zero(self) -> bool:
        return bool(self.residual.lower <= 0 <= self.residual.upper)

    @property
    def rel_percent(self) -> float:
        if self.scale == 0:
            return float("nan")
        return 100.0 * abs(float(self.residual.midpoint())) / self.scale


def _sq(mass: Tuple[float, float]) -> Interval:
    """Certified square of a mass-with-error interval."""
    m = _iv(*mass)
    return m * m


def certified_decuplet_spacings(
    delta=PDG_DECUPLET["Delta"],
    sigma_star=PDG_DECUPLET["Sigma_star"],
    xi_star=PDG_DECUPLET["Xi_star"],
    omega=PDG_DECUPLET["Omega"],
) -> List[RelationResult]:
    """Certified decuplet equal-spacing residuals (two independent relations).

    Equal spacing in hypercharge: (Sigma*-Delta) = (Xi*-Sigma*) = (Omega-Xi*).
    """
    d, s, x, o = _iv(*delta), _iv(*sigma_star), _iv(*xi_star), _iv(*omega)
    g1, g2, g3 = s - d, x - s, o - x
    scale = float((s - d).midpoint())
    return [
        RelationResult("decuplet spacing (Xi*-Sigma*)-(Sigma*-Delta)", g2 - g1, scale),
        RelationResult("decuplet spacing (Omega-Xi*)-(Xi*-Sigma*)", g3 - g2, scale),
    ]


def certified_meson_gmo(
    pi=PDG_PSEUDOSCALAR["pi+"],
    kaon=PDG_PSEUDOSCALAR["K+"],
    eta=PDG_PSEUDOSCALAR["eta"],
) -> RelationResult:
    """Certified pseudoscalar GMO residual 4*m_K^2 - 3*m_eta^2 - m_pi^2.

    Quadratic in the mass (mesons). The residual is sizeable (~6%) because the
    physical eta mixes with the singlet eta'; see ``certified_eta_mixing``.
    """
    four = Interval.from_float(4.0)
    three = Interval.from_float(3.0)
    residual = four * _sq(kaon) - three * _sq(eta) - _sq(pi)
    scale = float((four * _sq(kaon)).midpoint())
    return RelationResult(
        "pseudoscalar GMO 4K^2-3eta^2-pi^2", residual, scale,
        note="quadratic; nonzero from eta-eta' mixing",
    )


def certified_coleman_glashow(states: Dict[str, Tuple[float, float]] = None) -> RelationResult:
    """Certified Coleman-Glashow relation among octet EM mass splittings.

    (M_n - M_p) + (M_Xi- - M_Xi0) - (M_Sigma- - M_Sigma+) = 0.
    """
    st = states or PDG_OCTET_STATES
    n, p = _iv(*st["n"]), _iv(*st["p"])
    xim, xi0 = _iv(*st["Xi-"]), _iv(*st["Xi0"])
    sm, sp = _iv(*st["Sigma-"]), _iv(*st["Sigma+"])
    residual = (n - p) + (xim - xi0) - (sm - sp)
    scale = float((sm - sp).midpoint())
    return RelationResult(
        "Coleman-Glashow (n-p)+(Xi--Xi0)-(Sigma--Sigma+)", residual, scale,
        note="electromagnetic mass splittings",
    )


def certified_constituent_quark_masses(
    delta=PDG_DECUPLET["Delta"], omega=PDG_DECUPLET["Omega"]
) -> Dict[str, Interval]:
    """Certified constituent quark masses from the decuplet (additive model).

    In the decuplet, Delta = qqq and Omega = sss, so m_q = M_Delta/3 and
    m_s = M_Omega/3; the strange-light splitting m_s - m_q drives the equal
    spacing.
    """
    three = Interval.from_float(3.0)
    m_q = _iv(*delta) / three
    m_s = _iv(*omega) / three
    return {"m_q": m_q, "m_s": m_s, "m_s_minus_m_q": m_s - m_q}


def certified_eta_mixing(
    pi=PDG_PSEUDOSCALAR["pi+"],
    kaon=PDG_PSEUDOSCALAR["K+"],
    eta=PDG_PSEUDOSCALAR["eta"],
    eta_prime=PDG_PSEUDOSCALAR["eta_prime"],
) -> Dict[str, Interval]:
    """Certified eta-eta' mixing parameters from a 2x2 mass-squared system.

    The octet member mass-squared is fixed by GMO, m8^2 = (4 m_K^2 - m_pi^2)/3.
    The physical eta, eta' diagonalize a 2x2 [[m8^2, t],[t, m1^2]] system, so
    from trace/determinant:
        m1^2 = (m_eta^2 + m_eta'^2) - m8^2
        t^2  = m8^2 * m1^2 - m_eta^2 * m_eta'^2
    Both returned as certified intervals (t^2 >= 0 is the consistency check).
    """
    four = Interval.from_float(4.0)
    three = Interval.from_float(3.0)
    m8_sq = (four * _sq(kaon) - _sq(pi)) / three
    eta_sq, etap_sq = _sq(eta), _sq(eta_prime)
    m1_sq = (eta_sq + etap_sq) - m8_sq
    t_sq = m8_sq * m1_sq - eta_sq * etap_sq
    return {"m8_sq": m8_sq, "m1_sq": m1_sq, "t_sq": t_sq}


def certified_relations_battery() -> List[RelationResult]:
    """Run the full battery of certified SU(3)-flavor mass relations."""
    results: List[RelationResult] = []
    # Octet GMO (linear).
    r_oct = gmo_residual_from_masses(
        PDG_OCTET["N"], PDG_OCTET["Sigma"], PDG_OCTET["Lambda"], PDG_OCTET["Xi"]
    )
    scale_oct = 3 * PDG_OCTET["Lambda"][0] + PDG_OCTET["Sigma"][0]
    results.append(RelationResult("baryon octet GMO 2(N+Xi)-3Lambda-Sigma", r_oct, scale_oct))
    # Decuplet equal spacing (two relations).
    results.extend(certified_decuplet_spacings())
    # Pseudoscalar meson GMO (quadratic).
    results.append(certified_meson_gmo())
    # Coleman-Glashow EM relation.
    results.append(certified_coleman_glashow())
    return results


# ===========================================================================
# Weight diagrams (I3, Y) -- the geometric patterns of the Eightfold Way.
# ===========================================================================

# (name, I3, Y) for the decuplet, completing the data already in OCTET.
DECUPLET_WEIGHTS: Tuple[Tuple[str, float, float], ...] = (
    ("Delta-", -1.5, 1.0), ("Delta0", -0.5, 1.0), ("Delta+", 0.5, 1.0), ("Delta++", 1.5, 1.0),
    ("Sigma*-", -1.0, 0.0), ("Sigma*0", 0.0, 0.0), ("Sigma*+", 1.0, 0.0),
    ("Xi*-", -0.5, -1.0), ("Xi*0", 0.5, -1.0),
    ("Omega-", 0.0, -2.0),
)


def _weight_diagram_svg(points, title: str, width: int = 460, height: int = 420) -> str:
    """Render (I3, Y) weight points as a standalone SVG string."""
    cx, cy, scale = width / 2, height / 2 + 20, 95.0
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="sans-serif">',
        f'<rect width="{width}" height="{height}" fill="white"/>',
        f'<text x="{width/2}" y="28" text-anchor="middle" font-size="18" '
        f'font-weight="bold">{title}</text>',
    ]
    # Axes.
    parts.append(
        f'<line x1="40" y1="{cy}" x2="{width-40}" y2="{cy}" stroke="#bbb"/>'
        f'<line x1="{cx}" y1="60" x2="{cx}" y2="{height-30}" stroke="#bbb"/>'
        f'<text x="{width-30}" y="{cy-8}" font-size="13" fill="#888">I&#8323;</text>'
        f'<text x="{cx+8}" y="72" font-size="13" fill="#888">Y</text>'
    )
    for name, i3, y in points:
        px, py = cx + i3 * scale, cy - y * scale
        parts.append(
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="16" fill="#eef3ff" stroke="#2a4d9b"/>'
            f'<text x="{px:.1f}" y="{py+4:.1f}" text-anchor="middle" font-size="10">{name}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def octet_weight_diagram_svg() -> str:
    pts = [(s.name, s.iso3, s.hyper) for s in OCTET]
    return _weight_diagram_svg(pts, "Baryon octet (J=1/2)")


def decuplet_weight_diagram_svg() -> str:
    return _weight_diagram_svg(list(DECUPLET_WEIGHTS), "Baryon decuplet (J=3/2)")


# ===========================================================================
# Vector-meson nonet and omega-phi mixing.
# ===========================================================================

def certified_vector_quark_content(
    rho=PDG_VECTOR["rho"],
    k_star=PDG_VECTOR["K_star"],
    omega=PDG_VECTOR["omega"],
    phi=PDG_VECTOR["phi"],
) -> List[RelationResult]:
    """Certified ideal-mixing tests for the vector-meson nonet.

    Vector mesons mix almost ideally: phi is nearly pure s-sbar and omega nearly
    pure light-quark. The additive constituent picture then predicts (linearly)
    phi = 2*K* - rho (s-sbar from strange counting) and omega = rho. Each is
    returned as a certified residual against the measured mass.
    """
    r, ks, w, p = _iv(*rho), _iv(*k_star), _iv(*omega), _iv(*phi)
    two = Interval.from_float(2.0)
    phi_pred = two * ks - r
    return [
        RelationResult("vector phi as s-sbar: (2K*-rho)-phi", phi_pred - p,
                       float(p.midpoint()), note="ideal mixing"),
        RelationResult("vector omega as n-nbar: rho-omega", r - w,
                       float(w.midpoint()), note="ideal mixing"),
    ]


def certified_vector_mixing(
    rho=PDG_VECTOR["rho"],
    k_star=PDG_VECTOR["K_star"],
    omega=PDG_VECTOR["omega"],
    phi=PDG_VECTOR["phi"],
) -> Dict[str, Interval]:
    """Certified octet-singlet mixing parameters for the vector nonet.

    Octet member fixed by the (quadratic) vector GMO m8^2 = (4 K*^2 - rho^2)/3;
    physical omega, phi diagonalize [[m8^2, t],[t, m1^2]], so by trace/det
    m1^2 = omega^2 + phi^2 - m8^2 and t^2 = m8^2 m1^2 - omega^2 phi^2.
    """
    four = Interval.from_float(4.0)
    three = Interval.from_float(3.0)
    m8_sq = (four * _sq(k_star) - _sq(rho)) / three
    w_sq, p_sq = _sq(omega), _sq(phi)
    m1_sq = (w_sq + p_sq) - m8_sq
    t_sq = m8_sq * m1_sq - w_sq * p_sq
    return {"m8_sq": m8_sq, "m1_sq": m1_sq, "t_sq": t_sq}


# ===========================================================================
# Baryon magnetic moments (quark model / SU(6)), in nuclear magnetons.
# ===========================================================================

# Measured octet magnetic moments (nuclear magnetons), PDG.
MOMENTS: Dict[str, Tuple[float, float]] = {
    "p": (2.792847, 0.000001),
    "n": (-1.913043, 0.000005),
    "Lambda": (-0.613, 0.004),
    "Sigma+": (2.458, 0.010),
    "Sigma-": (-1.160, 0.025),
    "Xi0": (-1.250, 0.014),
    "Xi-": (-0.6507, 0.0025),
}


def certified_quark_moments(
    p=MOMENTS["p"], n=MOMENTS["n"], lam=MOMENTS["Lambda"]
) -> Dict[str, Interval]:
    """Certified constituent-quark magnetic moments from p, n, Lambda.

    Inverting the SU(6) relations mu_p=(4 mu_u-mu_d)/3, mu_n=(4 mu_d-mu_u)/3:
        mu_u = (4 mu_p + mu_n)/5,  mu_d = (mu_p + 4 mu_n)/5,  mu_s = mu_Lambda.
    """
    mp_p, mp_n = _iv(*p), _iv(*n)
    four, five = Interval.from_float(4.0), Interval.from_float(5.0)
    mu_u = (four * mp_p + mp_n) / five
    mu_d = (mp_p + four * mp_n) / five
    mu_s = _iv(*lam)
    return {"mu_u": mu_u, "mu_d": mu_d, "mu_s": mu_s}


def certified_moment_predictions() -> List[RelationResult]:
    """Certified quark-model predictions for the remaining octet moments.

    Quark moments are fixed by (p, n, Lambda); the other moments are then
    parameter-free predictions, each reported as a certified residual
    (predicted - measured) in nuclear magnetons.
    """
    q = certified_quark_moments()
    mu_u, mu_d, mu_s = q["mu_u"], q["mu_d"], q["mu_s"]
    three = Interval.from_float(3.0)
    four = Interval.from_float(4.0)
    preds = {
        "Sigma+": (four * mu_u - mu_s) / three,
        "Sigma-": (four * mu_d - mu_s) / three,
        "Xi0": (four * mu_s - mu_u) / three,
        "Xi-": (four * mu_s - mu_d) / three,
    }
    out: List[RelationResult] = []
    for name, pred in preds.items():
        meas = _iv(*MOMENTS[name])
        out.append(RelationResult(
            f"moment {name} (pred-meas)", pred - meas, abs(MOMENTS[name][0]),
            note="SU(6) quark model",
        ))
    return out


def certified_moment_relations() -> List[RelationResult]:
    """Parameter-free SU(6) magnetic-moment relations as certified residuals."""
    mp_p, mp_n = _iv(*MOMENTS["p"]), _iv(*MOMENTS["n"])
    half = Interval.from_float(0.5)
    three_half = Interval.from_float(1.5)
    # mu_p / mu_n = -3/2 exactly in the model (independent of mu_s).
    ratio = mp_p / mp_n
    r_ratio = RelationResult("moment ratio mu_p/mu_n vs -3/2", ratio + three_half, 1.5)
    # mu_Sigma0 = 1/2 (mu_Sigma+ + mu_Sigma-) exactly in the model (Sigma0 moment
    # is not directly measured; this is a certified prediction).
    sig0_pred = half * (_iv(*MOMENTS["Sigma+"]) + _iv(*MOMENTS["Sigma-"]))
    r_sig0 = RelationResult("predicted mu_Sigma0 = (mu_Sigma+ + mu_Sigma-)/2",
                            sig0_pred, abs(float(sig0_pred.midpoint())) or 1.0,
                            note="not directly measured")
    return [r_ratio, r_sig0]


# ===========================================================================
# Isospin / SU(3) decay-ratio (Clebsch-Gordan) predictions -- exact rationals.
# ===========================================================================

def certified_isospin_ratios() -> List[Tuple[str, Interval, str]]:
    """Parameter-free isospin branching ratios from squared Clebsch-Gordans.

    These are exact rationals; in interval arithmetic they are zero-width
    certified values. They are algebraic predictions of isospin symmetry, not
    fits to data.
    """
    def ratio(num: float, den: float) -> Interval:
        return Interval.from_float(num) / Interval.from_float(den)

    return [
        ("Delta+ -> p pi0 : n pi+", ratio(2, 1), "2:1"),
        ("Delta0 -> n pi0 : p pi-", ratio(2, 1), "2:1"),
        ("K*+ -> K0 pi+ : K+ pi0", ratio(2, 1), "2:1"),
        ("Delta++ -> p pi+ (pure)", ratio(1, 1), "1"),
    ]


# ===========================================================================
# Gell-Mann-Nishijima relation Q = I3 + Y/2 -- exact structural backbone.
# ===========================================================================

# (name, charge, I3, Y) for octet + decuplet members.
_GMN_STATES: Tuple[Tuple[str, float, float, float], ...] = (
    # baryon octet
    ("p", 1, 0.5, 1), ("n", 0, -0.5, 1),
    ("Sigma+", 1, 1, 0), ("Sigma0", 0, 0, 0), ("Sigma-", -1, -1, 0),
    ("Lambda", 0, 0, 0), ("Xi0", 0, 0.5, -1), ("Xi-", -1, -0.5, -1),
    # baryon decuplet
    ("Delta++", 2, 1.5, 1), ("Delta+", 1, 0.5, 1), ("Delta0", 0, -0.5, 1),
    ("Delta-", -1, -1.5, 1), ("Sigma*+", 1, 1, 0), ("Sigma*-", -1, -1, 0),
    ("Xi*0", 0, 0.5, -1), ("Xi*-", -1, -0.5, -1), ("Omega-", -1, 0, -2),
)


def certified_gell_mann_nishijima() -> RelationResult:
    """Certified Gell-Mann-Nishijima check Q - (I3 + Y/2) = 0 over all states.

    Evaluated in interval arithmetic across the full octet and decuplet; the
    returned residual is the worst-case enclosure (exactly [0, 0]).
    """
    half = Interval.from_float(0.5)
    worst = Interval.from_float(0.0)
    for _name, q, i3, y in _GMN_STATES:
        resid = _iv(q, 0.0) - (_iv(i3, 0.0) + half * _iv(y, 0.0))
        if abs(float(resid.upper)) > abs(float(worst.upper)) or abs(
            float(resid.lower)
        ) > abs(float(worst.lower)):
            worst = resid
    return RelationResult(
        f"Gell-Mann-Nishijima Q-(I3+Y/2) over {len(_GMN_STATES)} states",
        worst, 1.0, note="exact structural relation",
    )


def certified_sigma_lambda_transition() -> RelationResult:
    """Certified Sigma0->Lambda transition magnetic moment (quark model).

    The SU(6) prediction is |mu(Sigma0->Lambda)| = (mu_u - mu_d)/sqrt(3);
    compared against the measured |mu| = 1.61 +/- 0.08 nuclear magnetons.
    """
    q = certified_quark_moments()
    sqrt3 = Interval.from_float(3.0).sqrt()
    pred = (q["mu_u"] - q["mu_d"]) / sqrt3
    measured = _iv(1.61, 0.08)
    return RelationResult(
        "Sigma0->Lambda transition moment (pred-meas)", pred - measured,
        1.61, note="SU(6) quark model",
    )


# ===========================================================================
# SU(3) representation theory: irrep dimensions and tensor decompositions.
# ===========================================================================

def su3_dim(p: int, q: int) -> int:
    """Dimension of the SU(3) irrep (p, q): (p+1)(q+1)(p+q+2)/2."""
    return (p + 1) * (q + 1) * (p + q + 2) // 2


# Standard SU(3) tensor-product decompositions, as (label, left dim, right dim,
# [(p, q) summands]).
_SU3_DECOMPOSITIONS = (
    ("3 (x) 3bar = 1 + 8", 3, 3, [(0, 0), (1, 1)]),
    ("3 (x) 3 = 3bar + 6", 3, 3, [(0, 1), (2, 0)]),
    ("3 (x) 3 (x) 3 = 1 + 8 + 8 + 10", 3, 9, [(0, 0), (1, 1), (1, 1), (3, 0)]),
    ("8 (x) 8 = 1+8+8+10+10bar+27", 8, 8,
     [(0, 0), (1, 1), (1, 1), (3, 0), (0, 3), (2, 2)]),
)


def certified_su3_decompositions() -> List[RelationResult]:
    """Certified SU(3) tensor decompositions: product dim == sum of summand dims.

    Each residual is computed in interval arithmetic and is exactly [0, 0]; the
    decompositions are exact representation-theory identities (baryons live in
    3(x)3(x)3, mesons in 3(x)3bar).
    """
    out: List[RelationResult] = []
    for label, left, right, summands in _SU3_DECOMPOSITIONS:
        product = Interval.from_float(float(left)) * Interval.from_float(float(right))
        total = Interval.from_float(0.0)
        for p, q in summands:
            total = total + Interval.from_float(float(su3_dim(p, q)))
        out.append(RelationResult(label, product - total, float(left * right),
                                  note="exact rep-theory identity"))
    return out


# ===========================================================================
# Weak (Cabibbo) sector: CKM first-row unitarity and the Cabibbo angle.
# ===========================================================================

CKM_FIRST_ROW: Dict[str, Tuple[float, float]] = {
    "V_ud": (0.97373, 0.00031),
    "V_us": (0.2243, 0.0008),
    "V_ub": (0.00382, 0.00020),
}


def certified_ckm_unitarity(row: Dict[str, Tuple[float, float]] = None) -> RelationResult:
    """Certified CKM first-row unitarity residual |Vud|^2+|Vus|^2+|Vub|^2 - 1.

    A certified interval around the (small, topical) first-row unitarity test;
    this is arithmetic on PDG inputs, not a discovery claim.
    """
    r = row or CKM_FIRST_ROW
    total = _sq(r["V_ud"]) + _sq(r["V_us"]) + _sq(r["V_ub"])
    residual = total - Interval.from_float(1.0)
    return RelationResult(
        "CKM first-row unitarity |Vud|^2+|Vus|^2+|Vub|^2-1", residual, 1.0,
        note="PDG inputs",
    )


def certified_cabibbo_angle(row: Dict[str, Tuple[float, float]] = None) -> Interval:
    """Certified Cabibbo angle (degrees) from theta_C = atan(|V_us|/|V_ud|).

    atan is monotonic, so applying it to the endpoints of the |V_us|/|V_ud|
    enclosure yields a certified angle enclosure.
    """
    import mpmath as mp

    r = row or CKM_FIRST_ROW
    ratio = _iv(*r["V_us"]) / _iv(*r["V_ud"])
    deg = mp.mpf(180) / mp.pi
    return Interval(mp.atan(ratio.lower) * deg, mp.atan(ratio.upper) * deg)


# Representative axial-coupling fit (PDG / SU(3) hyperon semileptonic fit).
AXIAL: Dict[str, Tuple[float, float]] = {
    "g_A": (1.2754, 0.0013),
    "F": (0.463, 0.008),
    "D": (0.804, 0.008),
}


def certified_axial_fd() -> RelationResult:
    """Certified nucleon axial-coupling consistency g_A = F + D.

    F, D are the SU(3) axial reduced couplings; the neutron-beta-decay g_A
    should equal their sum. Reported as a certified residual (F+D) - g_A.
    """
    residual = (_iv(*AXIAL["F"]) + _iv(*AXIAL["D"])) - _iv(*AXIAL["g_A"])
    return RelationResult("axial coupling (F+D) - g_A", residual,
                          AXIAL["g_A"][0], note="SU(3) hyperon fit")
