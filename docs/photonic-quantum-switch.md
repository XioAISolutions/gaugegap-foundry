# NetGap — the finite core of a photonic quantum switch

Quantum networking needs a switch: a device that routes quantum information carried in
photons from any input port to any output port **without measuring it** (a measurement
would collapse the state). Thin-film-lithium-niobate (TFLN) photonic prototypes do this
with a programmable mesh of electro-optic couplers plus encoding converters.

NetGap keeps the part that is exactly computable and certifiable: the **unitary switch
fabric**. Strip the hardware away and a non-blocking, lossless quantum switch is a
finite unitary on N photonic modes, and "routing without loss" is exactly the statement
that a unitary preserves inner products, norm, fidelity, and entanglement.

> **Boundary:** this is a finite, lossless, unitary linear-optics model. It is not a
> hardware device, a TFLN materials or electro-optic claim, a loss / noise / thermal /
> insertion-loss model of a real chip, a fabrication or coherence-time claim, or a full
> quantum-network protocol. It is the exact mathematical switch fabric such a device
> implements.

## Device concept ↔ exact finite object

| Device stage (reel) | Finite object | Certified statement |
|---|---|---|
| Non-blocking switch (any in → any out) | permutation / crossbar unitary on N modes | unitary; **all N! routings** realized |
| Realized by a mesh of couplers | product of embedded 2×2 couplers (a sorting network) | mesh reconstructs the fabric with error `0` |
| Switch without collapsing the state | the fabric is a **unitary channel** | inner products & norm preserved ⇒ **no information loss** (discharged Lean/Coq) |
| Input/output state converters | encoding-conversion unitary `U`, `U†U = I` | **round-trip fidelity = 1** |
| Preserves quantum properties | routing = local unitary on the photon's subsystem | **entanglement invariant** — route one qubit of a Bell pair and `S = ln 2` is unchanged |

## What a run certifies

`foundry run netgap-0001-photonic-switch` emits a JSON bundle and (with
`--emit-certificate`) the discharged files, reporting:

- `fabric_unitary = true` and `mesh_reconstruction_error = 0` — the routing unitary is
  exactly the product of 2×2 couplers;
- `reachability`: every one of the `N!` routings is unitary and realized by a mesh —
  the non-blocking property;
- `inner_products_preserved`, `norm_preserved`, `round_trip_fidelity = 1` — quantum
  information is routed and converted without loss;
- `entanglement.preserved = true` with `S = ln 2` before and after — coherence survives
  the switch;
- a discharged Lean 4 / Coq certificate: given unitarity (`fidOut = fidIn`) and an input
  at the no-loss floor (`fidIn ≥ floor`), `fidOut ≥ floor` — routing preserves fidelity.

```bash
foundry run netgap-0001-photonic-switch
foundry run netgap-smoke
```

## The network layer (`netgap-0002` … `netgap-0005`)

The switch fabric is the first rung. The network layer adds the primitives a real
quantum network needs, each reduced to its exact finite core.

| ID | Primitive | Exact statement | Certificate |
|---|---|---|---|
| `netgap-0002` | **Clements/Reck decomposition** | any programmable N-mode unitary factors into an adjacent 2×2-coupler mesh | reconstruction error at machine precision (~1e-16) |
| `netgap-0003` | **Entanglement swapping** | two Bell pairs + a Bell measurement on the middle qubits leave the outer pair maximally entangled for **every** outcome | concurrence = 1, outcome probabilities sum to 1 |
| `netgap-0004` | **Loss budget** | heralded chain of transmissivity `η` over `k` switches: heralded fidelity 1, success `η^k`, monotone loss | discharged Lean/Coq `η·s ≤ s` |
| `netgap-0005` | **BB84 key rate** | asymptotic secret-key rate `r = 1 − 2h(Q)`, secure below `Q ≈ 0.11` | discharged Lean/Coq `r ≥ 0` when `h(Q) ≤ ½` |

```bash
foundry run netgap-0002-clements
foundry run netgap-0003-entanglement-swap
foundry run netgap-0004-loss-budget
foundry run netgap-0005-qkd
```

- **`netgap-0002`** turns the abstract routing unitary into a concrete mesh of couplers
  (the programmable core of a TFLN switch), verified by exact reconstruction.
- **`netgap-0003`** is the quantum-repeater primitive: entanglement is *created* between
  qubits that never met, by measuring their partners — the basis of long-distance
  quantum links.
- **`netgap-0004`** is the first honest step toward hardware: loss is explicit. The
  surviving-photon state is idealized as preserved, but the photon is lost with
  probability `1 − η^k`, and that loss is certified monotone.
- **`netgap-0005`** closes the loop with an application: a secure key can be extracted
  below the BB84 error threshold, discharged as a formal non-negativity certificate.

> **Boundary:** these are finite, exact, idealized models — machine-precision linear
> algebra, unit-fidelity Bell measurements, heralded-loss accounting, and the asymptotic
> one-way BB84 formula. They are not hardware, device-noise, finite-key, or
> composable-security claims. Each states exactly what it proves and what it does not.
