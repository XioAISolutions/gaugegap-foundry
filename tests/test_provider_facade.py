"""Pin the unified provider facade contract (roadmap §7.3).

``providers.get_provider`` is the single entry point for every hardware adapter.
These tests lock that contract: each declared provider resolves to a
``QuantumProvider`` subclass, credential checks are side-effect-free and return a
bool without credentials, and an unknown provider fails closed.
"""
from __future__ import annotations

import pytest

from gaugegap.providers import QuantumProvider, get_provider

# (provider name, a valid backend for that provider)
PROVIDERS = (
    ("quantinuum", "H2-1E"),
    ("ibm", "aer_simulator"),
    ("braket", "braket_ahs"),
    ("ionq", "ionq_simulator"),
)


@pytest.mark.parametrize("name,backend", PROVIDERS)
def test_each_provider_resolves_to_the_shared_interface(name, backend):
    provider = get_provider(name, backend_name=backend)
    assert isinstance(provider, QuantumProvider)


@pytest.mark.parametrize("name,backend", PROVIDERS)
def test_credential_check_is_safe_without_credentials(name, backend):
    provider = get_provider(name, backend_name=backend)
    # Must not raise and must return a bool when no credentials are configured.
    assert isinstance(provider.check_credentials(), bool)


def test_provider_name_is_case_insensitive():
    assert isinstance(get_provider("IBM", backend_name="aer_simulator"), QuantumProvider)


def test_unknown_provider_fails_closed():
    with pytest.raises(ValueError, match="Unknown provider"):
        get_provider("not-a-provider", backend_name="emulator")
