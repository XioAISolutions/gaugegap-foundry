"""Regression guard for the canonical Hamiltonian factory (roadmap §7.2).

The factory normalizes construction across the finite gauge models. These tests
pin two contracts so a future de-duplication cannot silently drift:

1. The factory matrix is bit-identical to the legacy builder it delegates to.
2. ``HamiltonianArtifact.digest()`` is deterministic across rebuilds.

They also confirm the finite-reference models are Hermitian under the factory's
own audit and that unknown models fail closed.
"""
from __future__ import annotations

import numpy as np
import pytest

from gaugegap.hamiltonian_factory import (
    build_and_audit,
    build_hamiltonian,
    registered_models,
)


def test_z2_plaquette_matches_legacy_builder_bit_for_bit():
    from gaugegap.models.z2_plaquette import hamiltonian_dense

    params = dict(n_plaquettes=2, plaquette_coupling=1.0, transverse_field=0.2)
    artifact = build_hamiltonian("z2-plaquette", **params)
    legacy = np.asarray(hamiltonian_dense(**params), dtype=np.complex128)
    assert np.array_equal(artifact.matrix, legacy)


def test_u1_plaquette_matches_legacy_builder_bit_for_bit():
    from gaugegap.gaugegap_u1 import u1_plaquette_hamiltonian

    params = dict(n_links=2, g_electric=1.0, g_magnetic=0.5, truncation=1)
    artifact = build_hamiltonian("u1-plaquette", **params)
    legacy = np.asarray(u1_plaquette_hamiltonian(**params), dtype=np.complex128)
    assert np.array_equal(artifact.matrix, legacy)


def test_su2_prototype_matches_legacy_lattice_bit_for_bit():
    from gaugegap.gaugegap_su2_pure import SU2PureGaugeConfig, SU2PureGaugeLattice

    params = dict(nx=2, ny=2, g_electric=1.0, g_magnetic=1.0, j_max=0.5, boundary="periodic")
    artifact = build_hamiltonian("su2-pure-prototype", **params)
    legacy = np.asarray(
        SU2PureGaugeLattice(SU2PureGaugeConfig(**params)).hamiltonian_dense(),
        dtype=np.complex128,
    )
    assert np.array_equal(artifact.matrix, legacy)


@pytest.mark.parametrize("model_id", registered_models())
def test_digest_is_deterministic_across_rebuilds(model_id):
    first = build_hamiltonian(model_id)
    second = build_hamiltonian(model_id)
    assert first.digest() == second.digest()
    assert first.matrix.shape[0] == first.matrix.shape[1]
    assert first.implementation_status


@pytest.mark.parametrize("model_id", ("z2-plaquette", "u1-plaquette"))
def test_finite_reference_models_are_hermitian(model_id):
    _, audit = build_and_audit(model_id)
    assert audit.square
    assert audit.finite
    assert audit.hermitian


def test_unknown_model_fails_closed():
    with pytest.raises(ValueError, match="unknown model"):
        build_hamiltonian("not-a-model")
