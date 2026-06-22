"""Tests for sonification & the sampling limit (Nyquist / aliasing)."""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gaugegap.quantum.sonification import (
    alias_frequency,
    analyze_sonification,
    demo_datasets,
    nyquist_frequency,
    nyquist_rate,
    power_spectrum,
    sonify,
    spectral_similarity,
)


class TestSonification(unittest.TestCase):
    def test_nyquist_and_rate(self):
        self.assertEqual(nyquist_frequency(8000.0), 4000.0)
        self.assertEqual(nyquist_rate(2000.0), 4000.0)

    def test_aliasing_fold(self):
        # 6000 Hz sampled at 8000 Hz aliases to 2000 Hz; in-band tone is unchanged
        self.assertAlmostEqual(alias_frequency(6000.0, 8000.0), 2000.0, places=6)
        self.assertAlmostEqual(alias_frequency(1500.0, 8000.0), 1500.0, places=6)
        # the fold always lands in [0, Nyquist]
        for f in (4100.0, 5200.0, 7900.0, 9000.0):
            self.assertLessEqual(alias_frequency(f, 8000.0), 4000.0 + 1e-9)

    def test_self_similarity_is_one(self):
        a, _ = demo_datasets(seed=1)
        sa = sonify(a, sample_rate=8000.0)
        self.assertAlmostEqual(spectral_similarity(sa, sa, 8000.0), 1.0, places=6)

    def test_unrelated_similarity_is_spurious(self):
        # independent datasets still score non-negligible spectral similarity
        r = analyze_sonification(seed=0)
        self.assertGreater(r.unrelated_similarity, 0.1)
        self.assertLess(r.unrelated_similarity, r.self_similarity)
        self.assertTrue(r.similarity_is_spurious)

    def test_sonify_length_and_band(self):
        a, _ = demo_datasets(seed=2, n=10)
        sig = sonify(a, sample_rate=8000.0, dur_per_point=0.03)
        self.assertEqual(sig.size, 10 * int(8000.0 * 0.03))
        # energy concentrated within the chosen band
        freqs, p = power_spectrum(sig, 8000.0)
        peak = freqs[int(np.argmax(p))]
        self.assertLessEqual(peak, 2200.0)

    def test_certificate_hole_free(self):
        r = analyze_sonification()
        self.assertNotIn("sorry", r.lean4)
        self.assertNotIn("admit", r.lean4.lower())
        self.assertNotIn("Admitted", r.coq)
        self.assertIn("aliasing_fold", r.lean4)
        self.assertIn("aliasing_fold", r.coq)


if __name__ == "__main__":
    unittest.main()
