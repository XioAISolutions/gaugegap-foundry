# Radical Pair Forge

Radical Pair Forge is a bounded GaugeGap track for the spin-chemistry core of the
radical-pair magnetoreception hypothesis: the claim that a photo-induced pair of
radicals in a cryptochrome protein can report the direction of the Earth's
magnetic field through the singlet/triplet interconversion of two electron
spins.

## What It Is

The first unit, `radicalpair-0001`, is an exactly diagonalizable finite spin
Hamiltonian, not a protein simulation and not a device:

```
H = gamma_e B.(S1 + S2) + sum_n S_(radical n) . A_n . I_n
```

Two electron spins plus a declared nuclear inventory. The observable is the
singlet recombination yield under symmetric Haberkorn recombination, computed in
closed form,

```
Phi_S = (1/Z) sum_mn |<m|P_S|n>|^2 k^2 / (k^2 + omega_mn^2)
```

and swept over a deterministic Fibonacci sphere of field directions at 50 uT,
where the electron Larmor frequency is 1.401 MHz.

Three of the four results are structural: they follow from the form of the
Hamiltonian and do not depend on the hyperfine values chosen.

### 1. The anisotropy of a coupling tensor is the compass, not entanglement

Replace every hyperfine tensor with its trace-preserving isotropic part and the
direction dependence vanishes to machine precision. The radical pair is still
prepared in a singlet, the two electrons are still correlated, and the compass
is gone. Whatever the mechanism is, it is not "entanglement senses the field".

### 2. The mechanism cannot resolve polarity, as an exact theorem

`Phi_S(B) = Phi_S(-B)` identically. Spin time reversal `Theta` is antiunitary
with `Theta S Theta^-1 = -S`; the hyperfine term is bilinear in spin and
therefore even under `Theta`; the singlet projector is rotationally invariant.
So `Theta H(B) Theta^-1 = H(-B)` preserves both the spectrum and every
`|<m|P_S|n>|^2`, and the yield cannot depend on the sign of the field.

This is an inclination sensor. It cannot tell North from South. A term odd under
`Theta`, such as a chirality-induced spin selectivity term, would be required to
break the degeneracy, and none is modelled here.

### 3. Loading the partner radical costs you the compass

With one anisotropically coupled nucleus on the flavin and a spin-free partner,
the anisotropy is large. Add a single tryptophan beta-proton to the partner
radical and it falls by close to an order of magnitude. This is why an
anisotropically coupled radical paired with a nearly spin-free partner is the
favourable geometry for the hypothesis.

### 4. The pair has to live about as long as it precesses

Sweeping the recombination rate from `1e3` to `1e10` per second collapses the
anisotropy once recombination outruns precession. The window sits near
`k ~ omega`, a lifetime of order a microsecond.

### The energy audit

At 50 uT the electron Zeeman quantum is `2.24e-7` of `k_B T` at 300 K, and a
5 mT magnet only reaches `2.24e-5`. No field in this problem can drive a thermal
population change. The effect is a change in reaction *rates* during a coherent
window, and the recorded ratio is there so no reader can mistake it for anything
else.

### Cross-check

The closed form is checked against an exact solve of the Haberkorn master
equation, `int rho dt = (-L)^-1 rho(0)`, which also runs with `k_S != k_T` where
no closed form exists. Symmetric rates agree to `~1e-16`; asymmetric rates
differ, and converge back as the rates are brought together.

## Claim Boundary

Allowed language:

- finite radical-pair spin-Hamiltonian calculation
- singlet-yield anisotropy over field direction
- exact polarity degeneracy of the model Hamiltonian
- isotropic-hyperfine negative control
- recombination-lifetime window
- reproducible finite result

Avoided language:

- quantum eye, wetware eye, or bio-magnetometer
- a sensor, device, or anything that can be plugged in
- any sensitivity figure in tesla per root hertz
- a measurement of cryptochrome, flavin, or any protein
- evidence that a bird, insect, or any animal uses this mechanism
- quantum coherence observed in living tissue
- entanglement carrying information, or acting at a distance

What this track does **not** model, and would need before any of it bore on a
real organism or instrument: spin relaxation (so the long-lifetime side of the
rate window is not reproduced, and anisotropy wrongly persists as `k -> 0`),
exchange and dipolar coupling between the radicals, the full nuclear inventory
of a real flavin and tryptophan, and the orientational ordering of the proteins
in a membrane, which the hypothesis requires and which remains unestablished.

The hyperfine values in `HYPERFINE_REGISTRY` are literature-style
order-of-magnitude model inputs, and the relative Euler orientations are
illustrative. The structural results above do not depend on them; the recorded
numerical yields do.

## How To Run

```bash
# default inventory: anisotropic flavin nucleus plus a loaded partner radical
python scripts/run_radical_pair_forge.py \
  --output-dir results/radicalpair-0001-cryptochrome-compass

# the favourable geometry: same nucleus, spin-free partner
python scripts/run_radical_pair_forge.py --inventory spin-free-partner \
  --output-dir results/radicalpair-0001-spin-free-partner

# reduced smoke check
python scripts/run_radical_pair_forge.py --direction-count 40 \
  --control-direction-count 20 --rate-points 4 --output-dir /tmp/radical-pair-smoke

python -m pytest tests/test_radical_pair_forge.py
```

Or through the orchestrator:

```bash
foundry run --group radical-pair-forge
```

The runner exits non-zero if any registered check fails, and writes
`summary.json`, `directions.csv`, `rate_sweep.csv`, and `radical_pair_forge.svg`.
