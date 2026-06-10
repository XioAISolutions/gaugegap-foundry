"""Deterministic seeding for reproducible stochastic computations (issue #12, A6).

A single place to obtain a seeded NumPy ``Generator`` so that every stochastic
routine in the project can be made bit-for-bit reproducible. Routines should
accept a ``seed`` (or an explicit ``rng``) and call :func:`make_rng` instead of
touching the global ``numpy.random`` state -- global seeding (e.g.
``np.random.seed(42)``) is a footgun that silently couples unrelated code.

A default seed is used when none is given; it can be overridden process-wide with
the ``GAUGEGAP_SEED`` environment variable, so a whole run is reproducible from
one knob.
"""
from __future__ import annotations

import os

import numpy as np

DEFAULT_SEED = 1234


def default_seed() -> int:
    """The default seed, overridable via the GAUGEGAP_SEED environment variable."""
    env = os.environ.get("GAUGEGAP_SEED")
    if env:
        try:
            return int(env)
        except ValueError:
            pass
    return DEFAULT_SEED


def make_rng(seed: int | np.random.Generator | None = None) -> np.random.Generator:
    """Return a NumPy ``Generator``.

    - ``None``  -> a fresh generator seeded with :func:`default_seed` (reproducible);
    - ``int``   -> a fresh generator seeded with that value;
    - ``Generator`` -> returned unchanged (lets callers thread an existing rng).
    """
    if isinstance(seed, np.random.Generator):
        return seed
    if seed is None:
        seed = default_seed()
    return np.random.default_rng(int(seed))


def child_seeds(seed: int, n: int) -> list[int]:
    """Derive ``n`` independent, reproducible child seeds from a parent seed.

    Uses NumPy's SeedSequence spawning so parallel/independent sub-tasks get
    statistically independent streams that are still fully determined by the
    parent seed.
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    seq = np.random.SeedSequence(int(seed))
    return [int(child.generate_state(1)[0]) for child in seq.spawn(n)]
