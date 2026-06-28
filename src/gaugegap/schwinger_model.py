"""Finite Hamiltonian Schwinger model with staggered matter and Gauss projection.

The implementation uses an open one-dimensional lattice, staggered spinless
fermions on sites, compact U(1) electric-flux states on links with a hard-wall
truncation, and exact Gauss-law projection before diagonalization.

This is a finite benchmark, not the continuum Schwinger model and not 4D QED.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import itertools
from typing import Iterable

import numpy as np


CLAIM_BOUNDARY = (
    "finite open-chain lattice Schwinger benchmark with staggered fermions and "
    "hard-wall electric-flux truncation; not a continuum extrapolation, not 3+1D QED, "
    "and not a Yang--Mills mass-gap result"
)


@dataclass(frozen=True)
class SchwingerConfig:
    n_sites: int = 4
    flux_truncation: int = 2
    gauge_coupling: float = 1.0
    lattice_spacing: float = 1.0
    fermion_mass: float = 0.2
    hopping: float | None = None
    left_boundary_flux: int = 0
    right_boundary_flux: int = 0

    def __post_init__(self) -> None:
        if self.n_sites < 2:
            raise ValueError("n_sites must be at least 2")
        if self.flux_truncation < 1:
            raise ValueError("flux_truncation must be at least 1")
        if self.gauge_coupling <= 0 or self.lattice_spacing <= 0:
            raise ValueError("gauge_coupling and lattice_spacing must be positive")

    @property
    def kinetic_hopping(self) -> float:
        return 1.0 / (2.0 * self.lattice_spacing) if self.hopping is None else self.hopping


@dataclass(frozen=True)
class BasisState:
    occupations: tuple[int, ...]
    fluxes: tuple[int, ...]


@dataclass(frozen=True)
class GaussAudit:
    physical_dimension: int
    max_basis_residual: float
    transition_leakage_count: int
    clipped_hopping_count: int
    passed: bool


@dataclass(frozen=True)
class SchwingerResult:
    config: dict[str, object]
    physical_dimension: int
    ground_energy: float
    first_excited_energy: float
    spectral_gap: float
    hermiticity_residual: float
    gauss_audit: dict[str, object]
    charge_density: tuple[float, ...]
    electric_flux: tuple[float, ...]
    staggered_condensate: float
    claim_boundary: str = CLAIM_BOUNDARY

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def staggered_background(site: int) -> int:
    return (1 - (-1) ** site) // 2


def site_charge(occupations: tuple[int, ...], site: int) -> int:
    return occupations[site] - staggered_background(site)


def gauss_residuals(state: BasisState, config: SchwingerConfig) -> tuple[int, ...]:
    residuals = []
    for site in range(config.n_sites):
        incoming = config.left_boundary_flux if site == 0 else state.fluxes[site - 1]
        outgoing = config.right_boundary_flux if site == config.n_sites - 1 else state.fluxes[site]
        residuals.append(outgoing - incoming - site_charge(state.occupations, site))
    return tuple(residuals)


def enumerate_physical_basis(config: SchwingerConfig) -> tuple[BasisState, ...]:
    flux_values = range(-config.flux_truncation, config.flux_truncation + 1)
    physical: list[BasisState] = []
    for occupations in itertools.product((0, 1), repeat=config.n_sites):
        for fluxes in itertools.product(flux_values, repeat=config.n_sites - 1):
            state = BasisState(tuple(occupations), tuple(fluxes))
            if all(value == 0 for value in gauss_residuals(state, config)):
                physical.append(state)
    return tuple(physical)


def _apply_annihilation(bits: tuple[int, ...], site: int):
    if bits[site] == 0:
        return None
    sign = -1.0 if sum(bits[:site]) % 2 else 1.0
    result = list(bits)
    result[site] = 0
    return tuple(result), sign


def _apply_creation(bits: tuple[int, ...], site: int):
    if bits[site] == 1:
        return None
    sign = -1.0 if sum(bits[:site]) % 2 else 1.0
    result = list(bits)
    result[site] = 1
    return tuple(result), sign


def _fermion_hop(bits: tuple[int, ...], source: int, target: int):
    annihilated = _apply_annihilation(bits, source)
    if annihilated is None:
        return None
    intermediate, sign_a = annihilated
    created = _apply_creation(intermediate, target)
    if created is None:
        return None
    result, sign_c = created
    return result, sign_a * sign_c


def build_projected_hamiltonian(config: SchwingerConfig) -> tuple[np.ndarray, tuple[BasisState, ...], GaussAudit]:
    basis = enumerate_physical_basis(config)
    if not basis:
        raise ValueError("Gauss-law sector is empty for the requested boundaries/truncation")
    if len(basis) > 4096:
        raise ValueError("projected Hilbert space too large for dense exact diagonalization")
    lookup = {state: index for index, state in enumerate(basis)}
    h = np.zeros((len(basis), len(basis)), dtype=complex)
    leakage = 0
    clipped = 0

    for column, state in enumerate(basis):
        electric = 0.5 * config.gauge_coupling**2 * config.lattice_spacing * sum(
            flux * flux for flux in state.fluxes
        )
        mass = config.fermion_mass * sum(
            ((-1) ** site) * (occupation - 0.5)
            for site, occupation in enumerate(state.occupations)
        )
        h[column, column] += electric + mass

        for link in range(config.n_sites - 1):
            left = _fermion_hop(state.occupations, link + 1, link)
            if left is not None:
                occupations, sign = left
                new_fluxes = list(state.fluxes)
                new_fluxes[link] += 1
                if new_fluxes[link] <= config.flux_truncation:
                    target = BasisState(occupations, tuple(new_fluxes))
                    row = lookup.get(target)
                    if row is None:
                        leakage += 1
                    else:
                        h[row, column] += -config.kinetic_hopping * sign
                else:
                    clipped += 1

            right = _fermion_hop(state.occupations, link, link + 1)
            if right is not None:
                occupations, sign = right
                new_fluxes = list(state.fluxes)
                new_fluxes[link] -= 1
                if new_fluxes[link] >= -config.flux_truncation:
                    target = BasisState(occupations, tuple(new_fluxes))
                    row = lookup.get(target)
                    if row is None:
                        leakage += 1
                    else:
                        h[row, column] += -config.kinetic_hopping * sign
                else:
                    clipped += 1

    residual = max(abs(value) for state in basis for value in gauss_residuals(state, config))
    audit = GaussAudit(len(basis), float(residual), leakage, clipped, residual == 0 and leakage == 0)
    return h, basis, audit


def solve_schwinger(config: SchwingerConfig = SchwingerConfig()) -> SchwingerResult:
    h, basis, audit = build_projected_hamiltonian(config)
    denominator = max(float(np.linalg.norm(h)), np.finfo(float).tiny)
    hermiticity = float(np.linalg.norm(h - h.conj().T) / denominator)
    eigenvalues, eigenvectors = np.linalg.eigh(h)
    probabilities = np.abs(eigenvectors[:, 0]) ** 2
    probabilities = probabilities / probabilities.sum()

    charges = tuple(
        float(sum(probability * site_charge(state.occupations, site) for probability, state in zip(probabilities, basis)))
        for site in range(config.n_sites)
    )
    fluxes = tuple(
        float(sum(probability * state.fluxes[link] for probability, state in zip(probabilities, basis)))
        for link in range(config.n_sites - 1)
    )
    condensate = float(sum(((-1) ** site) * charges[site] for site in range(config.n_sites)) / config.n_sites)
    first = float(eigenvalues[1]) if len(eigenvalues) > 1 else float(eigenvalues[0])
    return SchwingerResult(
        asdict(config),
        len(basis),
        float(eigenvalues[0]),
        first,
        first - float(eigenvalues[0]),
        hermiticity,
        asdict(audit),
        charges,
        fluxes,
        condensate,
    )


def scan_mass(masses: Iterable[float], base: SchwingerConfig = SchwingerConfig()) -> list[dict[str, float]]:
    rows = []
    for mass in masses:
        config = SchwingerConfig(
            n_sites=base.n_sites,
            flux_truncation=base.flux_truncation,
            gauge_coupling=base.gauge_coupling,
            lattice_spacing=base.lattice_spacing,
            fermion_mass=float(mass),
            hopping=base.hopping,
            left_boundary_flux=base.left_boundary_flux,
            right_boundary_flux=base.right_boundary_flux,
        )
        result = solve_schwinger(config)
        rows.append({
            "fermion_mass": float(mass),
            "ground_energy": result.ground_energy,
            "spectral_gap": result.spectral_gap,
            "staggered_condensate": result.staggered_condensate,
        })
    return rows
