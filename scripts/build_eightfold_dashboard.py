#!/usr/bin/env python3
"""Build a self-contained HTML dashboard of the certified Eightfold-Way suite.

Renders every certified SU(3)-flavor result (mass relations, mixings, magnetic
moments, decay ratios, representation theory, weak sector) into one standalone
HTML page with the (I3, Y) weight diagrams embedded inline. No external assets,
no server required -- open the file in a browser.

CLAIM BOUNDARY: finite effective SU(3)-flavor phenomenology made rigorous with
interval arithmetic; not lattice QCD, no continuum/first-principles claim.
"""
from __future__ import annotations

import argparse
import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.eightfold import (  # noqa: E402
    PDG_DECUPLET,
    certified_axial_fd,
    certified_cabibbo_angle,
    certified_ckm_unitarity,
    certified_constituent_quark_masses,
    certified_hyperon_axial,
    certified_isospin_ratios,
    certified_moment_predictions,
    certified_moment_relations,
    certified_omega_prediction,
    certified_quark_moments,
    certified_relations_battery,
    certified_sigma_lambda_transition,
    certified_su3_decompositions,
    certified_vector_quark_content,
    decuplet_weight_diagram_svg,
    octet_weight_diagram_svg,
)


def _iv(iv) -> str:
    return f"[{float(iv.lower):.4f}, {float(iv.upper):.4f}]"


def _rows(results) -> str:
    out = []
    for r in results:
        cls = "zero" if r.encloses_zero else "nonzero"
        out.append(
            f"<tr><td>{html.escape(r.name)}</td>"
            f"<td class='num'>{_iv(r.residual)}</td>"
            f"<td class='num'>{r.rel_percent:.2f}%</td>"
            f"<td class='{cls}'>{'yes' if r.encloses_zero else 'no'}</td></tr>"
        )
    return "\n".join(out)


def _table(title, results, note="") -> str:
    note_html = f"<p class='note'>{html.escape(note)}</p>" if note else ""
    return (
        f"<h2>{html.escape(title)}</h2>{note_html}"
        "<table><thead><tr><th>relation</th><th>certified residual</th>"
        "<th>rel.</th><th>encloses 0?</th></tr></thead>"
        f"<tbody>{_rows(results)}</tbody></table>"
    )


def build_html() -> str:
    battery = certified_relations_battery()
    moments = certified_moment_predictions() + certified_moment_relations() + [
        certified_sigma_lambda_transition()
    ]
    weak = [certified_ckm_unitarity(), certified_axial_fd()] + certified_hyperon_axial()
    vector = certified_vector_quark_content()
    decomps = certified_su3_decompositions()

    cq = certified_constituent_quark_masses()
    q = certified_quark_moments()
    omega = certified_omega_prediction(PDG_DECUPLET["Sigma_star"], PDG_DECUPLET["Xi_star"])
    ang = certified_cabibbo_angle()

    ratios = "".join(
        f"<tr><td>{html.escape(n)}</td><td class='num'>{_iv(iv)}</td>"
        f"<td class='num'>{html.escape(s)}</td></tr>"
        for n, iv, s in certified_isospin_ratios()
    )

    derived = (
        "<h2>Derived certified quantities</h2><table><tbody>"
        f"<tr><td>constituent m_q</td><td class='num'>{_iv(cq['m_q'])} MeV</td></tr>"
        f"<tr><td>constituent m_s</td><td class='num'>{_iv(cq['m_s'])} MeV</td></tr>"
        f"<tr><td>m_s - m_q (decuplet spacing)</td><td class='num'>{_iv(cq['m_s_minus_m_q'])} MeV</td></tr>"
        f"<tr><td>Omega- prediction (2&middot;&Xi;*-&Sigma;*)</td><td class='num'>{_iv(omega)} MeV "
        f"(meas {PDG_DECUPLET['Omega'][0]:.2f})</td></tr>"
        f"<tr><td>quark moments &mu;_u, &mu;_d, &mu;_s</td><td class='num'>"
        f"{_iv(q['mu_u'])}, {_iv(q['mu_d'])}, {_iv(q['mu_s'])} &mu;_N</td></tr>"
        f"<tr><td>Cabibbo angle &theta;_C</td><td class='num'>"
        f"[{float(ang.lower):.3f}, {float(ang.upper):.3f}]&deg;</td></tr>"
        "</tbody></table>"
    )

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Certified Eightfold-Way Dashboard</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 980px; margin: 2rem auto;
          padding: 0 1rem; color: #1a1a1a; line-height: 1.4; }}
  h1 {{ border-bottom: 3px solid #2a4d9b; padding-bottom: .3rem; }}
  h2 {{ margin-top: 2rem; color: #2a4d9b; }}
  table {{ border-collapse: collapse; width: 100%; margin: .5rem 0 1rem; font-size: .92rem; }}
  th, td {{ border: 1px solid #ddd; padding: 5px 9px; text-align: left; }}
  th {{ background: #eef3ff; }}
  td.num {{ font-family: ui-monospace, monospace; text-align: right; white-space: nowrap; }}
  td.zero {{ color: #137333; font-weight: 600; }}
  td.nonzero {{ color: #b3261e; }}
  .note {{ color: #666; font-size: .85rem; margin: .2rem 0; }}
  .boundary {{ background: #fff8e1; border: 1px solid #f0d000; padding: .6rem 1rem;
               border-radius: 6px; font-size: .9rem; }}
  .figs {{ display: flex; gap: 1rem; flex-wrap: wrap; justify-content: center; }}
  .figs > div {{ border: 1px solid #eee; border-radius: 6px; padding: .3rem; }}
</style></head><body>
<h1>Certified Eightfold-Way / Gell-Mann&ndash;Okubo Dashboard</h1>
<p class="boundary"><strong>Claim boundary.</strong> A finite, effective SU(3)-flavor
mass-operator / phenomenology suite made rigorous with interval arithmetic. Every
residual below is a certified enclosure propagated from PDG inputs. This is
<strong>not</strong> lattice QCD and makes no continuum or first-principles claim.</p>

<h2>Weight diagrams (I&#8323;, Y)</h2>
<div class="figs"><div>{octet_weight_diagram_svg()}</div>
<div>{decuplet_weight_diagram_svg()}</div></div>

{_table("Mass-relation battery", battery)}
{derived}
{_table("Vector nonet: ideal-mixing tests", vector, "phi as s-sbar, omega as light-quark")}
{_table("Baryon magnetic moments (SU(6) quark model)", moments)}
<h2>Isospin decay ratios (parameter-free, exact)</h2>
<table><thead><tr><th>decay</th><th>certified ratio</th><th>exact</th></tr></thead>
<tbody>{ratios}</tbody></table>
{_table("SU(3) tensor decompositions (exact)", decomps, "product dim - sum of summand dims")}
{_table("Weak (Cabibbo) sector", weak)}
<p class="note">Generated by scripts/build_eightfold_dashboard.py &mdash; reproduce with
<code>python3 scripts/run_eightfold.py</code>.</p>
</body></html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(ROOT / "figures" / "eightfold_dashboard.html"))
    args = ap.parse_args()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_html())
    print(f"Wrote {out}  ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
