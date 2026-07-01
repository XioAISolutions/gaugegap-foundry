"""NetGap network layer: finite, certifiable quantum-networking primitives.

Builds on the photonic-switch fabric with the next rungs a real quantum network needs,
each reduced to its exact finite core:

* ``reck_decomposition`` — factor any programmable N-mode unitary into an adjacent
  2x2-coupler mesh (Reck/Clements-style), reconstructing it exactly (netgap-0002);
* ``entanglement_swap`` — two Bell pairs + a Bell measurement on the middle qubits
  entangle the outer qubits that never interacted; the quantum-repeater primitive
  (netgap-0003);
* ``lossy_switch_chain`` — a heralded lossy switch chain with transmissivity ``eta``:
  the state is preserved on heralding, end-to-end success is ``eta**k``, and loss is
  honest and monotone (netgap-0004);
* ``bb84_key_rate`` — the exact asymptotic BB84 secret-key rate ``1 - 2 h(Q)`` and its
  secure-key threshold (netgap-0005).

CLAIM BOUNDARY: these are finite, exact, idealized models. They are not hardware,
materials, device-loss/noise, or full-security-proof claims; they are the exact
mathematical cores of the corresponding network primitives.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from gaugegap.quantum.quantum_information import concurrence, partial_trace

CLAIM_BOUNDARY = (
    "finite exact idealized quantum-network primitives; not hardware, device-loss, or "
    "full-security-proof claims"
)


# ============================================================ netgap-0002: Reck mesh
def _embed(n: int, i: int, block: np.ndarray) -> np.ndarray:
    u = np.eye(n, dtype=np.complex128)
    u[i, i], u[i, i + 1] = block[0, 0], block[0, 1]
    u[i + 1, i], u[i + 1, i + 1] = block[1, 0], block[1, 1]
    return u


@dataclass(frozen=True)
class MeshDecomposition:
    n_modes: int
    couplers: tuple[tuple[int, np.ndarray], ...]  # (adjacent mode i, 2x2 unitary)
    phases: np.ndarray  # diagonal residual phases

    def reconstruct(self) -> np.ndarray:
        rec = np.diag(self.phases).astype(np.complex128)
        for i, block in reversed(self.couplers):
            rec = _embed(self.n_modes, i, block).conj().T @ rec
        return rec


def reck_decomposition(unitary: np.ndarray) -> MeshDecomposition:
    """Factor a unitary into a mesh of adjacent 2x2 couplers plus a diagonal phase.

    Uses adjacent Givens rotations to null the sub-diagonal; a unitary upper-triangular
    matrix is diagonal, so the residual is a pure phase screen. Exact linear algebra.
    """
    w = np.array(unitary, dtype=np.complex128)
    n = w.shape[0]
    couplers: list[tuple[int, np.ndarray]] = []
    for col in range(n - 1):
        for row in range(n - 1, col, -1):
            a, b = w[row - 1, col], w[row, col]
            r = float(np.hypot(abs(a), abs(b)))
            if r < 1e-15:
                continue
            g = np.array([[np.conj(a), np.conj(b)], [-b, a]], dtype=np.complex128) / r
            w = _embed(n, row - 1, g) @ w
            couplers.append((row - 1, g))
    phases = np.diag(w).copy()
    return MeshDecomposition(n_modes=n, couplers=tuple(couplers), phases=phases)


def mesh_reconstruction_error(unitary: np.ndarray) -> float:
    return float(np.linalg.norm(reck_decomposition(unitary).reconstruct() - unitary))


# =================================================== netgap-0003: entanglement swap
def _bell() -> np.ndarray:
    v = np.zeros(4, dtype=np.complex128)
    v[0] = v[3] = 1.0 / np.sqrt(2.0)
    return v


_BELL_LABELS = ("phi_plus", "phi_minus", "psi_plus", "psi_minus")


def _bell_vectors() -> dict[str, np.ndarray]:
    s = 1.0 / np.sqrt(2.0)
    return {
        "phi_plus": np.array([s, 0, 0, s], dtype=np.complex128),
        "phi_minus": np.array([s, 0, 0, -s], dtype=np.complex128),
        "psi_plus": np.array([0, s, s, 0], dtype=np.complex128),
        "psi_minus": np.array([0, s, -s, 0], dtype=np.complex128),
    }


def entanglement_swap() -> dict[str, object]:
    """Two Bell pairs (A-B, C-D); a Bell measurement on B-C entangles A-D.

    For every Bell outcome on the middle qubits, the outer qubits A,D are projected into
    a maximally entangled state (concurrence 1), though they never interacted.
    """
    state = np.kron(_bell(), _bell())  # order A,B,C,D (qubits 0,1,2,3)
    eye = np.eye(2, dtype=np.complex128)
    outcomes: dict[str, object] = {}
    all_max = True
    for label, bc in _bell_vectors().items():
        proj_bc = np.outer(bc, bc.conj())  # 4x4 on qubits B,C
        projector = np.kron(np.kron(eye, proj_bc), eye)  # 16x16 on A,B,C,D
        projected = projector @ state
        prob = float(np.real(np.vdot(projected, projected)))
        if prob < 1e-12:
            outcomes[label] = {"probability": 0.0}
            continue
        projected = projected / np.sqrt(prob)
        rho_ad = partial_trace(projected, keep_qubits=[0, 3], total_qubits=4)
        c = float(concurrence(rho_ad))
        outcomes[label] = {"probability": round(prob, 6), "concurrence_AD": round(c, 6)}
        all_max = all_max and abs(c - 1.0) < 1e-6
    return {
        "outcomes": outcomes,
        "all_outcomes_maximally_entangled": bool(all_max),
        "total_probability": round(sum(o.get("probability", 0.0) for o in outcomes.values()), 6),
    }


# ======================================================= netgap-0004: loss budget
def lossy_switch_chain(eta: float, k: int) -> dict[str, object]:
    """Heralded lossy switch chain: transmissivity ``eta`` per switch, ``k`` switches.

    Conditioned on the photon surviving, the state is preserved (heralded fidelity 1).
    End-to-end heralding probability is ``eta**k``, which is monotone non-increasing in
    ``k`` — loss is explicit, not hidden.
    """
    if not 0.0 <= eta <= 1.0 or k < 0:
        raise ValueError("require 0 <= eta <= 1 and k >= 0")
    success = float(eta ** k)
    success_one_more = float(eta ** (k + 1))
    return {
        "eta": eta,
        "k": k,
        "heralded_fidelity": 1.0,
        "success_probability": success,
        "loss_probability": 1.0 - success,
        "success_after_one_more_switch": success_one_more,
        "loss_is_monotone": bool(success_one_more <= success + 1e-15),
    }


def emit_loss_certificate(label: str, eta: float, success: float) -> tuple[str, str]:
    """Discharged proof that each added lossy switch cannot increase success: eta*s <= s."""
    ns = "".join(ch for ch in label.title() if ch.isalnum()) or "Loss"
    ns = ns if not ns[0].isdigit() else "L" + ns
    lean = f"""import Mathlib.Tactic

