#!/usr/bin/env python3
"""Certified Eightfold-Way / Gell-Mann-Okubo benchmark report.

Runs the three certified pieces and prints a report:
  (A) certified octet spectrum and the certified count of distinct mass levels
      at the SU(3) limit, with the octet (b,c) breaking turned on;
  (B) the certified GMO residual of the model operator (encloses 0);
  (C) the certified empirical GMO residual from PDG masses, and the certified
      decuplet equal-spacing prediction of the Omega^- mass.

CLAIM BOUNDARY: a finite SU(3)-flavor mass-operator (Gell-Mann-Okubo) benchmark
made rigorous with interval arithmetic; not a lattice-QCD or continuum claim.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.eightfold import (  # noqa: E402
    OCTET,
    PDG_DECUPLET,
    PDG_OCTET,
    OctetModel,
    certified_distinct_levels,
    certified_gmo_residual_model,
    certified_octet_spectrum,
    certified_omega_prediction,
    gmo_residual_from_masses,
)


def _fmt(iv) -> str:
    return f"[{float(iv.lower):.6f}, {float(iv.upper):.6f}]"


def main() -> int:
    print("# Certified Eightfold-Way / Gell-Mann-Okubo benchmark\n")

    # (A) certified spectrum + distinct-level count.
    print("(A) Octet mass operator -- certified multiplet structure")
    symmetric = OctetModel(b=0.0, c=0.0)
    broken = OctetModel()  # default b, c != 0
    for label, model in (("SU(3) limit (b=c=0)", symmetric), ("octet breaking", broken)):
        enc = certified_octet_spectrum(model)
        clusters = certified_distinct_levels(enc)
        sizes = [len(c) for c in clusters]
        max_w = max(float(iv.width()) for iv in enc)
        print(
            f"  {label:<22}: {len(clusters)} certified-distinct level(s), "
            f"cluster sizes {sizes}, max enclosure width {max_w:.2e}"
        )
    print("  (octet decomposes as N(2) + Sigma(3) + Lambda(1) + Xi(2) = 8)\n")

    # (B) model GMO residual encloses 0.
    print("(B) Model GMO residual  2(N+Xi) - 3*Lambda - Sigma")
    r_model = certified_gmo_residual_model(broken)
    print(f"  certified residual = {_fmt(r_model)}  (must enclose 0)")
    print(f"  encloses 0: {bool(r_model.lower <= 0 <= r_model.upper)}\n")

    # (C) empirical certified checks.
    print("(C) Empirical certified checks (PDG masses with uncertainties)")
    r_data = gmo_residual_from_masses(
        PDG_OCTET["N"], PDG_OCTET["Sigma"], PDG_OCTET["Lambda"], PDG_OCTET["Xi"]
    )
    scale = 3 * PDG_OCTET["Lambda"][0] + PDG_OCTET["Sigma"][0]
    rel_lo = abs(float(r_data.lower)) / scale
    rel_hi = abs(float(r_data.upper)) / scale
    print(f"  GMO residual    = {_fmt(r_data)} MeV  (~{100*min(rel_lo,rel_hi):.2f}% of mass scale)")
    omega = certified_omega_prediction(PDG_DECUPLET["Sigma_star"], PDG_DECUPLET["Xi_star"])
    meas = PDG_DECUPLET["Omega"]
    print(f"  Omega^- predicted = {_fmt(omega)} MeV  (equal-spacing 2*Xi* - Sigma*)")
    print(f"  Omega^- measured  = {meas[0]:.2f} +/- {meas[1]:.2f} MeV")
    diff = abs(float(omega.midpoint()) - meas[0])
    print(f"  |prediction - measured| = {diff:.2f} MeV  (~{100*diff/meas[0]:.2f}%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
