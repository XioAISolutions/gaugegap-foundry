"""Establish ``certify.certify_spectrum`` as the canonical certify entry (roadmap §7.4).

There were three certify-adjacent surfaces (``certify.py``, ``curverank_certified``,
``rigorous/enclosure_certificate``). ``certify_spectrum`` is the general public API:
it builds enclosures from the shared rigorous kernel and *orchestrates* both formal
emitters. These tests pin that contract — soundness of the enclosures and that the
formal payloads match the dedicated emitters exactly — so the canonical path cannot
silently diverge from the modules it delegates to.
"""
from __future__ import annotations

import numpy as np

from gaugegap.certify import certify_spectrum
from gaugegap.curverank_operators import berry_keating_xp
from gaugegap.rigorous.curverank_formal_emit import discharged_separation_proof
from gaugegap.rigorous.enclosure_certificate import emit_enclosure_certificate

N_BASIS = 8


def _xp_matrix() -> np.ndarray:
    H = berry_keating_xp(N_BASIS)
    return (H + H.conj().T) / 2.0


def test_enclosures_are_sound_and_ascending():
    H = _xp_matrix()
    cert = certify_spectrum(H)
    eigenvalues = np.linalg.eigvalsh(H)
    # Every true eigenvalue lies inside at least one certified enclosure.
    for value in eigenvalues:
        assert any(lo - 1e-9 <= value <= hi + 1e-9 for (lo, hi) in cert.enclosures)
    # Enclosures are reported ascending by midpoint, with non-negative width.
    assert cert.midpoints == sorted(cert.midpoints)
    assert cert.max_width >= 0.0


def test_separation_formal_payload_matches_the_dedicated_emitter():
    H = _xp_matrix()
    cert = certify_spectrum(H, formal_family="xp", k_zeros=20, threshold=1.0)
    proof = discharged_separation_proof("xp", cert.n, k_zeros=20, threshold=1.0)
    assert cert.formal is not None
    assert cert.formal["kind"] == "separation_proof"
    assert cert.formal["lower_bound"] == proof.lower_bound
    assert cert.formal["separated"] == (proof.lower_bound > proof.threshold)
    assert cert.formal["lean4"] == proof.lean4


def test_generic_enclosure_certificate_matches_the_dedicated_emitter():
    H = _xp_matrix()
    cert = certify_spectrum(H, emit_formal=True, name="XpEight")
    expected = emit_enclosure_certificate(cert.enclosures, name="XpEight").to_dict()
    assert cert.formal is not None
    assert cert.formal["n"] == expected["n"]
    assert cert.formal["name"] == expected["name"]
    assert cert.formal["global_enclosure"] == expected["global_enclosure"]
    assert cert.formal["lean4"] == expected["lean4"]


def test_certificate_dict_carries_a_claim_boundary():
    cert = certify_spectrum(_xp_matrix())
    assert "Millennium Prize" in cert.to_dict()["claim_boundary"]
