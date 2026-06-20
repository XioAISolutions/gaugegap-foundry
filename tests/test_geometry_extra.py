"""Tests for the deeper geometry extras: A-G Cartan/Dynkin, mirror pairs, reels."""
from __future__ import annotations

import importlib.util
import sys
import tempfile
from pathlib import Path
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.visualization.topology import (
    cartan_matrix, dynkin_diagram, cartan_determinant,
    fermat_quintic_hodge, mirror_threefold, is_mirror_pair,
)

_ATLAS = [("A", 4), ("B", 4), ("C", 4), ("D", 5), ("E", 6), ("E", 7),
          ("E", 8), ("F", 4), ("G", 2)]


class TestCartanAtlas(unittest.TestCase):
    def test_all_types_det_and_positive_definite(self):
        for (typ, n) in _ATLAS:
            d = dynkin_diagram(typ, n)
            self.assertEqual(d["determinant"], cartan_determinant(typ, n),
                             msg=f"{typ}{n}")
            self.assertEqual(d["determinant"], d["known_determinant"], msg=f"{typ}{n}")
            self.assertTrue(d["positive_definite"], msg=f"{typ}{n}")

    def test_cartan_diagonal_is_two(self):
        for (typ, n) in _ATLAS:
            C = cartan_matrix(typ, n)
            self.assertTrue((np.diag(C) == 2).all(), msg=f"{typ}{n}")
            self.assertEqual(C.shape, (n, n))

    def test_g2_triple_bond(self):
        d = dynkin_diagram("G", 2)
        self.assertEqual(d["bonds"][0]["mult"], 3)

    def test_invalid_types_raise(self):
        for bad in [("D", 3), ("E", 5), ("F", 5), ("G", 3)]:
            with self.assertRaises(ValueError):
                cartan_matrix(*bad)


class TestMirrorSymmetry(unittest.TestCase):
    def test_quintic_mirror(self):
        q = fermat_quintic_hodge()
        m = mirror_threefold(q)
        self.assertEqual(m.h[(1, 1)], 101)
        self.assertEqual(m.h[(2, 1)], 1)
        self.assertEqual(m.euler_characteristic(), 200)
        self.assertEqual(q.euler_characteristic(), -200)
        self.assertTrue(is_mirror_pair(q, m))
        self.assertTrue(is_mirror_pair(m, q))

    def test_double_mirror_is_identity(self):
        q = fermat_quintic_hodge()
        mm = mirror_threefold(mirror_threefold(q))
        self.assertEqual(mm.h[(1, 1)], q.h[(1, 1)])
        self.assertEqual(mm.h[(2, 1)], q.h[(2, 1)])


class TestExtraFigures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "scripts" / "generate_geometry_extra.py"
        spec = importlib.util.spec_from_file_location("geomextra", path)
        cls.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.mod)

    def test_animated_svg_has_smil_and_is_valid(self):
        import numpy as np
        p3 = np.array([[1.0, 0, -1], [0, 1, -1], [-1, 0, 1]])
        f2 = np.array([[0.5, 0.3], [-0.5, 0.3], [0.0, -0.6]])
        svg = self.mod.animated_flatten_svg(p3, f2, "t")
        self.assertIn("<animate", svg)
        self.assertIn("repeatCount=\"indefinite\"", svg)
        self.assertTrue(svg.startswith("<svg"))
        self.assertTrue(svg.rstrip().endswith("</svg>"))
        self.assertEqual(svg.count("<circle"), 3)

    def test_generates_all_files_deterministically(self):
        import sys as _sys
        outs = []
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            for d in (d1, d2):
                old = _sys.argv
                _sys.argv = ["prog", "--output-dir", d]
                try:
                    self.mod.main()
                finally:
                    _sys.argv = old
            files1 = sorted(p.name for p in Path(d1).glob("*"))
            # 2 reels + 9 dynkin + 1 mirror + 1 atlas json = 13
            self.assertEqual(len(files1), 13)
            for f in Path(d1).glob("*"):
                self.assertEqual(f.read_text(), (Path(d2) / f.name).read_text(),
                                 msg=f.name)


if __name__ == "__main__":
    unittest.main()
