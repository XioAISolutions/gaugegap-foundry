"""Error-budget separation for finite-system benchmarks (issue #12, A6).

A small, principled way to keep the *sources* of uncertainty in a result
separate rather than collapsing them into one opaque number. Each contribution
is tagged with a category (statistical / systematic / truncation / numerical)
and a combination kind:

  - ``stochastic`` contributions (shot noise, sampling) combine in **quadrature**;
  - ``bound`` contributions (truncation bounds, systematic offsets) are
    **worst-case** and combine **linearly**.

The conservative total is ``sqrt(sum of stochastic^2) + sum of bounds`` -- random
errors added in quadrature, then bounded systematics added on top. This mirrors
standard metrology practice and makes the dominant source explicit.

CLAIM BOUNDARY: this is bookkeeping for finite-system numerical uncertainty. It
makes no continuum or first-principles claim.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

CATEGORIES = ("statistical", "systematic", "truncation", "numerical", "other")
KINDS = ("stochastic", "bound")


@dataclass(frozen=True)
class ErrorComponent:
    """One named contribution to an error budget."""

    name: str
    value: float                 # non-negative magnitude (1-sigma, or a bound)
    category: str = "other"
    kind: str = "stochastic"     # "stochastic" (quadrature) or "bound" (linear)

    def __post_init__(self) -> None:
        if not math.isfinite(self.value) or self.value < 0:
            raise ValueError(f"error value must be finite and non-negative: {self.value}")
        if self.category not in CATEGORIES:
            raise ValueError(f"category must be one of {CATEGORIES}")
        if self.kind not in KINDS:
            raise ValueError(f"kind must be one of {KINDS}")


@dataclass
class ErrorBudget:
    """A separated budget of error contributions for a single quantity."""

    quantity: str = ""
    components: list[ErrorComponent] = field(default_factory=list)

    def add(self, name: str, value: float, category: str = "other",
            kind: str = "stochastic") -> "ErrorBudget":
        self.components.append(ErrorComponent(name, float(value), category, kind))
        return self

    # -- combinations -------------------------------------------------------
    def stochastic_total(self) -> float:
        """Quadrature sum of the stochastic (random) contributions."""
        return math.sqrt(sum(c.value ** 2 for c in self.components if c.kind == "stochastic"))

    def bound_total(self) -> float:
        """Linear (worst-case) sum of the bounded contributions."""
        return sum(c.value for c in self.components if c.kind == "bound")

    def total(self) -> float:
        """Conservative total: quadrature of stochastics + linear of bounds."""
        return self.stochastic_total() + self.bound_total()

    # -- introspection ------------------------------------------------------
    def by_category(self) -> dict[str, float]:
        """Per-category combined magnitude (quadrature within a category)."""
        out: dict[str, float] = {}
        for cat in CATEGORIES:
            vals = [c.value for c in self.components if c.category == cat]
            if vals:
                out[cat] = math.sqrt(sum(v ** 2 for v in vals))
        return out

    def dominant(self) -> ErrorComponent | None:
        """The single largest contribution (the thing to reduce first)."""
        return max(self.components, key=lambda c: c.value, default=None)

    def as_dict(self) -> dict[str, object]:
        dom = self.dominant()
        return {
            "quantity": self.quantity,
            "components": [
                {"name": c.name, "value": c.value, "category": c.category, "kind": c.kind}
                for c in self.components
            ],
            "stochastic_total": self.stochastic_total(),
            "bound_total": self.bound_total(),
            "total": self.total(),
            "by_category": self.by_category(),
            "dominant": dom.name if dom else None,
        }

    def report(self) -> str:
        lines = [f"Error budget for {self.quantity or '(unnamed)'}:"]
        for c in sorted(self.components, key=lambda x: -x.value):
            lines.append(f"  {c.value:.3e}  [{c.category}/{c.kind}]  {c.name}")
        lines.append(f"  -> statistical (quadrature): {self.stochastic_total():.3e}")
        lines.append(f"  -> systematic  (linear)    : {self.bound_total():.3e}")
        lines.append(f"  => conservative total       : {self.total():.3e}")
        dom = self.dominant()
        if dom is not None:
            lines.append(f"  (dominant source: {dom.name})")
        return "\n".join(lines)
