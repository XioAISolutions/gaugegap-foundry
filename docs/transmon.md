# Transmon artificial atoms: why a Josephson junction makes a qubit

A superconducting qubit is an electrical circuit that behaves like an atom. This module
([`gaugegap.quantum.transmon`](../src/gaugegap/quantum/transmon.py)) takes the
viral-reel explanation of superconducting qubits — Cooper pairs, Josephson junctions,
microwave control — and reduces it to the one statement that can be **certified**: *a
linear circuit cannot be a qubit; the Josephson nonlinearity is what makes one*.

## The physics, in one Hamiltonian

In the charge (Cooper-pair-number) basis,

```
H = 4 E_C (n − n_g)²  −  E_J cos(φ)
```

- `4 E_C (n − n_g)²` — the **charging energy** (diagonal): the cost of moving Cooper
  pairs onto the island.
- `−E_J cos(φ)` — the **Josephson tunnelling** (off-diagonal `−E_J/2`): Cooper pairs
  tunnel coherently through the insulator. This is the *nonlinear* term.

A plain `LC` circuit is a harmonic oscillator: equally spaced levels, so a pulse
resonant with `0→1` is equally resonant with `1→2`, `2→3`, … — you can never isolate a
two-level system. The `cos(φ)` nonlinearity breaks that degeneracy.

## What is certified

| Quantity | Result | Meaning |
|---|---|---|
| Anharmonicity `α = ω₁₂ − ω₀₁` | `→ −E_C` (e.g. `−1.15 E_C` at `E_J/E_C=50`) | the qubit transition is detuned from `1→2`: **addressable** |
| Certified `α` enclosure | rigorous interval **strictly below 0** | the qubit is *provably* anharmonic (interval eigensolver on the exactly-rational matrix) |
| Charge dispersion `ε₀₁` | falls `~exp(−√(8E_J/E_C))` (`0.25 → 4·10⁻⁵ → 3·10⁻⁸`) | why transmons resist charge noise (Koch 2007) |

The discharged Lean 4 / Coq certificate records the algebraic core: with leading-order
`ω₀₁ = √(8E_JE_C) − E_C` and `ω₁₂ = √(8E_JE_C) − 2E_C`, a nonzero charging energy
`E_C > 0` gives `ω₀₁ > ω₁₂` — a resolvable qubit transition. The harmonic limit
`E_C → 0` closes the gap (no qubit). z3 independently re-checks the same schema, and the
interval enclosure of the *full* numerical anharmonicity is what proves addressability
for the actual diagonalized spectrum.

```bash
python -c "from gaugegap.quantum.transmon import analyze_transmon as a; r=a(EJ=50,EC=1); \
print('anharmonicity/E_C =', round(r.anharmonicity_over_EC,3), \
'| certified < 0:', r.is_anharmonic_certified)"
# anharmonicity/E_C = -1.149 | certified < 0: True
```

## Claim boundary

The standard Cooper-pair-box / transmon model (Koch et al., Phys. Rev. A **76**, 042319,
2007) as a finite charge-basis diagonalization with a rigorous interval enclosure of the
anharmonicity. Energies are in units of `E_C`. This is **not** a fabrication, materials,
or coherence-time (`T₁`/`T₂`) claim, **not** a statement about any specific device, and
**not** a member of the [physical-limits web](physical-limits-web.md) — it is the device
physics underneath this repo's hardware adapters (IBM / Braket / IonQ / Quantinuum),
made certifiable.
