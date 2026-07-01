#!/usr/bin/env python3
"""Run the NetGap noise layer: realistic channels + entanglement distribution.

Primitives: ``channels`` (amplitude/phase/depolarizing fidelity + quantum-advantage
floor, netgap-0006), ``distribution`` (entanglement over a lossy+noisy link, netgap-0007),
or ``all``.

Finite exact single-qubit CPTP models and entanglement criteria only; not a
device-calibrated noise model, finite-key proof, or hardware rate guarantee.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gaugegap.ledger import git_state, object_hash, utc_run_id, write_jsonl  # noqa: E402
from gaugegap.quantum.quantum_channel import CLAIM_BOUNDARY, noise_report  # noqa: E402

PRIMITIVE_TO_HYPOTHESIS = {"channels": "netgap-0006", "distribution": "netgap-0007", "all": "netgap-0006"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--primitive", choices=["channels", "distribution", "all"], default="all")
    ap.add_argument("--eta", type=float, default=0.9)
    ap.add_argument("--gamma", type=float, default=0.1, help="amplitude damping (T1)")
    ap.add_argument("--lam", type=float, default=0.05, help="phase damping (T2)")
    ap.add_argument("--emit-certificates", action="store_true")
    ap.add_argument("--output-dir", type=Path, default=None)
    args = ap.parse_args(argv)

    report = noise_report(eta=args.eta, gamma=args.gamma, lam=args.lam)
    hypothesis_id = PRIMITIVE_TO_HYPOTHESIS[args.primitive]
    if args.primitive == "channels":
        selected = {"channels": report["channels"]}
    elif args.primitive == "distribution":
        selected = {"distribution": report["distribution"]}
    else:
        selected = report

    config = {"eta": args.eta, "gamma": args.gamma, "lam": args.lam}
    payload = {
        "hypothesis_id": hypothesis_id,
        "track": "NetGap",
        "primitive": args.primitive,
        "run_id": utc_run_id(),
        "git": git_state(ROOT),
        "config": config,
        "config_hash": object_hash(config),
        "claim_boundary": CLAIM_BOUNDARY,
        "report": selected,
    }

    out = args.output_dir or (ROOT / "results" / hypothesis_id)
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{hypothesis_id}-{args.primitive}.json").write_text(json.dumps(payload, indent=2, sort_keys=True, default=str))
    write_jsonl(out / f"{hypothesis_id}-records.jsonl", [payload])
    if args.emit_certificates:
        amp = report["channels"]["amplitude"]["certificate"]
        (out / "netgap_advantage.lean").write_text(amp["lean4"])
        (out / "netgap_advantage.v").write_text(amp["coq"])
        dl = report["distribution"]["certificate"]
        (out / "netgap_distillability.lean").write_text(dl["lean4"])
        (out / "netgap_distillability.v").write_text(dl["coq"])

    ch, dist = report["channels"], report["distribution"]
    print("=" * 72)
    print(f"NetGap noise layer: primitive={args.primitive}")
    for kind in ("amplitude", "phase", "depolarizing"):
        c = ch[kind]
        print(f"  [0006] {kind:<12} F_avg={c['average_fidelity']:.4f} beats_classical={c['beats_classical_bound']}")
    print(
        f"  [0007] distribution eta={dist['eta']} gamma={dist['gamma']} lam={dist['lam']}: "
        f"singlet_fraction={dist['singlet_fraction']:.4f} concurrence={dist['concurrence']:.4f} "
        f"distillable={dist['distillable']} rate={dist['raw_distribution_rate']:.4f}"
    )
    print(f"  CLAIM BOUNDARY: {CLAIM_BOUNDARY}")
    print(f"  wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
