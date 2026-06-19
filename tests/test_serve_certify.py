"""Tests for the certify HTTP service's pure request handler."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _load():
    path = ROOT / "scripts" / "serve_certify.py"
    spec = importlib.util.spec_from_file_location("serve_certify", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestCertifyRequest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = _load()

    def test_diagonal_matrix(self):
        out = self.m.certify_request({"matrix": [[2.0, 0.0], [0.0, 3.0]]})
        self.assertEqual(out["n"], 2)
        encl = out["enclosures"]
        self.assertLessEqual(encl[0][0], 2.0)
        self.assertLessEqual(2.0, encl[0][1])
        self.assertLessEqual(encl[1][0], 3.0)
        self.assertLessEqual(3.0, encl[1][1])

    def test_emit_formal(self):
        out = self.m.certify_request({"matrix": [[1.0, 0.0], [0.0, 4.0]],
                                      "emit_formal": True})
        self.assertEqual(out["formal"]["kind"], "spectral_enclosure_certificate")

    def test_missing_matrix(self):
        with self.assertRaises(ValueError):
            self.m.certify_request({})

    def test_non_square(self):
        with self.assertRaises(ValueError):
            self.m.certify_request({"matrix": [[1.0, 2.0, 3.0]]})

    def test_too_large(self):
        n = self.m.MAX_DIM + 1
        with self.assertRaises(ValueError):
            self.m.certify_request({"matrix": [[0.0] * n for _ in range(n)]})


if __name__ == "__main__":
    unittest.main()
