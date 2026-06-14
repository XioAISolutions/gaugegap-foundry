"""Spectra — a tiny declarative language for *certified* spectral screening.

Spectra is a domain-specific language over this repository's certified pipeline.
Its defining idea: **certification is a first-class semantic.** A value produced
by ``certify`` is a rigorous interval (no floats leak), and an ``assert
separated`` either is discharged by the interval-arithmetic kernel — emitting a
machine-checkable Lean/Coq certificate — or the program *fails*. You cannot state
a spectral separation the kernel will not back.

This is deliberately small and honest: it screens finite-truncation candidate
Hilbert–Pólya operators and benchmarks them. It is **not** a general quantum
programming language, and nothing it expresses is a proof of the Riemann
Hypothesis — the separations are certified *negative* results about finite
matrices.

Grammar (one statement per line; ``#`` starts a comment)::

    zeros    Z   = riemann(20)
    operator xp  = berry_keating(n=20)
    operator dr  = dirac_rindler(n=20)
    certify  Mx  = mismatch(xp, Z)
    assert   separated(Mx, threshold=1.0)
    measure  Qx  = qpe(xp, window=0.5, precision=6)   # needs qiskit
    report   "results/spectra-demo"

Families: ``berry_keating`` (xp), ``dirac_rindler``, ``quantum_graph``.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from gaugegap.curverank_certified import certified_family_mismatch
from gaugegap.rigorous.curverank_formal_emit import (
    discharged_monotonicity_proof,
    discharged_separation_proof,
)

_FAMILIES = {
    "berry_keating": "xp",
    "xp": "xp",
    "dirac_rindler": "dirac_rindler",
    "quantum_graph": "quantum_graph",
}


class SpectraError(Exception):
    """Raised on a parse error or a failed (uncertified) assertion."""


@dataclass
class Program:
    """Result of running a Spectra program."""
    zeros: Dict[str, int] = field(default_factory=dict)
    operators: Dict[str, Dict] = field(default_factory=dict)
    certificates: Dict[str, Dict] = field(default_factory=dict)
    assertions: List[Dict] = field(default_factory=list)
    monotonicity: List[Dict] = field(default_factory=list)
    measurements: Dict[str, Dict] = field(default_factory=dict)
    report_dir: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "claim_boundary": (
                "Certified finite-truncation spectral screening + benchmark; "
                "not a proof of the Riemann Hypothesis."
            ),
            "zeros": self.zeros,
            "operators": self.operators,
            "certificates": {
                k: {"family": v["family"], "n": v["n"], "k_zeros": v["k_zeros"],
                    "lower": v["lower"], "upper": v["upper"]}
                for k, v in self.certificates.items()
            },
            # Reference the emitted certificate files by name; the full Lean/Coq
            # source lives in the .lean/.v files, not inlined here.
            "assertions": [
                {"certificate": a["certificate"], "threshold": a["threshold"],
                 "certified_lower": a["certified_lower"], "separated": a["separated"],
                 "lean4_file": f"{a['certificate']}_separation.lean",
                 "coq_file": f"{a['certificate']}_separation.v"}
                for a in self.assertions
            ],
            "monotonicity": [
                {"family": m["family"], "panel": m["panel"], "lowers": m["lowers"],
                 "lean4_file": f"{m['family']}_monotone.lean",
                 "coq_file": f"{m['family']}_monotone.v"}
                for m in self.monotonicity
            ],
            "measurements": self.measurements,
        }


# --- statement patterns ------------------------------------------------------
_RE_ZEROS = re.compile(r"^zeros\s+(\w+)\s*=\s*riemann\(\s*(\d+)\s*\)$")
_RE_OPERATOR = re.compile(r"^operator\s+(\w+)\s*=\s*(\w+)\(\s*n\s*=\s*(\d+)\s*\)$")
_RE_CERTIFY = re.compile(r"^certify\s+(\w+)\s*=\s*mismatch\(\s*(\w+)\s*,\s*(\w+)\s*\)$")
_RE_ASSERT = re.compile(r"^assert\s+separated\(\s*(\w+)\s*,\s*threshold\s*=\s*([\d.]+)\s*\)$")
_RE_PROVE_MONO = re.compile(
    r"^prove\s+monotone\(\s*(\w+)\s*,\s*panel\s*=\s*([\d,]+)\s*,\s*zeros\s*=\s*(\w+)\s*\)$"
)
_RE_MEASURE = re.compile(
    r"^measure\s+(\w+)\s*=\s*qpe\(\s*(\w+)\s*,\s*window\s*=\s*([\d.]+)\s*,\s*"
    r"precision\s*=\s*(\d+)\s*(?:,\s*backend\s*=\s*([\w-]+)\s*)?\)$"
)
_RE_REPORT = re.compile(r'^report\s+"([^"]+)"$')


class Interpreter:
    def __init__(self) -> None:
        self.p = Program()

    def run(self, source: str) -> Program:
        for lineno, raw in enumerate(source.splitlines(), start=1):
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            try:
                self._exec(line)
            except SpectraError:
                raise
            except Exception as exc:  # surface kernel errors with line context
                raise SpectraError(f"line {lineno}: {exc}") from exc
        if self.p.report_dir is not None:
            self._write_report(Path(self.p.report_dir))
        return self.p

    def _exec(self, line: str) -> None:
        m = _RE_ZEROS.match(line)
        if m:
            self.p.zeros[m.group(1)] = int(m.group(2))
            return
        m = _RE_OPERATOR.match(line)
        if m:
            name, fam, n = m.group(1), m.group(2), int(m.group(3))
            if fam not in _FAMILIES:
                raise SpectraError(f"unknown family {fam!r}")
            self.p.operators[name] = {"family": _FAMILIES[fam], "n": n}
            return
        m = _RE_CERTIFY.match(line)
        if m:
            self._certify(*m.groups())
            return
        m = _RE_ASSERT.match(line)
        if m:
            self._assert_separated(m.group(1), float(m.group(2)))
            return
        m = _RE_PROVE_MONO.match(line)
        if m:
            panel = [int(x) for x in m.group(2).split(",") if x.strip()]
            self._prove_monotone(m.group(1), panel, m.group(3))
            return
        m = _RE_MEASURE.match(line)
        if m:
            self._measure(m.group(1), m.group(2), float(m.group(3)), int(m.group(4)),
                          m.group(5) or "emulator")
            return
        m = _RE_REPORT.match(line)
        if m:
            self.p.report_dir = m.group(1)
            return
        raise SpectraError(f"cannot parse: {line!r}")

    def _certify(self, name: str, op_name: str, zeros_name: str) -> None:
        if op_name not in self.p.operators:
            raise SpectraError(f"unknown operator {op_name!r}")
        if zeros_name not in self.p.zeros:
            raise SpectraError(f"unknown zeros set {zeros_name!r}")
        op = self.p.operators[op_name]
        k = self.p.zeros[zeros_name]
        iv = certified_family_mismatch(op["family"], op["n"], k)
        lo, hi = iv.to_tuple()
        self.p.certificates[name] = {
            "family": op["family"], "n": op["n"], "k_zeros": k,
            "lower": float(lo), "upper": float(hi),
        }

    def _assert_separated(self, cert_name: str, threshold: float) -> None:
        if cert_name not in self.p.certificates:
            raise SpectraError(f"unknown certificate {cert_name!r}")
        c = self.p.certificates[cert_name]
        # discharged_separation_proof raises if lower <= threshold: a Spectra
        # assertion cannot pass unless the kernel certifies it.
        try:
            proof = discharged_separation_proof(
                c["family"], c["n"], c["k_zeros"], threshold=threshold
            )
        except ValueError as exc:
            raise SpectraError(
                f"assertion failed: {cert_name} not certifiably separated "
                f"(certified lower {c['lower']} <= threshold {threshold}): {exc}"
            ) from exc
        self.p.assertions.append({
            "certificate": cert_name, "threshold": threshold,
            "certified_lower": c["lower"], "separated": True,
            "lean4": proof.lean4, "coq": proof.coq,
        })

    def _prove_monotone(self, fam_token: str, panel: List[int], zeros_name: str) -> None:
        if fam_token not in _FAMILIES:
            raise SpectraError(f"unknown family {fam_token!r}")
        if zeros_name not in self.p.zeros:
            raise SpectraError(f"unknown zeros set {zeros_name!r}")
        family = _FAMILIES[fam_token]
        k = self.p.zeros[zeros_name]
        # Raises if the certified lower bounds are not strictly increasing across
        # the panel: a monotonicity claim cannot pass unless the kernel backs it.
        try:
            proof = discharged_monotonicity_proof(family, panel, k)
        except ValueError as exc:
            raise SpectraError(f"monotonicity failed: {exc}") from exc
        self.p.monotonicity.append({
            "family": family, "panel": list(panel), "k_zeros": k,
            "lowers": proof.lowers, "lean4": proof.lean4, "coq": proof.coq,
        })

    def _measure(self, name: str, op_name: str, window: float, precision: int,
                 backend: str = "emulator") -> None:
        if op_name not in self.p.operators:
            raise SpectraError(f"unknown operator {op_name!r}")
        if backend not in ("emulator", "ibm-hardware"):
            raise SpectraError(f"unknown backend {backend!r} "
                               "(use 'emulator' or 'ibm-hardware')")
        op = self.p.operators[op_name]
        # QPE needs qiskit; import lazily so certify/assert work without it.
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "cr_ibm", Path(__file__).resolve().parents[3] / "scripts" / "run_curverank_ibm.py"
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        except Exception as exc:  # pragma: no cover - depends on qiskit
            raise SpectraError(f"qpe unavailable (needs qiskit): {exc}") from exc
        use_emulator = backend == "emulator"
        try:
            row = mod.run_one(
                n_basis=op["n"], n_precision=precision, shots=4096, reps=2,
                window_radius=window, use_emulator=use_emulator,
                device="ibm_brisbane", method="dense",
            )
        except Exception as exc:  # hardware needs a token; fail honestly
            raise SpectraError(
                f"qpe on backend {backend!r} failed: {exc}"
            ) from exc
        row["backend_request"] = backend
        self.p.measurements[name] = row

    def _write_report(self, out: Path) -> None:
        out.mkdir(parents=True, exist_ok=True)
        (out / "spectra_report.json").write_text(
            json.dumps(self.p.to_dict(), indent=2), encoding="utf-8"
        )
        for a in self.p.assertions:
            stem = f"{a['certificate']}_separation"
            (out / f"{stem}.lean").write_text(a["lean4"], encoding="utf-8")
            (out / f"{stem}.v").write_text(a["coq"], encoding="utf-8")
        for mono in self.p.monotonicity:
            stem = f"{mono['family']}_monotone"
            (out / f"{stem}.lean").write_text(mono["lean4"], encoding="utf-8")
            (out / f"{stem}.v").write_text(mono["coq"], encoding="utf-8")


def run_program(source: str) -> Program:
    """Run Spectra source text and return the resulting Program."""
    return Interpreter().run(source)


def run_file(path: str | Path) -> Program:
    """Run a ``.spectra`` file."""
    return Interpreter().run(Path(path).read_text(encoding="utf-8"))
