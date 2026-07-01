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

## Where this can grow

This is the first NetGap layer. Natural finite extensions that stay inside the boundary:
Clements/Reck decomposition of an arbitrary programmable unitary, entanglement-swapping
and Bell-measurement routing, a lossy (non-unitary) channel model with an explicit loss
budget, and a small quantum-key-distribution or entanglement-distribution protocol over
the finite switch — each with its own certificate and claim boundary.

> **Boundary:** a finite unitary that preserves fidelity and entanglement is exact
> evidence for the switch fabric's mathematics. It does not establish that a physical
> TFLN chip achieves it, nor that a full quantum network is realizable end to end.
