"""Fail-closed structural audits for the finite Standard Model catalog."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Mapping

import numpy as np

from gaugegap.standard_model_catalog import StandardModelCatalog, tree_level_observables


@dataclass(frozen=True)
class AuditCheck:
    check_id: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class LagrangianAudit:
    passed: bool
    checks: tuple[AuditCheck, ...]
    field_count: int
    sector_count: int
    interaction_count: int
    charge_violations: tuple[str, ...]
    unknown_references: tuple[str, ...]
    nonrenormalizable_terms: tuple[str, ...]
    claim_boundary: str

    def summary(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "checks": [asdict(check) for check in self.checks],
            "field_count": self.field_count,
            "sector_count": self.sector_count,
            "interaction_count": self.interaction_count,
            "charge_violations": list(self.charge_violations),
            "unknown_references": list(self.unknown_references),
            "nonrenormalizable_terms": list(self.nonrenormalizable_terms),
            "claim_boundary": self.claim_boundary,
        }


def audit_standard_model(
    catalog: StandardModelCatalog,
    parameters: Mapping[str, float] | None = None,
    *,
    tolerance: float = 1e-10,
) -> LagrangianAudit:
    """Audit references, dimensions, charges, conjugate pairs, and EWSB algebra."""
    fields = catalog.field_map()
    sectors = catalog.sector_map()
    interactions = catalog.interaction_map()
    checks: list[AuditCheck] = []

    field_ids = [field.field_id for field in catalog.fields]
    sector_ids = [sector.sector_id for sector in catalog.sectors]
    interaction_ids = [interaction.interaction_id for interaction in catalog.interactions]
    unique_ids = (
        len(field_ids) == len(set(field_ids))
        and len(sector_ids) == len(set(sector_ids))
        and len(interaction_ids) == len(set(interaction_ids))
    )
    checks.append(AuditCheck("unique_ids", unique_ids, "field, sector, and interaction identifiers are unique"))

    unknown: list[str] = []
    charge_violations: list[str] = []
    nonrenormalizable: list[str] = []
    partner_errors: list[str] = []
    for interaction in catalog.interactions:
        if interaction.sector_id not in sectors:
            unknown.append(f"{interaction.interaction_id}:sector:{interaction.sector_id}")
        if interaction.parent_term not in sectors:
            unknown.append(f"{interaction.interaction_id}:parent:{interaction.parent_term}")
        for field_id in interaction.fields:
            if field_id not in fields:
                unknown.append(f"{interaction.interaction_id}:field:{field_id}")
        if all(field_id in fields for field_id in interaction.fields):
            total = sum(fields[field_id].charge_thirds for field_id in interaction.fields)
            if total != 0:
                charge_violations.append(f"{interaction.interaction_id}:{total}/3")
        if interaction.operator_dimension > 4:
            nonrenormalizable.append(interaction.interaction_id)
        partner = interaction.hermitian_partner
        if partner:
            other = interactions.get(partner)
            if other is None or other.hermitian_partner != interaction.interaction_id:
                partner_errors.append(interaction.interaction_id)

    checks.append(AuditCheck("references_resolve", not unknown, "all fields and parent sectors resolve"))
    checks.append(AuditCheck("electric_charge_conserved", not charge_violations, "every catalogued vertex has zero net electric charge"))
    checks.append(AuditCheck("renormalizable_dimensions", not nonrenormalizable, "all catalogued operators have dimension at most four"))
    checks.append(AuditCheck("hermitian_pairs", not partner_errors, "declared charged-current conjugate pairs are reciprocal"))

    known_couplings = {
        "g_s", "g_s^2", "g", "g/√2", "g^2", "g_Z", "g_Z^2",
        "e", "e^2", "g cosθW", "g^2 cos²θW", "e g cosθW",
        "g M_W", "g_Z M_Z", "y_t", "y_b", "y_tau", "lambda_h",
    }
    unknown_couplings = sorted({
        interaction.coupling for interaction in catalog.interactions
        if interaction.coupling not in known_couplings
    })
    checks.append(AuditCheck("couplings_declared", not unknown_couplings, "all interaction couplings are recognized by the catalog"))

    values = dict(catalog.default_parameters)
    if parameters:
        values.update({key: float(value) for key, value in parameters.items()})
    finite_positive = all(math.isfinite(value) and value >= 0.0 for value in values.values()) and values.get("v", 0.0) > 0.0
    checks.append(AuditCheck("parameters_finite", finite_positive, "configured couplings and symmetry-breaking scale are finite and nonnegative"))

    observables = tree_level_observables(values)
    matrix = np.asarray(observables["neutral_mass_squared"], dtype=float)
    symmetric = np.allclose(matrix, matrix.T, atol=tolerance, rtol=0.0)
    checks.append(AuditCheck("neutral_mass_matrix_symmetric", bool(symmetric), "neutral electroweak mass matrix is symmetric"))
    photon_zero = float(observables["photon_mass_squared_residual"]) <= tolerance * max(1.0, float(np.linalg.norm(matrix)))
    checks.append(AuditCheck("photon_massless_tree_level", photon_zero, "one neutral eigenvalue is zero within numerical tolerance"))
    mixing_orthogonal = float(observables["mixing_orthogonality_residual"]) <= tolerance
    checks.append(AuditCheck("mixing_matrix_orthogonal", mixing_orthogonal, "A/Z mixing matrix is orthogonal"))
    masses_positive = all(float(observables[key]) > 0.0 for key in ("m_w", "m_z", "m_h", "m_top", "m_bottom", "m_tau"))
    checks.append(AuditCheck("tree_level_masses_positive", masses_positive, "configured tree-level masses are positive"))

    convention_ok = "Rxi" in catalog.gauge_convention or "Rξ" in catalog.gauge_convention
    checks.append(AuditCheck("gauge_convention_explicit", convention_ok, "gauge-fixing and ghost terms declare an Rxi schematic convention"))
    source_ok = "canonical" in catalog.source_note.lower() and "blackboard" in catalog.source_note.lower()
    checks.append(AuditCheck("source_boundary_explicit", source_ok, "artistic blackboard text is not treated as the scientific source of truth"))

    passed = all(check.passed for check in checks)
    return LagrangianAudit(
        passed=passed,
        checks=tuple(checks),
        field_count=len(catalog.fields),
        sector_count=len(catalog.sectors),
        interaction_count=len(catalog.interactions),
        charge_violations=tuple(charge_violations),
        unknown_references=tuple(unknown),
        nonrenormalizable_terms=tuple(nonrenormalizable),
        claim_boundary=catalog.claim_boundary,
    )
