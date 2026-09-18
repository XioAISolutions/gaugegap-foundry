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
`PARTNER_PROBE_DIRECTIONS` and at the registered field and rate, so the numbers
cannot drift from this prose:

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

The two routes do not have the same numerical domain, and saying so is part of
the cross-check. The direct solve tracks the closed form over twenty decades of
rate, down to `1e-20`. The eigendecomposition route inverts the eigenvalues of a
non-Hermitian Liouvillian whose spectrum spans `|H|` down to `k`, so its relative
error grows as `eps * |H| / k`: at `k = 1e-10` it returned `0.1667` against a
true `0.4958`, finite and with nothing raised. It now refuses below
`sqrt(eps) * |H|`, where that error is at most `sqrt(eps)` — about `2.4 s^-1`
for the spin-free-partner system at 50 µT, against the registered `1e6`. A rate
small enough to underflow inside the decay operator itself (`k = 5e-324`
multiplied by the projector's `0.5` entries) is refused by both routes, and each
checks the yield it is about to return, because a Liouvillian that is singular
to working precision makes `np.linalg.solve` produce `nan` rather than raise.

Both routes are exact expressions, but their *numerical* agreement degrades with
the energy scale, because the conditioning of the `dim^2` solve does: the
asymmetric residual is `1.4e-16` at 50 uT, `1.1e-10` at 0.5 T and `2.0e-9` at
5 T. So the registered gate is decided at the registered field and rate, and the
field dependence is asserted in the test suite with a scale-aware tolerance
instead — see `test_the_two_solve_routes_agree_across_field_scales`. A flat
tolerance evaluated at the caller's field would fail a registered condition on
solve conditioning alone, which says nothing about the model.

### Registered conditions are not the caller's conditions

The hypothesis registers a field (50 uT), a rate (`1e6 s^-1`) and an angular
resolution (200 directions). Every registered condition is therefore decided at
those values, whatever `--field-ut`, `--direction-count` or `--rate-points` the
run used, and each one publishes the conditions it was decided at
(`polarity_field_microtesla`, `cross_check_rate_per_second`,
`zeeman_gate_field_microtesla`, and so on). The caller's own configuration is
still recorded — `field_microtesla`, `zeeman_thermal_ratio_300k`, the primary
sweep and the rate series all describe the run that was asked for — it just does
not decide anything the hypothesis registered.

The antipodal-degeneracy condition is decided the same way: it reads the
registered 200-direction sweep, and the primary sweep's residual is recorded
beside it as caller-specific output rather than gating anything. A 12-direction
run would otherwise certify that registered condition from 12 samples.

Accepted inputs are bounded as well as finite, because finiteness of the input
is not the property that matters -- finiteness of the operator built from it is.
`k = 1e308` is positive and finite, and the direct Liouvillian solve returned
`nan` for it instead of raising, which would have serialized as a measured
yield. `MAX_FIELD_TESLA`, `MAX_RATE_PER_S` and `MAX_HYPERFINE_MHZ` are derived
from the largest finite double and the factor each input is multiplied by before
it reaches a matrix, so they are not opinions about what a large field is; they
are published in every bundle. The CLI's own counts are bounded from the same
constants rather than separately: `--rate-points` is capped at the largest
decade the module will accept.

Bounding the inputs is not the whole property, so every computed quantity is
checked before it is used or published. Three defects had in-bounds inputs: a
direction whose components are finite but whose norm overflows, which
normalized to exactly `(0, 0, 0)` and silently dropped the Zeeman term from a
Hamiltonian that stayed finite; a temperature whose product with `k_B`
underflows to zero, which raised `ZeroDivisionError` inside the energy audit;
and a Zeeman/`k_B T` ratio that overflows from a legal field and a legal
temperature. `_require_finite_output` is the backstop for all of them, and the
direction is normalized by its largest component first so the norm cannot
overflow.

Counts are bounded by what they allocate, for the same reason magnitudes are
bounded by what they overflow — and the failure is not always loud. On numpy
2.4.6, `--direction-count 9223372036854775808` overflows int64 inside
`np.arange`, which returns an *empty* grid rather than raising, so the sweep ran
on zero directions and died several frames later in a reduction.
`MAX_DIRECTION_COUNT` and `MAX_HILBERT_DIMENSION` are arithmetic on a declared
byte budget rather than chosen numbers, and the Hilbert bound is applied to the
product of the multiplicities, not only to each one: enough individually legal
couplings still asks for an operator no budget covers. Each bound counts the
*peak* allocation rather than one of its terms — `build_hamiltonian` holds
thirteen `d x d` complex matrices at once (six embedded electron operators,
three nuclear, the accumulating Hamiltonian and three temporaries), and
`spin_operators` returns its three in one array, so the two have different
caps. A first version of this counted a single matrix and would have allowed a
dimension at which the electron operators alone are 384 MiB.

The hyperfine bound scales with the nuclear spin for the same reason. The term
that lands in the matrix is `A_ij * (S_i @ I_j)`, so the coefficient is
multiplied by the *operator* entries, and the nuclear ones grow with the spin:
`multiplicity=18` has a largest `I_z` entry of 8.5, and a principal value at
the spin-1/2 bound overflowed a Hamiltonian the constructor had accepted as
safe. The direction accounting
measures what a retained `DirectionSample` actually costs — object, `__dict__`
and boxed floats, about 556 bytes — instead of counting its numbers: the first
version of the cap counted 32 bytes per direction and so advertised a 64 MiB
budget that would really have needed about 1.1 GiB.

Unit conversion and operand order belong to the same class. `--field-ut 5e-324`
is a positive finite argument whose tesla value is exactly `0.0`, so the CLI
validates the value it will actually pass rather than the one it was given. And
the Zeeman/`k_B T` ratio multiplies its constants together *before* the field:
the other order underflows the numerator at `1e-310` T and published `0.0` for a
ratio whose true value, `4.48e-313`, is representable. A fabricated zero is
worse than an error, so a field too small for any representable ratio raises.

Shape is checked for the same reason. A `Sequence[float]` annotation is not a
shape check, and a four-component direction was normalized using all four
components while the Zeeman sum read the first three — the requested field
contribution came out a factor of `sqrt(2)` small with nothing raised. Every
three-vector argument, including a coupling's principal values and Euler
angles, goes through one converter that requires exactly three finite
components at the boundary where it is declared, rather than failing later
inside a matmul that names neither the coupling nor the field.

Nine controls inherited a caller parameter at some point in this track's
history, and each was found separately by review; two of them after a helper was
added to make a further escape impossible, because they did not route through
it. The guard is now a property test rather than a list of mechanisms:
`test_no_caller_parameter_can_change_a_registered_condition` runs the report at
5 T with an odd rate and resolution and requires the entire `checks` dict, and
the recorded evidence behind it, to be identical to a run at the registered
conditions. Under the previous code that run failed two registered conditions —
the Zeeman/`k_B T` ratio, on the caller's half-tesla field, and the asymmetric
solve, on conditioning.

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
  --rate-points 4 --output-dir /tmp/radical-pair-smoke

python -m pytest tests/test_radical_pair_forge.py
```

Or through the orchestrator:

```bash
foundry run --group radical-pair-forge
```

The runner exits non-zero if any registered check fails, and writes
`summary.json`, `directions.csv`, `rate_sweep.csv`, and `radical_pair_forge.svg`.
