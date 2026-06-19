#!/usr/bin/env python3
"""Minimal HTTP service exposing certify_spectrum (stdlib only, no dependencies).

POST /certify with a JSON body:

    {"matrix": [[2,0],[0,3]], "emit_formal": false, "name": "MyMatrix"}

returns the certified-spectrum JSON (rigorous interval eigenvalue enclosures, plus
an optional discharged Lean/Coq enclosure certificate). GET /health returns ok.

CLAIM BOUNDARY: returns rigorous finite-matrix eigenvalue enclosures (verification
infrastructure). Not a proof of the Riemann Hypothesis or any Millennium Prize
problem. Bind to localhost for local/dev use; this is a reference service, not a
hardened public endpoint.
"""
from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.certify import certify_spectrum

MAX_DIM = 256  # guard: certified enclosure is ~O(n^3) exact arithmetic


def certify_request(payload: dict) -> dict:
    """Pure request handler: validate a payload and return the certificate dict.

    Raises ValueError on bad input (the HTTP layer maps this to a 400).
    """
    if "matrix" not in payload:
        raise ValueError("missing 'matrix'")
    H = np.array(payload["matrix"], dtype=complex)
    if H.ndim != 2 or H.shape[0] != H.shape[1]:
        raise ValueError("'matrix' must be square")
    if H.shape[0] > MAX_DIM:
        raise ValueError(f"matrix too large (max {MAX_DIM})")
    if np.allclose(H.imag, 0):
        H = H.real
    cert = certify_spectrum(
        H,
        error=float(payload.get("error", 1e-12)),
        emit_formal=bool(payload.get("emit_formal", False)),
        name=str(payload.get("name", "Matrix")),
    )
    return cert.to_dict()


class _Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send(200, {"status": "ok"})
        else:
            self._send(404, {"error": "not found; POST /certify or GET /health"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/certify":
            self._send(404, {"error": "not found; POST /certify"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
            self._send(200, certify_request(payload))
        except ValueError as exc:
            self._send(400, {"error": str(exc)})
        except Exception as exc:  # pragma: no cover - defensive
            self._send(500, {"error": f"internal error: {exc}"})

    def log_message(self, *args) -> None:  # quiet by default
        pass


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8077)
    args = ap.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), _Handler)
    print(f"certify service on http://{args.host}:{args.port} "
          f"(POST /certify, GET /health) — Ctrl-C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
