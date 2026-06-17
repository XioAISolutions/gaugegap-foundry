# Quantum signal extraction

`gaugegap.curverank_signal` extracts *signals* — expectation values, phases,
overlaps, and spectral content — from a finite-dimensional state `|ψ⟩`. It
complements the QPE family (`curverank_qpe`) with the time-series /
super-resolution route plus standard primitives, and every routine has an
**exact (statevector) mode** so results are deterministic and hermetically
testable.

> **Claim boundary.** These extract signals from *finite-system* operators/states
> and benchmark the methods. A quantum-extracted eigenvalue is a (noisy)
> *estimate*, never a certificate — it is cross-checked against the certified
> interval kernel. This is **not a proof** of the Riemann Hypothesis or any
> Millennium Prize problem; it is finite-system spectral screening.

## What's in the module

| Routine | Signal extracted |
|---|---|
| `hadamard_test(psi, U)` | `Re/Im ⟨ψ\|U\|ψ⟩` — the core phase/overlap primitive |
| `correlation_signal(H, psi, times)` | `g(t) = ⟨ψ\|e^{-iHt}\|ψ⟩ = Σ_j \|⟨E_j\|ψ⟩\|² e^{-iE_j t}` |
| `prony` / `esprit` | frequencies (eigenvalues) + weights from a sampled signal |
| `extract_eigenvalues(H, psi)` | eigenvalue estimates via the time series |
| `validate_against_certified` | checks estimates against certified enclosures |
| `classical_shadows` / `shadow_expectation` | many observables from few copies |
| `amplitude_estimation` | maximum-likelihood amplitude estimation (simulated) |

## The idea: spectra as a classical signal

The correlation function

```
g(t) = ⟨ψ| e^{-iHt} |ψ⟩ = Σ_j |⟨E_j|ψ⟩|² · e^{-iE_j t}
```

is a **sum of complex exponentials** whose frequencies are exactly the
eigenvalues `E_j` and whose amplitudes are the overlaps `|⟨E_j|ψ⟩|²`. Sample it
(via Hadamard tests at many `t`), then recover the `E_j` with classical
super-resolution — **Prony** or **ESPRIT**. Versus register QPE this uses
*shallow* circuits and pushes the work into classical post-processing.

In exact mode this recovers the Berry–Keating `xp` eigenvalues to ~1e-14, and
**every recovered eigenvalue lands inside the certified interval enclosures** —
the honest validation loop: quantum/numerical estimate in, certified check out.

## Run it

```bash
python scripts/run_curverank_signal.py --n-basis 8 --method esprit          # exact
python scripts/run_curverank_signal.py --n-basis 8 --method prony --shots 8192
```

Output: per-eigenvalue estimate, whether it falls in a certified enclosure, and a
JSON report under `results/curverank-signal/`.

## QCELS — Heisenberg-style single-eigenvalue estimation

`qcels(H, psi)` estimates the **dominant** eigenvalue (largest overlap weight in
`|ψ⟩`) by fitting `g(t) ~ A e^{-iθt}` over a multilevel schedule that doubles the
coherent evolution time, with a sub-Nyquist `dt` and parabolic sub-grid
refinement. With a clean signal the error scales roughly like `1/total_time` — a
Heisenberg-style gain from *longer evolution*, not more ancillas:

| total_time | abs error (exact) |
|---:|---:|
| 10 | 1.7e-4 |
| 40 | 4.8e-5 |
| 160 | 1.9e-6 |
| 320 | 3.8e-8 |

## Noise study (`scripts/run_curverank_noise_study.py`, `make curverank-noise-study`)

`correlation_signal(..., dephasing=γ, shots=N)` models hardware decoherence
(`g(t) → e^{-γt} g(t)`) and Hadamard-test shot noise. Sweeping both reveals an
honest, useful contrast:

- **QCELS (dominant eigenvalue) is robust** — error stays ~1e-4–1e-3 across
  dephasing up to 0.1 and shot budgets down to ~1k, because it only fits one
  frequency.
- **ESPRIT full-spectrum super-resolution is fragile** — recovering *all*
  eigenvalues is ill-conditioned under noise, and the max error grows by orders
  of magnitude.

The practical lesson: extract *one* well-separated eigenvalue robustly (QCELS);
treat full-spectrum super-resolution as an exact/low-noise tool. Either way the
output is validated against the certified enclosures.

## Honest limits

- **Sampling cost** — exact mode is the noiseless limit; with `--shots`, accuracy
  follows the usual `~1/√N` (Hadamard test) statistics.
- **Aliasing** — `dt` is chosen sub-Nyquist from the spectral radius; eigenvalues
  outside `(-π/dt, π/dt]` would alias.
- **Estimate ≠ certificate** — extracted eigenvalues are validated against, and do
  not replace, the certified interval kernel.
- Classical shadows and amplitude estimation here are correct but small-scale
  demonstrations of the primitives, not a production estimation stack.
