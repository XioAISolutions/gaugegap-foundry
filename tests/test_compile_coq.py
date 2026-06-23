"""coqc compiles every emitted Coq certificate (skipped if Coq is absent)."""
import os
import shutil
import subprocess
import sys
import unittest

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

_HAVE_COQC = shutil.which("coqc") is not None


@unittest.skipUnless(_HAVE_COQC, "coqc not installed (Coq toolchain absent)")
class TestCompileCoq(unittest.TestCase):
    def test_all_coq_certificates_compile(self):
        proc = subprocess.run(
            [sys.executable, os.path.join(ROOT, "scripts", "compile_coq_certificates.py"),
             "--emit"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("compiled by coqc", proc.stdout)


class TestEmittersProduceCoq(unittest.TestCase):
    """Even without Coq, the emitters must produce hole-free Coq source."""

    def test_fresh_emitters_have_no_admitted(self):
        from compile_coq_certificates import _fresh_emitted_certs
        certs = _fresh_emitted_certs()
        self.assertGreaterEqual(len(certs), 11)
        for name, src in certs:
            self.assertIn("Qed.", src, name)
            self.assertNotIn("Admitted", src, name)


if __name__ == "__main__":
    unittest.main()
