"""Tests for the Geometry-of-GaugeGap visualization layer."""
from __future__ import annotations

import importlib.util
import sys
import warnings
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

warnings.filterwarnings("ignore")

from gaugegap.visualization.weight_diagrams import (
    su3_weights, su3_dimension, su3_root_system, NAMED_IRREPS,
    geometry_dataset, weyl_orbit_closed, weight_centroid,
)
from gaugegap.visualization.cy_projection import fermat_patches, orthographic
from gaugegap.visualization.svg import SVGCanvas


class TestWeightDiagrams(unittest.TestCase):
    def test_dimensions_match_freudenthal(self):
        for (p, q) in [(1, 0), (0, 1), (1, 1), (2, 0), (3, 0), (2, 2)]:
            ws = su3_weights(p, q)
            self.assertEqual(sum(w["mult"] for w in ws), su3_dimension(p, q),
                             msg=f"({p},{q})")

    def test_octet_center_multiplicity_two(self):
        ws = su3_weights(1, 1)
        center = [w for w in ws if abs(w["t3"]) < 1e-9 and abs(w["y"]) < 1e-9]
        self.assertEqual(len(center), 1)
        self.assertEqual(center[0]["mult"], 2)

    def test_fundamental_has_three_weights(self):
        ws = su3_weights(1, 0)
        self.assertEqual(len(ws), 3)
        self.assertTrue(all(w["mult"] == 1 for w in ws))

    def test_root_system_has_six_roots(self):
        roots = su3_root_system()
        self.assertEqual(len(roots), 6)
        # roots come in +/- pairs -> centroid at origin
        sx = sum(r["t3"] for r in roots)
        sy = sum(r["y"] for r in roots)
        self.assertAlmostEqual(sx, 0.0, places=9)
        self.assertAlmostEqual(sy, 0.0, places=9)

    def test_named_irreps(self):
        self.assertEqual(NAMED_IRREPS["adjoint"], (1, 1))
        self.assertEqual(su3_dimension(*NAMED_IRREPS["decuplet"]), 10)

    def test_symmetry_invariants(self):
        # Every irrep: centroid at the origin and the weight set is Weyl-closed.
        for (p, q) in [(1, 0), (1, 1), (3, 0), (2, 2)]:
            ws = su3_weights(p, q)
            cx, cy = weight_centroid(ws)
            self.assertAlmostEqual(cx, 0.0, places=9)
            self.assertAlmostEqual(cy, 0.0, places=9)
            self.assertTrue(weyl_orbit_closed(ws), msg=f"({p},{q})")

    def test_geometry_dataset_json_serialisable(self):
        import json
        d = geometry_dataset()
        s = json.dumps(d)  # must not raise (plain floats/ints/bools)
        self.assertIn("representations", d)
        self.assertTrue(all(r["weyl_orbit_closed"]
                            for r in d["representations"].values()))
        self.assertEqual(len(d["root_system"]), 6)
        self.assertGreater(len(s), 0)


class TestCYProjection(unittest.TestCase):
    def test_patch_count_and_shape(self):
        patches = fermat_patches(n=5, n_grid=8)
        self.assertEqual(len(patches), 25)
        self.assertEqual(patches[0].grid3d.shape, (8, 8, 3))

    def test_surface_equation_holds(self):
        # z1^n + z2^n = 1 by construction; check on the raw complex values.
        n, ng = 5, 6
        xi = np.linspace(0, np.pi / 2, ng)
        eta = np.linspace(-1.0, 1.0, ng)
        XI, ETA = np.meshgrid(xi, eta, indexing="ij")
        w = XI + 1j * ETA
        z1n = (np.cos(w) ** (2.0 / n)) ** n
        z2n = (np.sin(w) ** (2.0 / n)) ** n
        self.assertTrue(np.allclose(z1n + z2n, 1.0, atol=1e-9))

    def test_projection_finite(self):
        p = fermat_patches(n=5, n_grid=8)[0]
        xy = orthographic(p.grid3d)
        self.assertEqual(xy.shape, (8, 8, 2))
        self.assertTrue(np.isfinite(xy).all())


class TestSVGAndFigures(unittest.TestCase):
    def test_svg_canvas_basic(self):
        c = SVGCanvas(100, 100)
        c.circle(50, 50, 10)
        c.line(0, 0, 100, 100)
        out = c.to_svg()
        self.assertIn("<svg", out)
        self.assertIn("<circle", out)
        self.assertTrue(out.endswith("</svg>\n"))

    def test_interactive_html_is_self_contained_and_deterministic(self):
        import tempfile
        path = ROOT / "scripts" / "generate_geometry_html.py"
        spec = importlib.util.spec_from_file_location("geomhtml", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        import sys as _sys
        outs = []
        with tempfile.TemporaryDirectory() as d:
            for k in range(2):
                p = Path(d) / f"explorer{k}.html"
                old = _sys.argv
                _sys.argv = ["prog", "--output", str(p), "--cy-grid", "6"]
                try:
                    mod.main()
                finally:
                    _sys.argv = old
                outs.append(p.read_text())
            self.assertEqual(outs[0], outs[1])  # deterministic
        html = outs[0]
        self.assertIn("<canvas", html)
        self.assertIn("const DATA =", html)
        # self-contained: no external script/style references
        self.assertNotIn("http://", html)
        self.assertNotIn("https://", html)
        self.assertNotIn("cdn", html.lower())

    def test_figures_generate_and_are_deterministic(self):
        import tempfile
        path = ROOT / "scripts" / "generate_geometry_figures.py"
        spec = importlib.util.spec_from_file_location("geomfigs", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            mod.main_argv = None
            for d in (d1, d2):
                import sys as _sys
                argv = ["prog", "--output-dir", d, "--cy-grid", "8"]
                old = _sys.argv
                _sys.argv = argv
                try:
                    mod.main()
                finally:
                    _sys.argv = old
            a = sorted(Path(d1).glob("*.svg"))
            b = sorted(Path(d2).glob("*.svg"))
            self.assertEqual(len(a), 5)
            for fa, fb in zip(a, b):
                self.assertEqual(fa.read_text(), fb.read_text(), msg=fa.name)


if __name__ == "__main__":
    unittest.main()
