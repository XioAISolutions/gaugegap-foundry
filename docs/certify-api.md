# `certify_spectrum` — certified eigenvalue enclosures for any Hermitian matrix

The product-facing entry point over the general certified-eigenvalue kernel. Give
it a Hermitian matrix; get rigorous directed-rounding interval enclosures for every
eigenvalue (not floating-point estimates), plus a structured certificate.

## Python API

```python
import numpy as np
from gaugegap.certify import certify_spectrum

H = ...  # any real-symmetric or complex-Hermitian matrix
cert = certify_spectrum(H)
cert.enclosures   # [(lo, hi), ...] ascending, each rigorously contains an eigenvalue
cert.midpoints    # per-eigenvalue interval midpoints
cert.max_width    # widest enclosure (a global accuracy figure)
cert.to_dict()    # JSON-serialisable certificate (+ claim boundary)
```

For a registered candidate-operator family you can also attach the discharged
Lean 4 / Coq separation proof:

```python
from gaugegap.curverank_registry import get_operator
H = get_operator("xp").build(8)
cert = certify_spectrum(H, formal_family="xp")
cert.formal["separated"]   # True
cert.formal["lean4"]       # machine-checkable Lean 4 source
```

## Machine-checkable certificate for any matrix

`certify_spectrum(H, emit_formal=True)` attaches a generic, discharged
**global-spectral-enclosure** certificate (Lean 4 `linarith` / Coq `lra`, no proof
holes) for *any* Hermitian matrix — not just the registered families. The single
trust input is the verified interval kernel's per-eigenvalue bounds; the assistant
discharges that every eigenvalue lies within `[min lo_i, max hi_i]`
(`src/gaugegap/rigorous/enclosure_certificate.py`).

## CLI

Installed as a console entry point (`pip install -e .`):

```bash
gaugegap-certify matrix.npy                 # .npy / .csv / .txt, Hermitian
gaugegap-certify matrix.npy --output cert.json
gaugegap-certify matrix.npy --emit-formal --name MyMatrix   # generic Lean/Coq cert
gaugegap-certify xp_n8.npy --formal-family xp               # separation proof
```

## HTTP service

A stdlib-only reference service (no dependencies) wraps the API:

```bash
python scripts/serve_certify.py --host 127.0.0.1 --port 8077
curl -s localhost:8077/certify -d '{"matrix": [[2,0],[0,3]], "emit_formal": true}'
```

`POST /certify` returns the certificate JSON; `GET /health` returns ok. Bind to
localhost for local/dev use — it is a reference service, not a hardened public
endpoint.

## Scaling

The kernel is exact-arithmetic (~`O(n^3)`). `make certify-scaling`
(`scripts/run_certify_scaling.py`) benchmarks wall-time + max enclosure width vs
truncation size; on this machine n=4→32 runs in ~0.008s→~1.8s with enclosure
widths ~1e-10. Target small-to-moderate dense matrices.

## What is and isn't claimed

The enclosures are **rigorous** (residual / Bauer-Fike bounds in directed-rounding
interval arithmetic), suitable wherever a certified eigenvalue enclosure beats a
floating-point estimate — vibration/structural modes, control-loop stability,
power-grid small-signal analysis, finite-element spectra, validating a quantum
eigensolver's output. This is **verification infrastructure**; it is not a proof of
the Riemann Hypothesis or any Millennium Prize problem. Cost is roughly `O(n^3)` in
exact arithmetic, so it targets small-to-moderate dense matrices.
