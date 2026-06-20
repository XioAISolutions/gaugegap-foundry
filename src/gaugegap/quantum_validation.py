"""Quantum-validation harness: check quantum eigenvalue estimates against the
certified interval kernel.

Given a Hermitian operator and quantum estimates (QPE / Krylov / ESPRIT / QCELS),
this reports, per estimate, whether it lands inside a certified eigenvalue
enclosure and its residual against the classical exact spectrum. It is a typed,
schema-stable orchestration layer over the existing
``curverank_signal.validate_against_certified`` plus the operator registry — no
new numerics.

CLAIM BOUNDARY: finite-operator spectral screening + method benchmark. Certified
enclosures are rigorous; nothing here proves the Riemann Hypothesis or any
Millennium Prize problem, and quantum estimates are simulation unless a provider
job id is recorded elsewhere.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

import numpy as np

from gaugegap.rigorous.interval_arithmetic import Interval
from gaugegap.curverank_registry import get_operator
from gaugegap import curverank_signal as cs


@dataclass
class EstimateValidation:
    method: str
    estimate: float
    nearest_classical: float
    abs_residual_vs_classical: float
    certified_enclosure: tuple
    in_certified_enclosure: bool
    enclosure_halfwidth: float

    def to_dict(self) -> dict:
        return {
            "method": self.method,
            "estimate": self.estimate,
            "nearest_classical": self.nearest_classical,
            "abs_residual_vs_classical": self.abs_residual_vs_classical,
            "certified_enclosure": list(self.certified_enclosure),
            "in_certified_enclosure": self.in_certified_enclosure,
            "enclosure_halfwidth": self.enclosure_halfwidth,
        }


@dataclass
class ValidationReport:
    operator: str
    n_basis: int
    method: str
    n_estimates: int
    n_in_enclosure: int
    all_certified: bool
    max_abs_residual: float
    results: List[EstimateValidation] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "operator": self.operator,
            "n_basis": self.n_basis,
            "method": self.method,
            "n_estimates": self.n_estimates,
            "n_in_enclosure": f"{self.n_in_enclosure}/{self.n_estimates}",
            "all_certified": self.all_certified,
            "max_abs_residual": self.max_abs_residual,
            "results": [r.to_dict() for r in self.results],
        }


def validate_estimates(
    estimates: Sequence[float],
    *,
    method: str,
    enclosures: Sequence[Interval],
    classical_evals: np.ndarray,
    operator: str = "unknown",
    n_basis: int = 0,
    pad: float = 1e-6,
) -> ValidationReport:
    """Validate quantum ``estimates`` against certified ``enclosures`` and the
    classical exact spectrum. Reuses ``validate_against_certified`` for the
    in-enclosure test."""
    estimates = [float(x) for x in estimates]
    classical = np.asarray(classical_evals, dtype=float)
    encl_check = cs.validate_against_certified(estimates, enclosures, pad=pad)

    results: List[EstimateValidation] = []
    for est, chk in zip(estimates, encl_check):
        j = int(np.argmin(np.abs(classical - est)))
        lo, hi = chk["nearest_enclosure"]
        results.append(EstimateValidation(
            method=method,
            estimate=est,
            nearest_classical=float(classical[j]),
            abs_residual_vs_classical=abs(est - float(classical[j])),
            certified_enclosure=(float(lo), float(hi)),
            in_certified_enclosure=bool(chk["in_certified_enclosure"]),
            enclosure_halfwidth=(float(hi) - float(lo)) / 2.0,
        ))
    n_in = sum(r.in_certified_enclosure for r in results)
    max_res = max((r.abs_residual_vs_classical for r in results), default=0.0)
    return ValidationReport(
        operator=operator,
        n_basis=n_basis,
        method=method,
        n_estimates=len(results),
        n_in_enclosure=n_in,
        all_certified=(n_in == len(results) and len(results) > 0),
        max_abs_residual=max_res,
        results=results,
    )


def _estimates_for_method(
    method: str, H: np.ndarray, *, n_basis: int, seed: int,
    shots: Optional[int], use_emulator: bool, device: str,
) -> List[float]:
    """Run a single quantum method and return its eigenvalue estimate(s)."""
    rng = np.random.default_rng(seed)
    n = H.shape[0]
    psi = rng.standard_normal(n) + 1j * rng.standard_normal(n)
    psi /= np.linalg.norm(psi)

    if method == "esprit":
        return list(cs.extract_eigenvalues(
            H, psi, method="esprit", rng=np.random.default_rng(seed + 1)
        ).eigenvalues)
    if method == "qcels":
        return [float(cs.qcels(H, psi).eigenvalue)]
    if method == "krylov":
        from gaugegap.quantum.quantum_subspace_methods import quantum_krylov_method
        n_states = min(4, n)
        kr = quantum_krylov_method(np.ones(n) / np.sqrt(n), H,
                                   n_iterations=12, n_states=n_states)
        return [float(x) for x in np.real(kr.energies)]
    if method == "qpe":
        import importlib
        import sys
        from pathlib import Path
        scripts_dir = str(Path(__file__).resolve().parents[2] / "scripts")
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        rci = importlib.import_module("run_curverank_ibm")
        r = rci.run_one(n_basis, 6, shots or 4096, 2, 0.5,
                        use_emulator, device, "dense", H=H)
        return [float(r["estimated_eigenvalue"])]
    raise ValueError(f"unknown method {method!r}")


def validate_operator(
    operator: str,
    n_basis: int,
    *,
    methods: Sequence[str] = ("esprit", "qcels", "krylov", "qpe"),
    k_zeros: int = 20,
    seed: int = 0,
    shots: Optional[int] = None,
    use_emulator: bool = True,
    device: str = "",
) -> Dict[str, ValidationReport]:
    """End-to-end: build the operator, get certified enclosures + the classical
    exact spectrum, run each requested quantum method, and validate each against
    the certified kernel."""
    spec = get_operator(operator)
    H = spec.build(n_basis)
    H = (H + H.conj().T) / 2.0
    enclosures = spec.certified(n_basis)
    classical = np.linalg.eigvalsh(H)

    reports: Dict[str, ValidationReport] = {}
    for method in methods:
        estimates = _estimates_for_method(
            method, H, n_basis=n_basis, seed=seed, shots=shots,
            use_emulator=use_emulator, device=device,
        )
        reports[method] = validate_estimates(
            estimates, method=method, enclosures=enclosures,
            classical_evals=classical, operator=spec.name, n_basis=n_basis,
        )
    return reports


def quantum_error_budget(
    operator: str,
    n_basis: int,
    *,
    method: str = "qcels",
    n_runs: int = 20,
    shots: int = 1500,
    dephasing: float = 0.01,
    parent_seed: int = 1234,
    level: float = 0.95,
) -> dict:
    """Certified error budget for a stochastic quantum estimator.

    Generalises the ``run_error_budget`` QCELS pattern to any shot-noisy quantum
    method: runs ``method`` over independent child seeds, builds a confidence
    interval, and assembles a source-separated ``ErrorBudget`` (statistical CI +
    certified-enclosure truncation bound + numerical precision). Honest scope: the
    CI is a fixed-truncation statistical band; no continuum claim.
    """
    from gaugegap.repeated_runs import repeated_run
    from gaugegap.error_budget import ErrorBudget
    from gaugegap.seeding import make_rng

    spec = get_operator(operator)
    H = spec.build(n_basis)
    H = (H + H.conj().T) / 2.0
    evals = np.linalg.eigvalsh(H)
    target = float(min(evals, key=abs))           # smallest-|.| eigenvalue
    psi = np.ones(H.shape[0]) / np.sqrt(H.shape[0])

    def estimator(seed: int) -> float:
        rng = make_rng(seed)
        if method == "qcels":
            return abs(float(cs.qcels(H, psi, total_time=60.0, levels=4,
                                      shots=shots, dephasing=dephasing,
                                      rng=rng).eigenvalue))
        if method == "esprit":
            er = cs.extract_eigenvalues(H, psi, method="esprit", shots=shots,
                                        dephasing=dephasing, rng=rng)
            vals = np.asarray(er.eigenvalues)
            return abs(float(vals[np.argmin(np.abs(vals - target))]))
        raise ValueError(f"method {method!r} not supported for error budget "
                         "(use 'qcels' or 'esprit')")

    stats = repeated_run(estimator, parent_seed=parent_seed, n_runs=n_runs, level=level)

    # certified enclosure half-width for the target eigenvalue (truncation bound)
    enclosures = spec.certified(n_basis)
    idx = int(np.argmin([abs((iv.lower + iv.upper) / 2 - target) for iv in enclosures]))
    lo, hi = float(enclosures[idx].lower), float(enclosures[idx].upper)

    budget = ErrorBudget(quantity=f"{method}_estimate(|lambda_min|,{spec.name})")
    budget.add(f"{method}_shot_noise", stats.ci_halfwidth, "statistical", "stochastic")
    budget.add("certified_truncation_enclosure", (hi - lo) / 2, "truncation", "bound")
    budget.add("numerical_precision", 1e-12 * max(1.0, abs(target)), "numerical", "bound")
    dominant = budget.dominant()
    return {
        "operator": spec.name, "method": method, "n_basis": n_basis,
        "target_magnitude_classical": abs(target),
        "repeated_runs": stats.to_dict(),
        "error_budget": budget.as_dict(),
        "by_category": budget.by_category(),
        "total": budget.total(),
        "dominant_source": dominant.name if dominant else None,
        "claim_boundary": ("fixed-truncation statistical error budget for a quantum "
                           "estimator; not a continuum/Millennium claim"),
    }
