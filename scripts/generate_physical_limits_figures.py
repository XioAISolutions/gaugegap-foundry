#!/usr/bin/env python3
"""Generate the synthesis figures for the physical-limits web.

Produces (deterministic, dependency-free SVG + a self-contained HTML gallery):
  * web.svg      -- the unifying diagram: four currencies (energy, time,
                    information, geometry) as nodes, the certified phenomena as the
                    edges/faces connecting them, each labelled with its certified
                    inequality.
  * ladder.svg   -- a certificate "ladder": the machine-checked inequalities
                    stacked as a one-glance reference card.
  * index.html   -- a self-contained explainer embedding the web, the ladder, and
                    every module's own result figure with narrative captions.

CLAIM BOUNDARY: these are explanatory figures for finite-system / semiclassical
demonstrations of established bounds; no new claims. Not a continuum/Millennium claim.
"""
from __future__ import annotations
import argparse, shutil, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; SRC = ROOT / "src"
if str(SRC) not in sys.path: sys.path.insert(0, str(SRC))
from gaugegap.visualization.svg import SVGCanvas

# currency palette
C_ENERGY = "#f0c674"     # gold
C_TIME = "#58a6ff"       # blue
C_INFO = "#7ee787"       # green
C_GEOM = "#d2a8ff"       # purple
C_EDGE = "#8b949e"
C_TXT = "#e6edf3"
C_MUTED = "#8b949e"

# The web members: (name, inequality, currencies, color)
MEMBERS = [
    ("Quantum speed limit", "t ≥ τ_QSL", "time ↔ energy", C_TIME),
    ("Temporal double slit", "Δω = 2π/Δt,  σ_tσ_ω ≥ ½",
     "time ↔ frequency", C_TIME),
    ("Sonification / sampling", "0 < f_s − f < f_s/2  (aliasing fold)",
     "time ↔ frequency", C_TIME),
    ("Ergotropy / passivity", "0 ≤ W ≤ ⟨H⟩ − E₀",
     "work ↔ entropy", C_ENERGY),
    ("Decoherence / branching", "1 ≤ N_eff ≤ d", "information", C_INFO),
    ("Landauer's principle", "W_erase ≥ k_B T ln 2", "info ↔ energy", C_INFO),
    ("Bekenstein bound", "S ≤ 2π R E", "info ↔ energy ↔ geometry", C_GEOM),
    ("Alcubierre energy cond.", "ρ ≤ 0  (needs neg. energy)",
     "energy ↔ geometry", C_GEOM),
    ("Cherenkov cone", "cos θc = 1/(nβ),  β > 1/n",
     "velocity ↔ geometry", C_GEOM),
    ("Lieb–Robinson cone", "x(t) ≤ v_LR·t + ξ", "information ↔ time", C_INFO),
    ("Compton–Schwarzschild", "R² ≥ R_s·λ_C = 2 l_P²",
     "mass ↔ geometry", C_GEOM),
    ("Quantum Zeno", "survival ≥ 1 − (ΔE·T)²/N → 1",
     "measurement ↔ time", C_TIME),
]

# module result SVGs to pull into the gallery: (results path, caption)
GALLERY = [
    ("entanglement-dynamics/entanglement_buildup.svg",
     "Entanglement build-up S(t): 0 → ln 2 over a finite time."),
    ("entanglement-speed-limit/qsl_floor_vs_coupling.svg",
     "Quantum speed-limit floor ∝ 1/coupling; the exchange evolution saturates it."),
    ("temporal-double-slit/spectral_fringes.svg",
     "Time diffraction: two time slits → fringes in the frequency spectrum."),
    ("decoherence-branching/decoherence_branching.svg",
     "Decoherence: coherence → 0, effective branches N_eff → d."),
    ("ergotropy/extracted_work.svg",
     "Ergotropy: cumulative extracted work saturates — no perpetual motion."),
    ("alcubierre-warp/energy_density_profile.svg",
     "Alcubierre metric: energy density ≤ 0 — the warp bubble needs negative energy."),
    ("cherenkov/cherenkov_cone.svg",
     "Cherenkov: wavefronts pile into a cone, cos θc = 1/(nβ) (local speed limit)."),
    ("lieb-robinson/light_cone.svg",
     "Lieb–Robinson: the information front stays inside a linear light cone v_LR·t."),
]


def _node(c, x, y, label, color, r=46):
    c.circle(x, y, r, fill="#0b0e14", stroke=color, stroke_width=2.5)
    c.text(x, y + 5, label, size=15, fill=color)


def _edge_label(c, x, y, lines, color):
    for i, (txt, size, fill) in enumerate(lines):
        c.text(x, y + i * 15, txt, size=size, fill=fill)