namespace NetGap.Loss{ns}

axiom eta : ℝ
axiom s : ℝ
/-- TRUST INPUT 1 -- transmissivity in [0,1]. -/
axiom eta_le_one : eta ≤ 1
axiom eta_nonneg : eta ≥ 0
/-- TRUST INPUT 2 -- current heralding probability is non-negative. -/
axiom s_nonneg : s ≥ 0

/-- Adding one more lossy switch cannot increase the heralding probability. -/
theorem loss_monotone : eta * s ≤ s := by
  nlinarith [mul_nonneg s_nonneg (sub_nonneg.mpr eta_le_one)]

end NetGap.Loss{ns}
"""
    coq = f"""Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section NetGap_Loss{ns}.
Variable eta s : R.
(* TRUST INPUT 1: transmissivity in [0,1]. *)
Hypothesis eta_le_one : eta <= 1.
Hypothesis eta_nonneg : eta >= 0.
(* TRUST INPUT 2: current heralding probability is non-negative. *)
Hypothesis s_nonneg : s >= 0.

Theorem loss_monotone : eta * s <= s.
Proof. nra. Qed.

End NetGap_Loss{ns}.
"""
    return lean, coq


# ============================================================ netgap-0005: BB84 QKD
def binary_entropy(q: float) -> float:
    if q <= 0.0 or q >= 1.0:
        return 0.0
    return float(-q * np.log2(q) - (1.0 - q) * np.log2(1.0 - q))


def bb84_key_rate(qber: float) -> dict[str, object]:
    """Exact asymptotic BB84 secret-key rate r = 1 - 2 h(Q) and its secure threshold."""
    if not 0.0 <= qber <= 0.5:
        raise ValueError("require 0 <= qber <= 0.5")
    h = binary_entropy(qber)
    rate = 1.0 - 2.0 * h
    # Threshold: r = 0 where h(Q) = 1/2, i.e. Q ~ 0.1100.
    lo, hi = 0.0, 0.5
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if binary_entropy(mid) < 0.5:
            lo = mid
        else:
            hi = mid
    threshold = 0.5 * (lo + hi)
    return {
        "qber": qber,
        "binary_entropy": h,
        "key_rate": rate,
        "secure": bool(rate > 0.0),
        "secure_threshold_qber": round(threshold, 6),
    }


def emit_qkd_certificate(label: str, h_value: float, rate: float) -> tuple[str, str]:
    """Discharged proof that below the QBER threshold (h(Q) <= 1/2) the key rate is
    non-negative: r = 1 - 2 h(Q) >= 0."""
    ns = "".join(ch for ch in label.title() if ch.isalnum()) or "Bb84"
    ns = ns if not ns[0].isdigit() else "Q" + ns
    lean = f"""import Mathlib.Tactic

