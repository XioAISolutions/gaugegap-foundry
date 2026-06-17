# CUDA-Q evaluation

An honest fit analysis of [NVIDIA CUDA-Q](https://github.com/NVIDIA/cuda-quantum)
for this project, plus the optional adapter shipped alongside it.

**Verdict:** unlike most external tools evaluated here, CUDA-Q is a **genuine
fit** — as an *optional, GPU-accelerated simulation backend* for the quantum
tracks. It is **not** for the certified core (CPU interval arithmetic), and its
real benefit needs an NVIDIA GPU, so it must stay a capability-gated optional
dependency with a CPU fallback.

## What CUDA-Q is

- Open-source (**Apache-2.0**) hybrid quantum-classical platform from NVIDIA.
- C++/Python quantum kernels (`nvq++` compiler), with **CPU *and* GPU**
  simulation backends — statevector, tensor-network, multi-GPU/multi-node — and
  the ability to target real QPUs.
- Pip / container installable.

## Where it helps this repo

The repo simulates quantum circuits in two places:

- **QPE** (`curverank_qpe`) — register / windowed / iterative / Trotter.
- **Signal extraction** (`curverank_signal`) — the correlation signal
  `g(t) = ⟨ψ|e^{-iHt}|ψ⟩`.

Today these run on Aer / numpy at small `n`, which is fine. **The moment the work
pushes to larger qubit counts** (bigger truncations, deeper QPE, longer `g(t)`
records), a single CPU statevector becomes the bottleneck — and that is exactly
where CUDA-Q's GPU statevector / tensor-network simulators pay off. It plays the
same role as the IBM adapter: a backend, opted into, never required.

## Where it does NOT help

- **Not the certified core.** Eigenvalue enclosures are directed-rounding interval
  arithmetic on the CPU; CUDA-Q is irrelevant there.
- **Benefit needs a GPU.** CUDA-Q has a CPU mode, but at the repo's current sizes
  it would not beat Aer/numpy, and **CI has no GPU**. So it cannot be a required
  dependency.

## The optional adapter (`gaugegap.providers.cudaq_adapter`)

A thin, portable **gate-list statevector** primitive — the unit other quantum code
can target — with three backends:

```python
from gaugegap.providers import cudaq_adapter as cq
gates = cq.ghz_circuit(3)                       # [(h,0), (cx,0,1), (cx,1,2)]
cq.statevector(gates, 3, backend="numpy")       # tested reference (always available)
cq.statevector(gates, 3, backend="auto")        # CUDA-Q if installed, else numpy
cq.backend_info()                               # {"available": ..., "target"/"fallback": ...}
```

Design choices (verification-first):

- **Capability-gated** — `cudaq_available()` is the only switch; importing the
  module never needs CUDA-Q or a GPU.
- **CPU fallback always present** — the numpy statevector is the tested reference;
  `backend="auto"` falls back to it.
- **Parity, not trust** — a skip-guarded test (`tests/test_cudaq_adapter.py`)
  checks the CUDA-Q path against the numpy reference. **CI verifies the fallback;**
  the GPU path is exercised only where CUDA-Q + a GPU exist.

## Recommended next step (follow-up, only when needed)

Wire `backend="auto"` into the QPE and `g(t)` pipelines so large-`n` runs use the
GPU when present and the existing CPU path otherwise. Add `cuda-quantum` as an
optional extra (e.g. `pip install -e '.[gpu]'`). Until a run actually needs more
qubits than CPU handles, the adapter + this evaluation are the right amount of
investment — *good tool, adopt it the moment the simulations outgrow the CPU.*

## Claim boundary

Simulation acceleration only. CUDA-Q changes *how fast* a finite-system
simulation runs, never *what* is claimed: results stay finite-system spectral
screening, validated against the certified kernel, and **not a proof** of the
Riemann Hypothesis.