def build_web(path: Path):
    W, H = 920, 720
    c = SVGCanvas(W, H)
    # nodes (diamond): Energy top, Geometry bottom, Time left, Information right
    E = (460, 150); G = (460, 600); T = (175, 375); I = (745, 375)
    c.text(W / 2, 44, "The web of physical limits", size=22, fill=C_TXT)
    c.text(W / 2, 70, f"four currencies · {len(MEMBERS)} certified phenomena", size=13,
           fill=C_MUTED)

    # Bekenstein face: the Energy-Information-Geometry triangle (translucent)
    c.polygon([E, I, G], fill=C_GEOM, stroke="none", opacity=0.08)
    c.text((E[0] + I[0] + G[0]) / 3 + 40, (E[1] + I[1] + G[1]) / 3 + 4,
           "Bekenstein", size=12, fill=C_GEOM)
    c.text((E[0] + I[0] + G[0]) / 3 + 40, (E[1] + I[1] + G[1]) / 3 + 19,
           "S ≤ 2πRE", size=11, fill=C_MUTED)

    # edges
    c.line(*T, *E, stroke=C_TIME, stroke_width=2.0, opacity=0.8)        # time-energy
    c.line(*E, *I, stroke=C_ENERGY, stroke_width=2.0, opacity=0.8)      # energy-info
    c.line(*E, *G, stroke=C_GEOM, stroke_width=2.0, opacity=0.8)        # energy-geom
    c.line(*I, *G, stroke=C_GEOM, stroke_width=1.2, opacity=0.4)        # info-geom (Bek)

    # edge labels
    _edge_label(c, 300, 238, [("QSL:  t ≥ τ_QSL", 12, C_TIME),
                              ("time slits:  Δω = 2π/Δt", 11, C_MUTED)],
                C_TIME)
    _edge_label(c, 625, 238, [("ergotropy:  0 ≤ W ≤ ⟨H⟩−E₀", 12, C_ENERGY),
                              ("Landauer:  ≥ k_B T ln 2", 11, C_MUTED)], C_ENERGY)
    _edge_label(c, 505, 380, [("warp:  ρ ≤ 0", 12, C_GEOM)], C_GEOM)

    # decoherence: internal to Information (a small self-loop on the INFO node)
    c.circle(I[0] + 52, I[1] - 30, 16, fill="none", stroke=C_INFO,
             stroke_width=1.4, opacity=0.7)
    _edge_label(c, I[0], I[1] + 72, [("decoherence:", 11, C_INFO),
                                     ("1 ≤ N_eff ≤ d", 11, C_MUTED)], C_INFO)

    # nodes on top
    _node(c, *E, "ENERGY", C_ENERGY)
    _node(c, *G, "GEOMETRY", C_GEOM)
    _node(c, *T, "TIME", C_TIME)
    _node(c, *I, "INFO", C_INFO)

    c.text(W / 2, H - 26,
           "every edge is a trade-off; every label a machine-checked inequality",
           size=12, fill=C_MUTED)
    c.text(W / 2, H - 10,
           "finite-system / semiclassical demonstrations — not continuum claims",
           size=10, fill=C_MUTED)
    c.write(path)


def build_ladder(path: Path):
    W = 920; row_h = 70; H = 120 + row_h * len(MEMBERS)
    c = SVGCanvas(W, H)
    c.text(W / 2, 48, "Certificate ladder", size=22, fill=C_TXT)
    c.text(W / 2, 74, f"{len(MEMBERS)} machine-checked inequalities (discharged Lean 4 / Coq)",
           size=13, fill=C_MUTED)
    y0 = 110
    for i, (name, ineq, cur, color) in enumerate(MEMBERS):
        y = y0 + i * row_h
        c.line(60, y, W - 60, y, stroke="#222831", stroke_width=1.0)
        c.circle(84, y + 34, 7, fill=color, stroke="none")
        c.text(104, y + 30, name, size=15, fill=C_TXT, anchor="start")
        c.text(104, y + 50, cur, size=11, fill=C_MUTED, anchor="start")
        c.text(W - 80, y + 40, ineq, size=16, fill=color, anchor="end")
    c.line(60, y0 + row_h * len(MEMBERS), W - 60, y0 + row_h * len(MEMBERS),
           stroke="#222831", stroke_width=1.0)
    c.write(path)


