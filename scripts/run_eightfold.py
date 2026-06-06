#!/usr/bin/env python3
"""Certified Eightfold-Way / Gell-Mann-Okubo benchmark report.

Runs the full certified SU(3)-flavor battery:
  (A) certified octet spectrum + certified count of distinct mass levels;
  (B) the certified GMO residual of the model operator (encloses 0);
  (C) the certified relations battery from PDG masses-with-uncertainties --
      baryon-octet GMO, decuplet equal spacing, pseudoscalar GMO (quadratic),
      and the Coleman-Glashow EM relation -- each as a certified interval;
  (D) certified constituent quark masses and certified eta-eta' mixing;
  (E) Eightfold-Way weight-diagram figures (SVG).

CLAIM BOUNDARY: a finite SU(3)-flavor mass-operator (Gell-Mann-Okubo)
benchmark made rigorous with interval arithmetic; not a lattice-QCD or
continuum claim.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.eightfold import (  # noqa: E402
    PDG_DECUPLET,
    OctetModel,
    certified_constituent_quark_masses,
    certified_distinct_levels,
    certified_eta_mixing,
    certified_gmo_residual_model,
    certified_octet_spectrum,
    certified_omega_prediction,
    certified_relations_battery,
    decuplet_weight_diagram_svg,
    octet_weight_diagram_svg,
)


def _fmt(iv) -> str:
    return f"[{float(iv.lower):.4f}, {float(iv.upper):.4f}]"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--figures-dir", default=str(ROOT / "figures"))
    args = ap.parse_args()

    print("# Certified Eightfold-Way / Gell-Mann-Okubo benchmark\n")

    # (A) certified spectrum + distinct-level count.
    print("(A) Octet mass operator -- certified multiplet structure")
    for label, model in (("SU(3) limit (b=c=0)", OctetModel(b=0.0, c=0.0)),
                         ("octet breaking", OctetModel())):
        enc = certified_octet_spectrum(model)
        clusters = certified_distinct_levels(enc)
        print(
            f"  {label:<22}: {len(clusters)} certified-distinct level(s), "
            f"cluster sizes {[len(c) for c in clusters]}"
        )
    print("  (octet = N(2) + Lambda(1) + Sigma(3) + Xi(2) = 8)\n")

    # (B) model GMO residual encloses 0.
    r_model = certified_gmo_residual_model(OctetModel())
    print("(B) Model GMO residual  2(N+Xi) - 3*Lambda - Sigma")
    print(f"  certified residual = {_fmt(r_model)}  (encloses 0: {r_model.lower <= 0 <= r_model.upper})\n")

    # (C) certified relations battery.
    print("(C) Certified SU(3) relations battery (PDG masses with uncertainties)")
    print(f"  {'relation':<46} {'certified residual':>24} {'rel%':>7}  0?")
    print("  " + "-" * 86)
    for r in certified_relations_battery():
        print(
            f"  {r.name:<46} {_fmt(r.residual):>24} {r.rel_percent:>6.2f}%  "
            f"{'Y' if r.encloses_zero else 'n'}"
        )
    print()

    # (D) constituent quark masses + eta-eta' mixing.
    print("(D) Derived certified quantities")
    cq = certified_constituent_quark_masses()
    print(f"  constituent m_q = {_fmt(cq['m_q'])} MeV,  m_s = {_fmt(cq['m_s'])} MeV")
    print(f"  m_s - m_q       = {_fmt(cq['m_s_minus_m_q'])} MeV  (sets decuplet spacing)")
    omega = certified_omega_prediction(PDG_DECUPLET["Sigma_star"], PDG_DECUPLET["Xi_star"])
    print(f"  Omega^- predicted = {_fmt(omega)} MeV  vs measured "
          f"{PDG_DECUPLET['Omega'][0]:.2f}")
    mix = certified_eta_mixing()
    t_sq = mix["t_sq"]
    print(f"  eta-eta' mixing t^2 = {_fmt(t_sq)} MeV^4  "
          f"(t^2 > 0 consistent: {t_sq.lower > 0})\n")

    # (E) weight-diagram figures.
    figs = Path(args.figures_dir)
    figs.mkdir(parents=True, exist_ok=True)
    (figs / "octet_weight_diagram.svg").write_text(octet_weight_diagram_svg())
    (figs / "decuplet_weight_diagram.svg").write_text(decuplet_weight_diagram_svg())
    print(f"(E) Wrote weight diagrams to {figs}/octet_weight_diagram.svg, "
          f"decuplet_weight_diagram.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
