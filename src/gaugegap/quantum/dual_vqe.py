"""Optional SDP lower bound on the ground energy (dual-VQE style), cvxpy-gated.

E0 = max { t : H - t I >= 0 } is a semidefinite program whose optimum is exactly the
smallest eigenvalue. This module exposes that SDP as an optional cross-check on the
certified/Temple bounds. It is OPTIONAL: cvxpy is imported lazily and a clear error
is raised if it is absent (install the `[sdp]` extra).

Honest note: for a full finite Hermitian matrix this SDP returns E0 exactly and the
repo's interval kernel already provides a tighter *rigorous* lower bound; this is the
quantum-literature (dual-VQE) cross-check, not an upgrade.

CLAIM BOUNDARY: a numerical SDP value for a finite matrix; cross-check only.
"""
from __future__ import annotations

import numpy as np


def _require_cvxpy():
    try:
        import cvxpy  # noqa: F401
        return cvxpy
    except Exception as exc:  # pragma: no cover - optional dep
        raise RuntimeError(
            "dual_vqe needs cvxpy (optional). Install with: pip install "
            "'gaugegap-foundry[sdp]'  (or: pip install cvxpy)."
        ) from exc


def sdp_ground_energy_lower_bound(H: np.ndarray) -> float:
    """SDP lower bound on E0 via max{ t : H - t I >= 0 } (== E0 numerically)."""
    cp = _require_cvxpy()
    H = np.asarray((np.asarray(H) + np.asarray(H).conj().T) / 2.0)
    d = H.shape[0]
    t = cp.Variable()
    # H - t I is PSD; for complex H use the real symmetric embedding.
    if np.iscomplexobj(H) and np.linalg.norm(H.imag) > 1e-12:
        re, im = H.real, H.imag
        emb = np.block([[re, -im], [im, re]])
        M = emb - t * np.eye(2 * d)
    else:
        M = np.asarray(H.real) - t * np.eye(d)
    prob = cp.Problem(cp.Maximize(t), [M >> 0])
    prob.solve()
    return float(t.value)
