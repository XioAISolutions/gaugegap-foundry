#!/usr/bin/env python3
"""Run the NetGap network-layer primitives and emit reproducible evidence.

Primitives: ``clements`` (Reck mesh decomposition, netgap-0002), ``swap``
(entanglement swapping, netgap-0003), ``loss`` (heralded loss budget, netgap-0004),
``qkd`` (BB84 key rate, netgap-0005), or ``all``.

Finite exact idealized models only; not hardware, device-loss, or full-security-proof
claims.
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
from gaugegap.quantum.quantum_network import CLAIM_BOUNDARY, network_report  # noqa: E402

PRIMITIVE_TO_HYPOTHESIS = {
    "clements": "netgap-0002",
    "swap": "netgap-0003",
    "loss": "netgap-0004",
    "qkd": "netgap-0005",
    "all": "netgap-0002",
}
REPORT_KEY = {"clements": "clements", "swap": "entanglement_swap", "loss": "loss_budget", "qkd": "qkd"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--primitive", choices=[*REPORT_KEY, "all"], default="all")
    ap.add_argument("--modes", type=int, default=4)
    ap.add_argument("--eta", type=float, default=0.9)
    ap.add_argument("--switches", type=int, default=5)
    ap.add_argument("--qber", type=float, default=0.05)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--emit-certificates", action="store_true")
    ap.add_argument("--output-dir", type=Path, default=None)
    args = ap.parse_args(argv)

    report = network_report(
        n_modes=args.modes, eta=args.eta, k=args.switches, qber=args.qber, seed=args.seed
    )
    hypothesis_id = PRIMITIVE_TO_HYPOTHESIS[args.primitive]
    selected = report if args.primitive == "all" else {REPORT_KEY[args.primitive]: report[REPORT_KEY[args.primitive]]}

    config = {"modes": args.modes, "eta": args.eta, "switches": args.switches, "qber": args.qber, "seed": args.seed}
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
        for name, block in (("loss", report["loss_budget"]), ("qkd", report["qkd"])):
            cert = block.get("certificate", {})
            if cert:
                (out / f"netgap_{name}.lean").write_text(cert["lean4"])
                (out / f"netgap_{name}.v").write_text(cert["coq"])

    print("=" * 72)
    print(f"NetGap network layer: primitive={args.primitive}")
    c, sw = report["clements"], report["entanglement_swap"]
    lo, qk = report["loss_budget"], report["qkd"]
    print(f"  [0002] Clements/Reck reconstruction error: {c['reconstruction_error']:.2e} ({c['num_couplers']} couplers)")
    print(f"  [0003] entanglement swap: all outcomes maximally entangled = {sw['all_outcomes_maximally_entangled']}")
    print(f"  [0004] loss budget eta={lo['eta']} x{lo['k']}: success={lo['success_probability']:.4f}, monotone={lo['loss_is_monotone']}")
    print(f"  [0005] BB84 Q={qk['qber']}: key_rate={qk['key_rate']:.4f}, secure={qk['secure']} (threshold Q~{qk['secure_threshold_qber']})")
    print(f"  CLAIM BOUNDARY: {CLAIM_BOUNDARY}")
    print(f"  wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
