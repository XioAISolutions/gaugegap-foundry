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

Three results are structural: they follow from the form of the Hamiltonian and
hold for any hyperfine values. A fourth is parameter-dependent and is labelled
as such, because presenting it alongside the exact ones would overstate it.

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

The antipode of `(theta, phi)` is `(180 - theta, phi + 180)`, **not** a mirrored
polar angle: for a rhombic tensor the yield depends on azimuth as well, so two
samples at `theta` and `180 - theta` with unrelated azimuths need not agree. The
evidence bundle therefore records each direction's antipodal yield alongside its
own (`antipodal_singlet_yield` in `directions.csv`), and the figure plots one
against the other so the degeneracy is demonstrated rather than asserted.

The model therefore carries inclination but no polarity information: it cannot
distinguish North from South. A term odd under
`Theta`, such as a chirality-induced spin selectivity term, would be required to
break the degeneracy, and none is modelled here.

### 3. Fast recombination destroys the compass (structural)

As `k -> infinity` the pair has no time to leave the singlet: the yield tends to
one in every direction and the anisotropy tends to zero. Sweeping `1e3` to
`1e10` per second shows the collapse.

This is an **upper cutoff only**, not a lifetime window. Because no spin
relaxation is modelled, the anisotropy here is flat or slightly larger as
`k -> 0` — in the committed sweep it is larger at `1e3` than at `1e6`. A real
pair is bounded at long lifetimes by `T2` of order microseconds, which this
model does not contain. Do not read a microsecond optimum out of it.

### 4. Loading the partner radical costs you the compass (parameter-dependent)

With one anisotropically coupled nucleus on the flavin and a spin-free partner,
the anisotropy is large. Add a single tryptophan beta-proton to the partner
radical and it falls by about `8x`.

This one is **not** structural, and is reported as a measurement of this
registry rather than a property of the mechanism. The code compares exactly two
inventories, so it establishes neither the magnitude nor the sign of the effect
for any other partner tensor, magnitude or orientation. No theorem is offered.

An earlier draft claimed "only the sign of the effect is robust". That was also
an over-claim and has been removed: comparing two fixed inventories, and
observing that the difference vanishes as this particular tensor is scaled to
zero, says nothing about whether some other partner tensor could *increase* the
anisotropy. `probe_partner_suppression()` sweeps synthetic axial partner tensors across
magnitude and orientation to test exactly that, and its output is recorded in
every evidence bundle under `controls.partner_probe`, at a fixed
`PARTNER_PROBE_DIRECTIONS` so the numbers cannot drift from this prose:

The strength series is generated as **scalar multiples of one principal-value
tuple**, so the transverse-to-axial ratio is held at `-0.056707` throughout and
only the magnitude varies. Orientation is probed separately, at full strength.

| axis | partner tensor | ratio to spin-free |
|---|---|---|
| strength | axial 49.2 MHz | 0.402 |
| strength | axial 20 MHz | 0.673 |
| strength | axial 5 MHz | 0.858 |
| strength | axial 1 MHz | **0.542** |
| strength | axial 0.2 MHz | 0.726 |
| orientation | 49.2 MHz at beta = 90 deg | 0.305 |

No probe point increases the anisotropy. But suppression is **not monotonic in
coupling strength**: it weakens from 49 to 5 MHz, strengthens again at 1 MHz,
then weakens at 0.2 MHz — with shape and orientation held fixed, so this is a
statement about strength alone.

An earlier version of this probe hand-wrote each magnitude, which let the shape
ratio drift from `-0.057` to `-0.100` across the series and confounded strength
with shape; its non-monotonicity result could not be attributed to strength at
all. The conclusion survived the fixed-shape redesign, but the earlier evidence
for it was invalid. `test_the_strength_probe_holds_tensor_shape_fixed` now
asserts the shape invariant so the confound cannot return, and
`test_partner_probe_backs_the_documented_non_monotonicity` pins the result.

### The energy audit

At 50 uT the electron Zeeman quantum is `2.24e-7` of `k_B T` at 300 K, and a
5 mT magnet only reaches `2.24e-5`. No field in this problem can drive a thermal
population change. The effect is a change in reaction *rates* during a coherent
window, and the recorded ratio is there so no reader can mistake it for anything
else.

### Cross-check

The closed form is checked against an exact solve of the Haberkorn master
equation, `int rho dt = (-L)^-1 rho(0)`, which also runs with `k_S != k_T` where
no closed form exists. The Liouvillian is dense with side `dim^2`, so its cost
grows as `dim^6`; above `LIOUVILLIAN_DIM_LIMIT` the cross-check runs on a
smaller fixed system and the report records which one was used
(`cross_check_inventory`). The expression being validated is
inventory-independent, so a smaller system tests it just as well. Symmetric rates agree to `~1e-16`; asymmetric rates
differ, and converge back as the rates are brought together.

## Claim Boundary

Allowed language:

- finite radical-pair spin-Hamiltonian calculation
- singlet-yield anisotropy over field direction
- exact polarity degeneracy of the model Hamiltonian
- isotropic-hyperfine negative control
- fast-recombination cutoff
- reproducible finite result

Avoided language:

- quantum eye, wetware eye, or bio-magnetometer
- a sensor, device, or anything that can be plugged in
- any sensitivity figure in tesla per root hertz
- a measurement of cryptochrome, flavin, or any protein
- evidence that a bird, insect, or any animal uses this mechanism
- quantum coherence observed in living tissue
- entanglement carrying information, or acting at a distance
- a recombination-lifetime window or a microsecond optimum
- the partner-suppression factor as a structural or mechanism-level result
- any general claim about the sign or magnitude of partner suppression beyond this registry

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
