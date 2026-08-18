"""Certified coverage screening for candidate Hilbert-Polya operators.

``curverank_spectral`` answers "how far is this truncated spectrum from the
zeros?" as a single certified number ``M_n``.  This module answers a different,
proportion-shaped question with the same rigour:

    Of the first ``k`` Riemann zeros, how many are matched -- within a stated
    tolerance ``tau`` -- by the certified spectrum of a finite truncation of a
    candidate operator?

Every count is derived from interval enclosures, so the answer is a *pair* of
exact rational bounds rather than a point estimate:

* a zero is **certainly covered** when some eigenvalue enclosure lies within
  ``tau`` of it for every value in both enclosures;
* a zero is **certainly uncovered** when every eigenvalue enclosure is farther
  than ``tau`` from it for every value in both enclosures;
* anything else is **undetermined** at the current precision and is charged
  against the upper bound, never the lower one.

The comparison threshold is an input, not a result.  When the certified upper
bound falls below the threshold, the run emits a negative-result certificate:
that finite truncation of that operator provably cannot reach the threshold at
that tolerance.

CLAIM BOUNDARY:
Published density theorems about the proportion of nontrivial zeta zeros on the
critical line are statements about the zeros of the zeta function itself. This
module neither evaluates, reproduces, nor contradicts any such statement. It
measures a different finite quantity: spectral coverage by one truncated
candidate operator. A negative certificate rules out one truncation of one
operator family at one tolerance, and carries no implication for the Riemann
Hypothesis or for the Hilbert-Polya program as a whole.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from typing import Mapping, Sequence

import mpmath as mp

from gaugegap.curverank_certified import (
    certified_dirac_rindler_spectrum,
    certified_quantum_graph_spectrum,
    certified_xp_spectrum,
)
from gaugegap.curverank_spectral import (
    certified_spectral_mismatch,
    riemann_zero_intervals,
)
from gaugegap.rigorous.interval_arithmetic import Interval


CLAIM_BOUNDARY = (
    "Finite-truncation spectral screening only. This artifact measures how many of the "
    "first k certified Riemann-zero enclosures are matched within a stated tolerance by "
    "the certified spectrum of one truncated candidate operator. It is not a statement "
    "about the proportion of zeta zeros on the critical line, does not evaluate or "
    "contradict any published density theorem, and is not evidence for or against the "
    "Riemann Hypothesis. A negative certificate rules out exactly one finite truncation "
    "of one operator family at one tolerance."
)

CERTIFICATE_SCHEMA = "gaugegap.curverank_coverage_certificate.v1"

FAMILIES = ("xp", "dirac_rindler", "quantum_graph")

VERDICT_BELOW = "CERTIFIED_BELOW_THRESHOLD"
VERDICT_MEETS = "MEETS_THRESHOLD_AT_TRUNCATION"
VERDICT_UNDETERMINED = "UNDETERMINED_AT_PRECISION"

_DEFAULT_GRAPH_EDGES = [(0, 1), (0, 2), (0, 3)]


class CurveRankCoverageError(RuntimeError):
    """Raised when a screening request is not well posed."""


def certified_family_spectrum(family: str, n: int, **kwargs) -> list[Interval]:
    """Certified eigenvalue enclosures for a named candidate operator family."""

    if family == "xp":
        return certified_xp_spectrum(n, kwargs.get("L", 1.0))
    if family == "dirac_rindler":
        return certified_dirac_rindler_spectrum(
            n, kwargs.get("acceleration", 1.0), kwargs.get("mass", 0.0)
        )
    if family == "quantum_graph":
        import numpy as np

        edges = kwargs.get("edges", _DEFAULT_GRAPH_EDGES)
        lengths = kwargs.get(
            "lengths", [1.0, float(np.sqrt(2)), float(np.sqrt(3))]
        )
        return certified_quantum_graph_spectrum(edges, lengths, n)
    raise CurveRankCoverageError(
        f"unknown family {family!r}; choose from {', '.join(FAMILIES)}"
    )


def _separation_bounds(a: Interval, z: Interval) -> tuple[mp.mpf, mp.mpf]:
    """Rigorous ``(lower, upper)`` bounds on ``|x - y|`` for ``x in a``, ``y in z``.

    The lower endpoint is rounded down and the upper endpoint rounded up in the
    directed-rounding context, so neither bound can be crossed by rounding.
    """

    if a.upper < z.lower:
        low = (mp.iv.mpf([z.lower, z.lower]) - mp.iv.mpf([a.upper, a.upper])).a
    elif a.lower > z.upper:
        low = (mp.iv.mpf([a.lower, a.lower]) - mp.iv.mpf([z.upper, z.upper])).a
    else:
        low = mp.mpf(0)
    diff_hi = mp.iv.mpf([a.upper, a.upper]) - mp.iv.mpf([z.lower, z.lower])
    diff_lo = mp.iv.mpf([a.lower, a.lower]) - mp.iv.mpf([z.upper, z.upper])
    high = max(abs(diff_hi.a), abs(diff_hi.b), abs(diff_lo.a), abs(diff_lo.b))
    return mp.mpf(low), mp.mpf(high)


@dataclass(frozen=True)
class ZeroCoverage:
    """Per-zero verdict at the working precision."""

    index: int
    status: str  # "covered", "uncovered", or "undetermined"
    nearest_lower_bound: mp.mpf
    nearest_upper_bound: mp.mpf

    def to_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "status": self.status,
            "nearest_separation_lower": float(self.nearest_lower_bound),
            "nearest_separation_upper": float(self.nearest_upper_bound),
        }


@dataclass(frozen=True)
class CoverageResult:
    """Certified bounds on the matched fraction of the first ``k`` zeros."""

    k_zeros: int
    tolerance: float
    covered: int
    uncovered: int
    undetermined: int
    per_zero: tuple[ZeroCoverage, ...]

    @property
    def lower_fraction(self) -> Fraction:
        return Fraction(self.covered, self.k_zeros)

    @property
    def upper_fraction(self) -> Fraction:
        return Fraction(self.covered + self.undetermined, self.k_zeros)

    def to_dict(self) -> dict[str, object]:
        lower, upper = self.lower_fraction, self.upper_fraction
        return {
            "k_zeros": self.k_zeros,
            "tolerance": self.tolerance,
            "certainly_covered": self.covered,
            "certainly_uncovered": self.uncovered,
            "undetermined": self.undetermined,
            "coverage_lower": {"numerator": lower.numerator, "denominator": lower.denominator},
            "coverage_upper": {"numerator": upper.numerator, "denominator": upper.denominator},
            "coverage_lower_float": float(lower),
            "coverage_upper_float": float(upper),
            "per_zero": [entry.to_dict() for entry in self.per_zero],
        }


def certified_coverage(
    eig_intervals: Sequence[Interval],
    zero_intervals: Sequence[Interval],
    tolerance: float,
) -> CoverageResult:
    """Count how many zero enclosures are certifiably matched within ``tolerance``.

    Enclosures that contain zero are dropped first, mirroring the zero-mode
    filtering in :func:`gaugegap.curverank_spectral.certified_spectral_mismatch`,
    so a symmetric spectrum's structural zero mode cannot "cover" a zero.
    """

    if tolerance <= 0:
        raise CurveRankCoverageError("tolerance must be positive")
    if not zero_intervals:
        raise CurveRankCoverageError("no zero enclosures supplied")

    tau = mp.mpf(tolerance)
    abs_eigs = [abs(e) for e in eig_intervals if not (e.lower <= 0 <= e.upper)]

    entries: list[ZeroCoverage] = []
    covered = uncovered = undetermined = 0
    for index, zero in enumerate(zero_intervals):
        best_lower = mp.inf
        best_upper = mp.inf
        certainly = False
        possibly = False
        for eig in abs_eigs:
            low, high = _separation_bounds(eig, zero)
            if low < best_lower:
                best_lower = low
            if high < best_upper:
                best_upper = high
            if high <= tau:
                certainly = True
            if low <= tau:
                possibly = True
        if certainly:
            status = "covered"
            covered += 1
        elif not possibly:
            status = "uncovered"
            uncovered += 1
        else:
            status = "undetermined"
            undetermined += 1
        entries.append(ZeroCoverage(index, status, mp.mpf(best_lower), mp.mpf(best_upper)))

    return CoverageResult(
        k_zeros=len(zero_intervals),
        tolerance=float(tolerance),
        covered=covered,
        uncovered=uncovered,
        undetermined=undetermined,
        per_zero=tuple(entries),
    )


def classify(result: CoverageResult, threshold: Fraction | float) -> str:
    """Compare the certified coverage bounds against a supplied threshold."""

    target = Fraction(threshold).limit_denominator(10**9) if not isinstance(
        threshold, Fraction
    ) else threshold
    if result.upper_fraction < target:
        return VERDICT_BELOW
    if result.lower_fraction >= target:
        return VERDICT_MEETS
    return VERDICT_UNDETERMINED


def screen_family(
    family: str,
    n_basis: int,
    k_zeros: int,
    *,
    tolerance: float,
    threshold: Fraction | float,
    zeros_method: str = "auto",
    null_seeds: Sequence[int] = (),
    **family_kwargs,
) -> dict[str, object]:
    """Run one certified coverage screen and return the certificate payload.

    When ``null_seeds`` are supplied, the same coverage counter is run over
    structureless spectra of the same size and the result is recorded beside the
    candidate's, so the two numbers can never be quoted apart.
    """

    if family not in FAMILIES:
        raise CurveRankCoverageError(
            f"unknown family {family!r}; choose from {', '.join(FAMILIES)}"
        )
    if n_basis < 2:
        raise CurveRankCoverageError("n_basis must be at least 2")
    if k_zeros < 1:
        raise CurveRankCoverageError("k_zeros must be at least 1")

    eig_intervals = certified_family_spectrum(family, n_basis, **family_kwargs)
    zero_intervals = riemann_zero_intervals(k_zeros, method=zeros_method)
    coverage = certified_coverage(eig_intervals, zero_intervals, tolerance)
    mismatch = certified_spectral_mismatch(eig_intervals, zero_intervals)
    target = (
        threshold
        if isinstance(threshold, Fraction)
        else Fraction(threshold).limit_denominator(10**9)
    )
    verdict = classify(coverage, target)

    payload: dict[str, object] = {
        "schema": CERTIFICATE_SCHEMA,
        "family": family,
        "arithmetic": "interval_enclosures_with_directed_rounding",
        "working_precision_dps": int(mp.mp.dps),
        "parameters": {
            "n_basis": n_basis,
            "k_zeros": k_zeros,
            "tolerance": float(tolerance),
            "zeros_method": zeros_method,
            **{key: _jsonable(value) for key, value in sorted(family_kwargs.items())},
        },
        "threshold": {
            "numerator": target.numerator,
            "denominator": target.denominator,
            "float": float(target),
            "role": "supplied comparison threshold; an input to this screen, not a result of it",
        },
        "coverage": coverage.to_dict(),
        "certified_mismatch": {
            "lower": float(mismatch.lower),
            "upper": float(mismatch.upper),
            "definition": "M_n = ||sort(|eig|)[:n] - zeros[:n]||_2 / sqrt(n), certified enclosure",
        },
        "spectrum": {
            "enclosures": len(eig_intervals),
            "nonzero_enclosures": sum(
                1 for e in eig_intervals if not (e.lower <= 0 <= e.upper)
            ),
        },
        "verdict": verdict,
        "verdict_meaning": _verdict_meaning(verdict),
        "claim_boundary": CLAIM_BOUNDARY,
    }
    if null_seeds:
        nonzero = payload["spectrum"]["nonzero_enclosures"]  # type: ignore[index]
        payload["null_control"] = null_control(
            k_zeros,
            int(nonzero),
            tolerance=tolerance,
            seeds=null_seeds,
            zeros_method=zeros_method,
        )
        payload["beats_null_control"] = (
            coverage.lower_fraction
            > Fraction(
                int(payload["null_control"]["coverage_max"]["numerator"]),  # type: ignore[index]
                int(payload["null_control"]["coverage_max"]["denominator"]),  # type: ignore[index]
            )
        )
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    payload["certificate_digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return payload


def _verdict_meaning(verdict: str) -> str:
    if verdict == VERDICT_BELOW:
        return (
            "Negative result: at this truncation and tolerance the certified upper bound on "
            "matched zeros is strictly below the supplied threshold, so this finite model "
            "cannot reach it. No statement is made about other truncations, other operators, "
            "or the zeta zeros themselves."
        )
    if verdict == VERDICT_MEETS:
        return (
            "The certified lower bound on matched zeros reaches the supplied threshold at this "
            "truncation and tolerance. This is a finite screening observation, not evidence "
            "that the operator reproduces the zeros in any limit."
        )
    return (
        "The certified bounds straddle the supplied threshold: the enclosures are too wide at "
        "this precision to decide. Increase the working precision or the truncation size."
    )


def null_spectrum(
    k_zeros: int,
    n_values: int,
    *,
    seed: int,
    zeros_method: str = "auto",
) -> list[Interval]:
    """A structureless spectrum with the same range as the zeros it is compared to.

    The null draws ``n_values`` points uniformly from the interval spanned by the
    first ``k_zeros`` zero enclosures, using a seeded generator so the control is
    reproducible. It carries no spectral structure whatsoever: whatever coverage
    it achieves is what counting alone buys, before any operator is credited.
    """

    import numpy as np

    zeros = riemann_zero_intervals(k_zeros, method=zeros_method)
    low = float(min(z.lower for z in zeros))
    high = float(max(z.upper for z in zeros))
    generator = np.random.default_rng(seed)
    samples = sorted(generator.uniform(low, high, size=n_values))
    return [Interval.from_bounds(value, value) for value in samples]


def null_control(
    k_zeros: int,
    n_values: int,
    *,
    tolerance: float,
    seeds: Sequence[int],
    zeros_method: str = "auto",
) -> dict[str, object]:
    """Coverage achieved by structureless spectra of the same size and range.

    A candidate operator's coverage is only informative if it beats what an
    unstructured spectrum of the same size achieves by chance. This runs the
    identical coverage counter over several seeded null draws and reports the
    range, so the comparison is on the record next to the claim.
    """

    zeros = riemann_zero_intervals(k_zeros, method=zeros_method)
    fractions: list[Fraction] = []
    for seed in seeds:
        spectrum = null_spectrum(
            k_zeros, n_values, seed=seed, zeros_method=zeros_method
        )
        result = certified_coverage(spectrum, zeros, tolerance)
        fractions.append(result.upper_fraction)
    best = max(fractions)
    worst = min(fractions)
    mean = sum(fractions, Fraction(0)) / len(fractions)
    return {
        "model": "uniform draws over the range spanned by the first k zero enclosures",
        "n_values": n_values,
        "seeds": list(seeds),
        "coverage_min_float": float(worst),
        "coverage_max_float": float(best),
        "coverage_mean_float": float(mean),
        "coverage_max": {"numerator": best.numerator, "denominator": best.denominator},
        "role": (
            "null control: coverage reachable without any spectral structure. A candidate "
            "that does not exceed this range has not demonstrated anything about the zeros."
        ),
    }


def emit_coverage_coq(screens: Sequence[Mapping[str, object]]) -> str:
    """Emit a discharged Coq certificate for each screen's coverage bound.

    Following the pattern in :mod:`gaugegap.rigorous.curverank_formal_emit`, the
    interval computation is *not* re-derived inside Coq: the certified upper
    bound enters as one clearly labelled hypothesis, and Coq discharges the
    remaining real-arithmetic step with ``lra``.  Nothing is admitted.

    Only screens whose certified upper bound is strictly below the threshold
    yield a section; there is no inequality to discharge otherwise.
    """

    sections: list[str] = []
    for screen in screens:
        coverage = screen["coverage"]  # type: ignore[index]
        parameters = screen["parameters"]  # type: ignore[index]
        threshold = screen["threshold"]  # type: ignore[index]
        upper = Fraction(
            int(coverage["coverage_upper"]["numerator"]),  # type: ignore[index]
            int(coverage["coverage_upper"]["denominator"]),  # type: ignore[index]
        )
        target = Fraction(int(threshold["numerator"]), int(threshold["denominator"]))  # type: ignore[index]
        if upper >= target:
            continue
        ident = f"{screen['family']}_n{parameters['n_basis']}_k{parameters['k_zeros']}"  # type: ignore[index]
        sections.append(
            f"""Section CurveRankCoverage_{ident}.