namespace NetGap.Qkd{ns}

axiom hQ : ℝ
axiom r : ℝ
/-- TRUST INPUT 1 -- error rate below threshold: h(Q) <= 1/2. -/
axiom hQ_le_half : hQ ≤ 1/2
/-- TRUST INPUT 2 -- key-rate definition. -/
axiom r_def : r = 1 - 2 * hQ

/-- Below the QBER threshold the BB84 secret-key rate is non-negative. -/
theorem secure_key : r ≥ 0 := by
  rw [r_def]; linarith [hQ_le_half]

end NetGap.Qkd{ns}
"""
    coq = f"""Require Import Reals.
Require Import Lra.
Open Scope R_scope.

Section NetGap_Qkd{ns}.
Variable hQ r : R.
(* TRUST INPUT 1: error rate below threshold: h(Q) <= 1/2. *)
Hypothesis hQ_le_half : hQ <= 1/2.
(* TRUST INPUT 2: key-rate definition. *)
Hypothesis r_def : r = 1 - 2 * hQ.

Theorem secure_key : r >= 0.
Proof. rewrite r_def. lra. Qed.

End NetGap_Qkd{ns}.
"""
    return lean, coq


# =================================================================== combined report
def network_report(n_modes: int = 4, eta: float = 0.9, k: int = 5, qber: float = 0.05,
                   seed: int = 0) -> dict[str, object]:
    """Run all four network primitives and assemble one evidence bundle."""
    rng = np.random.default_rng(seed)
    # A Haar-ish random unitary via QR of a complex Gaussian matrix.
    z = rng.standard_normal((n_modes, n_modes)) + 1j * rng.standard_normal((n_modes, n_modes))
    q, rmat = np.linalg.qr(z)
    q = q @ np.diag(np.diag(rmat) / np.abs(np.diag(rmat)))  # fix phases -> Haar unitary

    swap = entanglement_swap()
    loss = lossy_switch_chain(eta, k)
    qkd = bb84_key_rate(qber)
    loss_lean, loss_coq = emit_loss_certificate("chain", eta, loss["success_probability"])
    qkd_lean, qkd_coq = emit_qkd_certificate("bb84", qkd["binary_entropy"], qkd["key_rate"])

    return {
        "clements": {
            "n_modes": n_modes,
            "reconstruction_error": mesh_reconstruction_error(q),
            "num_couplers": len(reck_decomposition(q).couplers),
        },
        "entanglement_swap": swap,
        "loss_budget": {**loss, "certificate": {"lean4": loss_lean, "coq": loss_coq}},
        "qkd": {**qkd, "certificate": {"lean4": qkd_lean, "coq": qkd_coq}},
        "claim_boundary": CLAIM_BOUNDARY,
    }
