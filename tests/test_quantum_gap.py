"""Tests for the unified Quantum Gap formula (quantumgap-0001).

The formula QG(O, floor) = lower(O) - floor is certified iff QG > 0. These tests pin
the algebra, the per-track constructors' reuse of certified kernels, the discharged
certificate having no holes, and the end-to-end report certifying every track.
"""
from __future__ import annotations

import numpy as np
import pytest

from gaugegap.quantum_gap import (
    QuantumGap,
    emit_quantum_gap_certificate,
    from_bound,
    from_fidelity,
    from_rate,
    from_spectrum,
    from_threshold,
    unified_gap_report,
)


def _qg(low, high, floor):
    return QuantumGap(
        observable="test", track="Test", enclosure_low=low, enclosure_high=high,
        floor=floor, claim_boundary="test boundary",
    )


def test_gap_is_low_minus_floor_and_certified_iff_positive():
    g = _qg(1.5, 1.7, 1.0)
    assert g.gap == pytest.approx(0.5)
    assert g.certified is True
    # A floor above the whole enclosure is not certified.
    assert _qg(1.5, 1.7, 1.6).certified is False
    # Exactly at the floor is not certified (strict).
    assert _qg(1.0, 1.2, 1.0).certified is False


def test_enclosure_ordering_is_enforced():
    with pytest.raises(ValueError):
        _qg(1.7, 1.5, 0.0)


def test_from_spectrum_gap_matches_dense_eigengap():
    # A diagonal matrix has an exactly known gap; the certified enclosure must bracket it.
    h = np.diag([0.0, 1.25, 3.0, 4.5])
    g = from_spectrum(h, observable="gap", track="GaugeGap", claim_boundary="finite")
    assert g.enclosure_low <= 1.25 <= g.enclosure_high
    assert g.certified is True


def test_from_threshold_fidelity_rate_bound_constructors():
    assert from_threshold(0.4, 0.6, threshold=0.1, observable="o", track="T",
                          claim_boundary="b").gap == pytest.approx(0.3)
    # 0.95 fidelity clears the 2/3 quantum-advantage floor.
    assert from_fidelity(0.95, claim_boundary="b").certified is True
    assert from_fidelity(0.6, claim_boundary="b").certified is False
    assert from_rate(0.42, observable="o", track="T", claim_boundary="b").certified is True
    assert from_bound(2.0, bound=1.0, observable="o", track="T",
                      claim_boundary="b").gap == pytest.approx(1.0)


def test_certificate_has_no_holes():
    lean, coq = emit_quantum_gap_certificate("unified", 1.0, 0.0)
    for text in (lean, coq):
        assert "sorry" not in text
        assert "Admitted" not in text
    assert "theorem quantum_gap_pos" in lean
    assert "Theorem quantum_gap_pos" in coq
    assert "linarith" in lean and "lra" in coq


def test_unified_report_certifies_every_track():
    rep = unified_gap_report()
    assert rep["n_rows"] >= 6
    assert rep["n_certified"] >= 6
    assert rep["all_certified"] is True
    tracks = {row["track"] for row in rep["rows"]}
    assert {"GaugeGap", "CurveRank", "FlowGap", "NetGap", "Limits"} <= tracks
    for row in rep["rows"]:
        # The reported gap is exactly low - floor for every row.
        assert row["gap"] == pytest.approx(row["enclosure_low"] - row["floor"])
        assert row["certified"] == (row["gap"] > 0.0)
