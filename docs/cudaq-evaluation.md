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

## Wired in: GPU-able `g(t)` + benchmark

`backend="auto"` is now wired into a circuit form of the correlation signal:

```python
from gaugegap.providers import cudaq_adapter as cq
g = cq.circuit_correlation_signal(H, times, backend="auto", trotter_steps=200)
```

`circuit_correlation_signal` runs the time evolution as a **Trotter circuit**
through the backend (numpy now, CUDA-Q GPU when present), using `|+...+>` as the
probe state. It is the GPU-able sibling of
`curverank_signal.correlation_signal`. Verification-first: the numpy backend is
**validated against the exact eigendecomposition within Trotter error** (see
`tests/test_cudaq_adapter.py`), and the CUDA-Q backend runs the identical gate
list.

Benchmark the backends:

```bash
python scripts/run_cudaq_benchmark.py --max-qubits 12   # make cudaq-benchmark
```

On CPU it shows the full-matrix numpy simulator's steep growth (e.g. ~0.7 s at
n=10), i.e. exactly where a GPU statevector pays off; the CUDA-Q rows populate
when a GPU is present.

## Still outstanding (needs a GPU to validate)

Wiring `backend="auto"` into the **QPE** path (`curverank_qpe`, which builds
qiskit circuits) needs a qiskit→gate-list bridge; and exercising the CUDA-Q path
end-to-end needs an actual GPU. Per the repo's verification-first stance, those
land once GPU CI (or a GPU dev machine) is available — the numpy-validated `g(t)`
path and the capability-gated adapter are the honest, testable groundwork. Add
`cuda-quantum` as an optional extra (`pip install -e '.[gpu]'`) when adopting.

## Claim boundary

Simulation acceleration only. CUDA-Q changes *how fast* a finite-system
simulation runs, never *what* is claimed: results stay finite-system spectral
screening, validated against the certified kernel, and **not a proof** of the
Riemann Hypothesis.