def build_mass_radius(path: Path):
    """The cosmic mass-radius diagram: every object lives in the wedge to the right of
    BOTH the Schwarzschild line (forbidden by gravity) and the Compton line (forbidden
    by quantum uncertainty); the two cross at the Planck point."""
    import math

    from gaugegap.relativity.compton_schwarzschild import (
        NAMED_OBJECTS,
        compton_wavelength,
        planck_length,
        planck_mass,
        schwarzschild_radius,
    )

    W, H = 920, 720
    c = SVGCanvas(W, H)
    # plot box in log10 space: x = log10(radius/m), y = log10(mass/kg)
    PX0, PX1, PY0, PY1 = 92, W - 40, H - 70, 96
    xlo, xhi = -37.0, 28.0      # radius decades
    ylo, yhi = -34.0, 40.0      # mass decades

    def sx(logr):
        return PX0 + (logr - xlo) / (xhi - xlo) * (PX1 - PX0)

    def sy(logm):
        return PY0 + (logm - ylo) / (yhi - ylo) * (PY1 - PY0)

    c.text(W / 2, 44, "The cosmic mass–radius diagram", size=22, fill=C_TXT)
    c.text(W / 2, 70, "every object sits between two certified limits — they meet at "
           "the Planck point", size=13, fill=C_MUTED)

    # boundary lines, sampled from the real formulae (log-log → straight lines)
    sch = [(sx(math.log10(schwarzschild_radius(10.0 ** lm))), sy(lm))
           for lm in (ylo, yhi)]
    com = [(sx(math.log10(compton_wavelength(10.0 ** lm))), sy(lm))
           for lm in (ylo, yhi)]

    # forbidden-by-gravity wedge (left of Schwarzschild, upper region): shade
    c.polygon([(sx(xlo), sy(yhi)), sch[1], sch[0], (sx(xlo), sy(ylo))],
              fill="#8b2f2f", stroke="none", opacity=0.18)
    # forbidden-by-quantum wedge (left of Compton, lower region): shade
    c.polygon([(sx(xlo), sy(ylo)), com[1], com[0], (sx(xlo), sy(yhi))],
              fill="#2f4b8b", stroke="none", opacity=0.16)

    c.line(*sch[0], *sch[1], stroke="#ff7b72", stroke_width=2.4)
    c.line(*com[0], *com[1], stroke=C_TIME, stroke_width=2.4)

    # Planck point (crossing) and its length floor
    lp = planck_length()
    mp = planck_mass()
    px, py = sx(math.log10(lp * math.sqrt(2))), sy(math.log10(mp / math.sqrt(2)))
    c.circle(px, py, 6, fill="#f0c674", stroke="#0b0e14", stroke_width=1.5)
    c.text(px + 10, py + 4, "Planck point  (√2 l_P)", size=12, fill=C_ENERGY,
           anchor="start")

    # axis frame + decade ticks
    c.line(PX0, PY0, PX1, PY0, stroke=C_EDGE, stroke_width=1.2)
    c.line(PX0, PY0, PX0, PY1, stroke=C_EDGE, stroke_width=1.2)
    for lr in range(-36, 28, 8):
        c.line(sx(lr), PY0, sx(lr), PY0 + 5, stroke=C_EDGE, stroke_width=1.0)
        c.text(sx(lr), PY0 + 18, f"1e{lr}", size=10, fill=C_MUTED)
    for lm in range(-32, 40, 8):
        c.line(PX0 - 5, sy(lm), PX0, sy(lm), stroke=C_EDGE, stroke_width=1.0)
        c.text(PX0 - 8, sy(lm) + 3, f"1e{lm}", size=10, fill=C_MUTED, anchor="end")
    c.text(W / 2, H - 30, "radius  [m]", size=13, fill=C_TXT)

    # named objects
    for name, m, r in NAMED_OBJECTS:
        x, y = sx(math.log10(r)), sy(math.log10(m))
        c.circle(x, y, 3.4, fill=C_INFO, stroke="none")
        c.text(x + 7, y + 3, name, size=10, fill=C_TXT, anchor="start")

    # boundary labels
    c.text(sx(-30), sy(28), "forbidden by gravity", size=14, fill="#ff7b72")
    c.text(sx(-30), sy(30.5), "(R < R_s : black hole)", size=10, fill=C_MUTED)
    c.text(sx(-22), sy(-30), "forbidden by quantum uncertainty", size=13, fill=C_TIME)
    c.text(sx(-22), sy(-32.2), "(R < λ_C)", size=10, fill=C_MUTED)
    c.text(sx(14), sy(2), "allowed", size=15, fill=C_INFO)

    c.text(W / 2, H - 12,
           "R_s·λ_C = 2 l_P² for every mass — a machine-checked identity", size=10,
           fill=C_MUTED)
    c.write(path)