(* TRUST INPUT (external to Coq): the certified screen reports that at most
   {coverage['certainly_covered'] + coverage['undetermined']} of the {coverage['k_zeros']} zero enclosures are matched within tolerance
   {parameters['tolerance']!r} by the truncated {screen['family']} spectrum at n = {parameters['n_basis']}.
   The bound comes from interval enclosures with directed rounding; Coq does not
   re-derive it. *)
Variable coverage_{ident} : R.
Hypothesis certified_upper_bound_{ident} :
  coverage_{ident} <= {upper.numerator} / {upper.denominator}.

Definition comparisonThreshold_{ident} : R := {target.numerator} / {target.denominator}.

(* Finite negative result: this truncation cannot reach the supplied comparison
   threshold. Not a statement about the zeta zeros, and not a proof or
   disproof of the Riemann Hypothesis. Discharged by lra; closed with Qed. *)
Theorem coverage_below_threshold_{ident} :
  coverage_{ident} < comparisonThreshold_{ident}.
Proof.
  unfold comparisonThreshold_{ident}.
  lra.
Qed.

End CurveRankCoverage_{ident}.
"""
        )

    header = """(* Discharged coverage certificates emitted by gaugegap.curverank_coverage.
   Requires Coq >= 8.13; uses only the standard library (Reals, Lra).

   CLAIM BOUNDARY: each theorem states that one finite truncation of one
   candidate operator cannot reach a supplied comparison threshold at a stated
   tolerance. These are not statements about the proportion of zeta zeros on the
   critical line, and they neither support nor contradict the Riemann
   Hypothesis. *)
Require Import Reals.
Require Import Lra.
Open Scope R_scope.
"""
    if not sections:
        return header + "\n(* No screen fell below its threshold; nothing to discharge. *)\n"
    return header + "\n" + "\n".join(sections)


def _jsonable(value: object) -> object:
    if isinstance(value, (int, float, str, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, Mapping):
        return {str(key): _jsonable(item) for key, item in value.items()}
    return str(value)


def canonical_json(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"
