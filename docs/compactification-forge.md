# Compactification Forge

Compactification Forge is a finite educational substrate for string-theory
extra-dimension content.  It starts with compact circles and tori, not full
Calabi-Yau geometry.

## What It Demonstrates

The first unit, `compact-0001`, computes finite Kaluza-Klein and winding-mode
spectra.  In natural toy units, a compact radius `R` contributes terms like:

```text
m^2 = m0^2 + sum_i (n_i / R_i)^2 + sum_i (w_i R_i / alpha')^2
```

The key explainer result is visible in the emitted spectrum:

- the zero mode remains visible at low energy;
- compact momentum modes become heavy when `R` is small;
- winding modes move in the opposite direction with `R`;
- a low detector cutoff can therefore see an effectively lower-dimensional world.

## What It Does Not Do

This track does not compute:

- a Calabi-Yau metric;
- moduli stabilization;
- a Standard Model particle spectrum;
- a proof of string theory;
- evidence that real extra dimensions exist.

It is a finite toy model for the straw/hose analogy and for the low-energy
effective-spectrum idea.

## Foundry Use

The Foundry Experience can show this as a spectrum scene: hidden dimensions are
not asserted, but the finite mechanism is made visible.  The right reader-facing
phrase is:

> A compact hidden coordinate would appear through discrete excitation towers;
> if those towers sit above the accessible cutoff, the low-energy observer sees
> fewer dimensions.

## Run

```bash
python scripts/run_compactification_forge.py --geometry suite --output-dir /tmp/compact-0001
```

The script emits `summary.json`, `modes.csv`, and `compactification_forge.svg`.