def build_gallery_html(path: Path, copied):
    panels = "".join(
        f'<figure><img src="{name}" alt="{cap}"/>'
        f'<figcaption>{cap}</figcaption></figure>\n'
        for name, cap in copied)
    ladder_rows = "".join(
        f"<tr><td><span class='dot' style='background:{col}'></span>{n}</td>"
        f"<td class='cur'>{cur}</td><td class='ineq' style='color:{col}'>{iq}</td></tr>"
        for n, iq, cur, col in MEMBERS)
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>The web of physical limits</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ background:#0b0e14; color:#e6edf3; font-family:-apple-system,Segoe UI,
         Roboto,sans-serif; margin:0; padding:0 0 64px; }}
  header {{ padding:48px 24px 8px; text-align:center; }}
  h1 {{ font-size:30px; margin:0; }} h2 {{ color:#7ee787; margin-top:48px; }}
  .sub {{ color:#8b949e; }}
  main {{ max-width:1000px; margin:0 auto; padding:0 24px; }}
  .hero {{ text-align:center; }} .hero img {{ max-width:100%; height:auto; }}
  table {{ width:100%; border-collapse:collapse; margin:16px 0; font-size:14px; }}
  td {{ border-bottom:1px solid #222831; padding:10px 8px; }}
  .cur {{ color:#8b949e; }} .ineq {{ font-family:monospace; text-align:right; }}
  .dot {{ display:inline-block; width:10px; height:10px; border-radius:50%;
          margin-right:10px; }}
  .gallery {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr));
              gap:20px; }}
  figure {{ margin:0; background:#11151c; border:1px solid #222831; border-radius:10px;
            padding:12px; }}
  figure img {{ width:100%; height:auto; border-radius:6px; }}
  figcaption {{ color:#8b949e; font-size:13px; margin-top:8px; }}
  .note {{ color:#8b949e; font-size:13px; border-left:3px solid #f0c674;
           padding:8px 14px; margin:24px 0; background:#11151c; }}
</style></head>
<body>
<header>
  <h1>The web of physical limits</h1>
  <p class="sub">"Mind-blowing physics" reduced to its rigorous, certifiable
  cores &mdash; a family of fundamental bounds shown to be one structure.</p>
</header>
<main>
  <section class="hero"><img src="web.svg" alt="web of physical limits"/></section>
  <p>Each reel made an extraordinary claim. Stripped of the clickbait, each leaves a
  genuine, finite, exactly computable statement: a <strong>trade-off inequality</strong>
  among four currencies &mdash; <b>energy</b>, <b>time</b>, <b>information/entropy</b>,
  and <b>geometry</b>. Two keystones (Landauer, Bekenstein) connect the quantum side to
  thermodynamics and to geometry, closing the web.</p>

  <h2>The certificate ladder</h2>
  <p class="sub">Every label above is a discharged Lean&nbsp;4 / Coq inequality
  (single labelled trust input, no holes).</p>
  <table><tbody>{ladder_rows}</tbody></table>
  <p class="hero"><img src="ladder.svg" alt="certificate ladder"/></p>

  <h2>The cosmic mass–radius diagram</h2>
  <p class="sub">The whole web has a global shape. Plot every object by mass and size:
  the lower-left is sealed off by two certified limits — the <b style="color:#ff7b72">
  Schwarzschild radius</b> (pack tighter and you are a black hole) and the
  <b style="color:#58a6ff">Compton wavelength</b> (localize tighter and the quantum
  vacuum pair-produces). They cross at the <b style="color:#f0c674">Planck point</b>,
  and the identity <code>R_s·λ_C = 2 ℓ_P²</code> holds for <em>every</em> mass — a
  machine-checked inequality (<code>R² ≥ R_s·λ_C</code>).</p>
  <p class="hero"><img src="mass_radius.svg" alt="cosmic mass-radius diagram"/></p>

  <h2>The phenomena, one figure each</h2>
  <div class="gallery">{panels}</div>

  <div class="note">Claim boundary: finite-system / semiclassical demonstrations of
  established physical bounds, each bracketed or machine-checked. Not
  continuum/Yang&ndash;Mills/Millennium claims; not a buildable warp drive or
  free-energy device. Dependency-light (numpy); deterministic SVG.</div>
</main>
</body></html>
"""
    path.write_text(html, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--output-dir", type=Path, default=ROOT / "figures" / "physical-limits")
    args = ap.parse_args()
    out = args.output_dir; out.mkdir(parents=True, exist_ok=True)

    build_web(out / "web.svg")
    build_ladder(out / "ladder.svg")
    build_mass_radius(out / "mass_radius.svg")

    copied = []
    for rel, cap in GALLERY:
        src = ROOT / "results" / rel
        dst_name = rel.replace("/", "__")
        if src.exists():
            shutil.copyfile(src, out / dst_name)
            copied.append((dst_name, cap))
    build_gallery_html(out / "index.html", copied)

    print(f"Wrote web.svg, ladder.svg, mass_radius.svg, index.html "
          f"(+ {len(copied)} module figures) to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
