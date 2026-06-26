"""Canonical, finite Standard Model field and interaction catalog.

This module is a structural reference for visualization and deterministic audits.  It
uses the compact renormalizable Standard Model sector decomposition as its source of
truth.  It does not treat artistic blackboard transcriptions as authoritative, evaluate
a path integral, or claim a nonperturbative continuum construction.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Mapping

import numpy as np


CLAIM_BOUNDARY = (
    "canonical sector decomposition, field inventory, tree-level relations, and finite "
    "interaction graph only; no scattering prediction, loop calculation, path-integral "
    "evaluation, nonperturbative construction, or Millennium Prize claim"
)
SOURCE_NOTE = (
    "The visual scene may be inspired by dense expanded-Lagrangian blackboards, but the "
    "catalog below is generated from a canonical compact Standard Model specification."
)


@dataclass(frozen=True)
class FieldSpec:
    field_id: str
    label: str
    kind: str
    spin: float
    mass_dimension: float
    charge_thirds: int
    color_representation: str
    weak_representation: str
    hypercharge: str
    multiplicity: int = 1
    notes: str = ""

    @property
    def electric_charge(self) -> float:
        return self.charge_thirds / 3.0

    def summary(self) -> dict[str, object]:
        payload = asdict(self)
        payload["electric_charge"] = self.electric_charge
        return payload


@dataclass(frozen=True)
class SectorSpec:
    sector_id: str
    label: str
    compact_term: str
    operator_dimension: int
    gauge_basis: str
    notes: str = ""

    def summary(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class InteractionSpec:
    interaction_id: str
    label: str
    sector_id: str
    fields: tuple[str, ...]
    coupling: str
    operator_dimension: int
    parent_term: str
    hermitian_partner: str | None = None
    notes: str = ""

    def summary(self) -> dict[str, object]:
        payload = asdict(self)
        payload["fields"] = list(self.fields)
        return payload


@dataclass(frozen=True)
class StandardModelCatalog:
    gauge_group: tuple[str, ...]
    sectors: tuple[SectorSpec, ...]
    fields: tuple[FieldSpec, ...]
    interactions: tuple[InteractionSpec, ...]
    default_parameters: Mapping[str, float]
    control_ranges: Mapping[str, tuple[float, float, float]]
    gauge_convention: str
    claim_boundary: str = CLAIM_BOUNDARY
    source_note: str = SOURCE_NOTE

    def field_map(self) -> dict[str, FieldSpec]:
        return {field.field_id: field for field in self.fields}

    def sector_map(self) -> dict[str, SectorSpec]:
        return {sector.sector_id: sector for sector in self.sectors}

    def interaction_map(self) -> dict[str, InteractionSpec]:
        return {interaction.interaction_id: interaction for interaction in self.interactions}

    def summary(self) -> dict[str, object]:
        return {
            "gauge_group": list(self.gauge_group),
            "gauge_convention": self.gauge_convention,
            "sectors": [sector.summary() for sector in self.sectors],
            "fields": [field.summary() for field in self.fields],
            "interactions": [interaction.summary() for interaction in self.interactions],
            "default_parameters": dict(self.default_parameters),
            "control_ranges": {
                key: list(value) for key, value in self.control_ranges.items()
            },
            "claim_boundary": self.claim_boundary,
            "source_note": self.source_note,
        }


def _fields() -> tuple[FieldSpec, ...]:
    return (
        FieldSpec("gluon", "g", "gauge", 1.0, 1.0, 0, "adjoint 8", "singlet", "0", 8),
        FieldSpec("photon", "γ", "gauge", 1.0, 1.0, 0, "singlet", "mixed neutral", "0"),
        FieldSpec("z_boson", "Z", "gauge", 1.0, 1.0, 0, "singlet", "mixed neutral", "0"),
        FieldSpec("w_plus", "W⁺", "gauge", 1.0, 1.0, 3, "singlet", "charged adjoint", "+1"),
        FieldSpec("w_minus", "W⁻", "gauge", 1.0, 1.0, -3, "singlet", "charged adjoint", "-1"),
        FieldSpec("higgs", "H", "scalar", 0.0, 1.0, 0, "singlet", "doublet remnant", "0"),
        FieldSpec("goldstone_plus", "φ⁺", "scalar", 0.0, 1.0, 3, "singlet", "doublet", "+1"),
        FieldSpec("goldstone_minus", "φ⁻", "scalar", 0.0, 1.0, -3, "singlet", "doublet", "-1"),
        FieldSpec("goldstone_zero", "φ⁰", "scalar", 0.0, 1.0, 0, "singlet", "doublet", "0"),
        FieldSpec("up", "u", "fermion", 0.5, 1.5, 2, "fundamental 3", "doublet/singlet", "+1/6,+2/3"),
        FieldSpec("anti_up", "ū", "fermion", 0.5, 1.5, -2, "anti-fundamental 3̄", "conjugate", "opposite"),
        FieldSpec("down", "d", "fermion", 0.5, 1.5, -1, "fundamental 3", "doublet/singlet", "+1/6,-1/3"),
        FieldSpec("anti_down", "d̄", "fermion", 0.5, 1.5, 1, "anti-fundamental 3̄", "conjugate", "opposite"),
        FieldSpec("top", "t", "fermion", 0.5, 1.5, 2, "fundamental 3", "doublet/singlet", "+1/6,+2/3"),
        FieldSpec("anti_top", "t̄", "fermion", 0.5, 1.5, -2, "anti-fundamental 3̄", "conjugate", "opposite"),
        FieldSpec("bottom", "b", "fermion", 0.5, 1.5, -1, "fundamental 3", "doublet/singlet", "+1/6,-1/3"),
        FieldSpec("anti_bottom", "b̄", "fermion", 0.5, 1.5, 1, "anti-fundamental 3̄", "conjugate", "opposite"),
        FieldSpec("charged_lepton", "ℓ⁻", "fermion", 0.5, 1.5, -3, "singlet", "doublet/singlet", "-1/2,-1"),
        FieldSpec("anti_charged_lepton", "ℓ⁺", "fermion", 0.5, 1.5, 3, "singlet", "conjugate", "opposite"),
        FieldSpec("tau", "τ⁻", "fermion", 0.5, 1.5, -3, "singlet", "doublet/singlet", "-1/2,-1"),
        FieldSpec("anti_tau", "τ⁺", "fermion", 0.5, 1.5, 3, "singlet", "conjugate", "opposite"),
        FieldSpec("neutrino", "ν", "fermion", 0.5, 1.5, 0, "singlet", "doublet", "-1/2"),
        FieldSpec("anti_neutrino", "ν̄", "fermion", 0.5, 1.5, 0, "singlet", "conjugate", "+1/2"),
        FieldSpec("ghost_g", "cᵍ", "ghost", 0.0, 1.0, 0, "adjoint 8", "singlet", "0", 8),
        FieldSpec("ghost_g_bar", "c̄ᵍ", "ghost", 0.0, 1.0, 0, "adjoint 8", "singlet", "0", 8),
        FieldSpec("ghost_w_plus", "c⁺", "ghost", 0.0, 1.0, 3, "singlet", "charged", "+1"),
        FieldSpec("ghost_w_minus", "c⁻", "ghost", 0.0, 1.0, -3, "singlet", "charged", "-1"),
    )


def _sectors() -> tuple[SectorSpec, ...]:
    return (
        SectorSpec("qcd_gauge", "QCD gauge", "-¼ Gᵃ_{μν}Gᵃμν", 4, "SU(3)c gauge basis"),
        SectorSpec("electroweak_gauge", "Electroweak gauge", "-¼ Wⁱ_{μν}Wⁱμν - ¼ B_{μν}Bμν", 4, "SU(2)L × U(1)Y gauge basis"),
        SectorSpec("fermion_kinetic", "Fermion kinetic", "Σ_f f̄ iγμDμ f", 4, "chiral gauge basis"),
        SectorSpec("higgs_kinetic", "Higgs kinetic", "(DμΦ)†(DμΦ)", 4, "complex scalar doublet"),
        SectorSpec("higgs_potential", "Higgs potential", "-V(Φ),  V=-μ²Φ†Φ+λ(Φ†Φ)²", 4, "scalar gauge basis"),
        SectorSpec("yukawa", "Yukawa", "-(Q̄L Yd Φ dR + Q̄L Yu Φ̃ uR + L̄L Ye Φ eR + h.c.)", 4, "flavour and chiral basis"),
        SectorSpec("gauge_fixing", "Gauge fixing", "L_gf(Rξ)", 4, "Rξ schematic", "Gauge-dependent bookkeeping, not an observable sector."),
        SectorSpec("ghost", "Faddeev-Popov ghosts", "L_ghost(Rξ)", 4, "Rξ schematic", "Grassmann scalar fields tied to the selected gauge fixing."),
    )


def _interactions() -> tuple[InteractionSpec, ...]:
    return (
        InteractionSpec("ggg", "three-gluon", "qcd_gauge", ("gluon", "gluon", "gluon"), "g_s", 4, "qcd_gauge"),
        InteractionSpec("gggg", "four-gluon", "qcd_gauge", ("gluon", "gluon", "gluon", "gluon"), "g_s^2", 4, "qcd_gauge"),
        InteractionSpec("uug", "up-gluon current", "fermion_kinetic", ("up", "anti_up", "gluon"), "g_s", 4, "fermion_kinetic"),
        InteractionSpec("ddg", "down-gluon current", "fermion_kinetic", ("down", "anti_down", "gluon"), "g_s", 4, "fermion_kinetic"),
        InteractionSpec("ttg", "top-gluon current", "fermion_kinetic", ("top", "anti_top", "gluon"), "g_s", 4, "fermion_kinetic"),
        InteractionSpec("bbg", "bottom-gluon current", "fermion_kinetic", ("bottom", "anti_bottom", "gluon"), "g_s", 4, "fermion_kinetic"),
        InteractionSpec("uuA", "up-electromagnetic current", "fermion_kinetic", ("up", "anti_up", "photon"), "e", 4, "fermion_kinetic"),
        InteractionSpec("ddA", "down-electromagnetic current", "fermion_kinetic", ("down", "anti_down", "photon"), "e", 4, "fermion_kinetic"),
        InteractionSpec("llA", "charged-lepton electromagnetic current", "fermion_kinetic", ("charged_lepton", "anti_charged_lepton", "photon"), "e", 4, "fermion_kinetic"),
        InteractionSpec("uuZ", "up neutral current", "fermion_kinetic", ("up", "anti_up", "z_boson"), "g_Z", 4, "fermion_kinetic"),
        InteractionSpec("ddZ", "down neutral current", "fermion_kinetic", ("down", "anti_down", "z_boson"), "g_Z", 4, "fermion_kinetic"),
        InteractionSpec("llZ", "charged-lepton neutral current", "fermion_kinetic", ("charged_lepton", "anti_charged_lepton", "z_boson"), "g_Z", 4, "fermion_kinetic"),
        InteractionSpec("nnZ", "neutrino neutral current", "fermion_kinetic", ("neutrino", "anti_neutrino", "z_boson"), "g_Z", 4, "fermion_kinetic"),
        InteractionSpec("udWplus", "charged quark current", "fermion_kinetic", ("anti_up", "down", "w_plus"), "g/√2", 4, "fermion_kinetic", "udWminus"),
        InteractionSpec("udWminus", "conjugate charged quark current", "fermion_kinetic", ("up", "anti_down", "w_minus"), "g/√2", 4, "fermion_kinetic", "udWplus"),
        InteractionSpec("lnWplus", "charged lepton current", "fermion_kinetic", ("anti_neutrino", "charged_lepton", "w_plus"), "g/√2", 4, "fermion_kinetic", "lnWminus"),
        InteractionSpec("lnWminus", "conjugate charged lepton current", "fermion_kinetic", ("neutrino", "anti_charged_lepton", "w_minus"), "g/√2", 4, "fermion_kinetic", "lnWplus"),
        InteractionSpec("WWA", "W pair-photon", "electroweak_gauge", ("w_plus", "w_minus", "photon"), "e", 4, "electroweak_gauge"),
        InteractionSpec("WWZ", "W pair-Z", "electroweak_gauge", ("w_plus", "w_minus", "z_boson"), "g cosθW", 4, "electroweak_gauge"),
        InteractionSpec("WWAA", "W pair-two-photon", "electroweak_gauge", ("w_plus", "w_minus", "photon", "photon"), "e^2", 4, "electroweak_gauge"),
        InteractionSpec("WWAZ", "W pair-photon-Z", "electroweak_gauge", ("w_plus", "w_minus", "photon", "z_boson"), "e g cosθW", 4, "electroweak_gauge"),
        InteractionSpec("WWZZ", "W pair-two-Z", "electroweak_gauge", ("w_plus", "w_minus", "z_boson", "z_boson"), "g^2 cos²θW", 4, "electroweak_gauge"),
        InteractionSpec("WWH", "W pair-Higgs", "higgs_kinetic", ("w_plus", "w_minus", "higgs"), "g M_W", 3, "higgs_kinetic"),
        InteractionSpec("ZZH", "Z pair-Higgs", "higgs_kinetic", ("z_boson", "z_boson", "higgs"), "g_Z M_Z", 3, "higgs_kinetic"),
        InteractionSpec("WWHH", "W pair-two-Higgs", "higgs_kinetic", ("w_plus", "w_minus", "higgs", "higgs"), "g^2", 4, "higgs_kinetic"),
        InteractionSpec("ZZHH", "Z pair-two-Higgs", "higgs_kinetic", ("z_boson", "z_boson", "higgs", "higgs"), "g_Z^2", 4, "higgs_kinetic"),
        InteractionSpec("ttH", "top Yukawa", "yukawa", ("top", "anti_top", "higgs"), "y_t", 4, "yukawa"),
        InteractionSpec("bbH", "bottom Yukawa", "yukawa", ("bottom", "anti_bottom", "higgs"), "y_b", 4, "yukawa"),
        InteractionSpec("tauH", "tau Yukawa", "yukawa", ("tau", "anti_tau", "higgs"), "y_tau", 4, "yukawa"),
        InteractionSpec("HHHH", "Higgs quartic", "higgs_potential", ("higgs", "higgs", "higgs", "higgs"), "lambda_h", 4, "higgs_potential"),
        InteractionSpec("ghostG", "QCD ghost-gluon", "ghost", ("ghost_g", "ghost_g_bar", "gluon"), "g_s", 4, "ghost"),
        InteractionSpec("ghostWA", "charged ghost-photon", "ghost", ("ghost_w_plus", "ghost_w_minus", "photon"), "e", 4, "ghost"),
        InteractionSpec("ghostWZ", "charged ghost-Z", "ghost", ("ghost_w_plus", "ghost_w_minus", "z_boson"), "g cosθW", 4, "ghost"),
    )


def standard_model_catalog() -> StandardModelCatalog:
    parameters = {
        "g_s": 1.22,
        "g": 0.653,
        "g_prime": 0.358,
        "lambda_h": 0.129,
        "v": 246.22,
        "y_t": 0.995,
        "y_b": 0.024,
        "y_tau": 0.0102,
        "xi": 1.0,
    }
    ranges = {
        "g_s": (0.2, 2.0, 0.002),
        "g": (0.2, 1.2, 0.001),
        "g_prime": (0.1, 1.0, 0.001),
        "lambda_h": (0.01, 0.6, 0.001),
        "v": (100.0, 350.0, 0.1),
        "y_t": (0.1, 1.5, 0.001),
        "y_b": (0.0, 0.1, 0.0001),
        "y_tau": (0.0, 0.05, 0.0001),
        "xi": (0.1, 5.0, 0.01),
    }
    return StandardModelCatalog(
        gauge_group=("SU(3)c", "SU(2)L", "U(1)Y"),
        sectors=_sectors(),
        fields=_fields(),
        interactions=_interactions(),
        default_parameters=parameters,
        control_ranges=ranges,
        gauge_convention="compact unbroken-basis catalog with an Rxi schematic ghost/gauge-fixing layer",
    )


def tree_level_observables(parameters: Mapping[str, float] | None = None) -> dict[str, object]:
    catalog = standard_model_catalog()
    values = dict(catalog.default_parameters)
    if parameters:
        values.update({key: float(value) for key, value in parameters.items()})
    g = values["g"]
    gp = values["g_prime"]
    v = values["v"]
    lam = values["lambda_h"]
    norm = math.hypot(g, gp)
    sin_theta = gp / norm
    cos_theta = g / norm
    electric = g * sin_theta
    m_w = g * v / 2.0
    m_z = norm * v / 2.0
    m_h = math.sqrt(max(0.0, 2.0 * lam)) * v
    neutral_mass_squared = (v * v / 4.0) * np.array(
        [[g * g, -g * gp], [-g * gp, gp * gp]], dtype=float
    )
    mixing = np.array([[sin_theta, cos_theta], [cos_theta, -sin_theta]], dtype=float)
    eigenvalues = np.linalg.eigvalsh(neutral_mass_squared)
    return {
        "parameters": values,
        "sin_theta_w": sin_theta,
        "cos_theta_w": cos_theta,
        "sin2_theta_w": sin_theta * sin_theta,
        "electric_charge_coupling": electric,
        "m_w": m_w,
        "m_z": m_z,
        "m_h": m_h,
        "m_top": values["y_t"] * v / math.sqrt(2.0),
        "m_bottom": values["y_b"] * v / math.sqrt(2.0),
        "m_tau": values["y_tau"] * v / math.sqrt(2.0),
        "neutral_mass_squared": neutral_mass_squared.tolist(),
        "neutral_mass_eigenvalues": eigenvalues.tolist(),
        "photon_mass_squared_residual": float(abs(eigenvalues[0])),
        "mixing_matrix": mixing.tolist(),
        "mixing_orthogonality_residual": float(np.linalg.norm(mixing.T @ mixing - np.eye(2))),
    }
