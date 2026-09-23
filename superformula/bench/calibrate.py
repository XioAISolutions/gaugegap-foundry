"""Calibrate the controllability ruler on clean renders, then freeze it.

    python superformula/bench/calibrate.py --out superformula/bench/results/calibration.json

Nothing here touches a generator. Every silhouette is rendered from exactly
known parameters, so this measures the *ruler*, not a video model: if the ruler
cannot read the lobe count or the rotation back from a perfect render, no
verdict it later gives on generated video means anything.

Discipline, borrowed from the EJA frozen-calibration lane:

* two disjoint splits — different seeds, yaws, and n1 values;
* the abstention threshold for each pitch is chosen on the calibration split
  only, as the smallest confidence that admits zero wrong commitments there;
* the held-out split is scored with those thresholds frozen, and its wrong
  answers are reported, not re-tuned away.

A pitch where the held-out split still commits wrong answers is outside the
ruler's validated domain, and PROTOCOL.md forbids commanding views there.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "node"))

import controllability as ruler  # noqa: E402
import gielis_comfy_node as node  # noqa: E402

PITCHES = [0, 10, 20, 30, 40, 50, 60]
ORDERS = list(range(3, 13))
SPLITS = {
    "calibration": {"seed": 11, "n1": [0.6, 1.0, 1.6, 2.2]},
    "held_out": {"seed": 29, "n1": [0.8, 1.3, 1.9]},
}
CANVAS = 384


def _silhouette(m, n1, pitch, yaw, mode="batch", frames=1, yaw_end=None):
    _, masks, _ = node.render_frames(
        frames=frames, resolution=128, width=CANVAS, height=CANVAS,
        m1_start=m, m1_end=m, m2_start=0.0, m2_end=0.0, n1_1=n1,
        yaw_start=yaw, yaw_end=yaw if yaw_end is None else yaw_end, pitch=pitch, mode=mode,
    )
    return masks


def _observe(split):
    rng = np.random.default_rng(SPLITS[split]["seed"])
    rows = []
    for pitch in PITCHES:
        for m in ORDERS:
            for n1 in SPLITS[split]["n1"]:
                yaw = float(rng.uniform(0.0, 360.0))
                r = ruler.symmetry_order(_silhouette(m, n1, pitch, yaw)[0], min_confidence=0.0)
                rows.append({"pitch": pitch, "m": m, "n1": n1, "yaw": round(yaw, 3),
                             "m_hat": r["m"], "confidence": round(r["confidence"], 4)})
    return rows


def _freeze_thresholds(rows):
    """Per pitch: the smallest threshold with zero wrong commitments on calibration."""
    thresholds = {}
    for pitch in PITCHES:
        wrong = [r["confidence"] for r in rows
                 if r["pitch"] == pitch and r["m_hat"] is not None and r["m_hat"] != r["m"]]
        thresholds[pitch] = round(max([ruler.DEFAULT_MIN_CONFIDENCE] + [w + 1e-3 for w in wrong]), 4)
    return thresholds


def _score(rows, thresholds):
    table = {}
    for pitch in PITCHES:
        sel = [r for r in rows if r["pitch"] == pitch]
        tau = thresholds[pitch]
        committed = [r for r in sel if r["m_hat"] is not None and r["confidence"] >= tau]
        correct = sum(r["m_hat"] == r["m"] for r in committed)
        wrong = [r for r in committed if r["m_hat"] != r["m"]]
        table[pitch] = {
            "n": len(sel),
            "threshold": tau,
            "correct": correct,
            "abstained": len(sel) - len(committed),
            "wrong": len(wrong),
            "coverage": round(len(committed) / len(sel), 3),
            "wrong_examples": [f"{r['m']}->{r['m_hat']} (n1={r['n1']}, conf {r['confidence']:.2f})"
                               for r in wrong[:5]],
        }
    return table


def _rotation(mode):
    """Rotation read-back on 17-frame sweeps: commanded vs recovered deg/frame."""
    rows = []
    for pitch in (0, 10, 20, 30):
        for m in (3, 5, 7):
            for rate in (1.0, 3.0, 0.8 * 180.0 / m):   # the last one is near the aliasing limit
                masks = _silhouette(m, 1.0, pitch, 10.0, mode=mode, frames=17, yaw_end=10.0 + 16 * rate)
                r = ruler.rotation_per_frame(masks, m)
                rows.append({"pitch": pitch, "m": m, "commanded": round(rate, 3),
                             "recovered": round(r["deg_per_frame"], 4),
                             "abs_error": round(abs(r["deg_per_frame"] - rate), 4),
                             "residual": round(r["residual_deg"], 4)})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", help="Write results as JSON")
    args = parser.parse_args()

    calibration = _observe("calibration")
    thresholds = _freeze_thresholds(calibration)
    held_out = _observe("held_out")
    held_table = _score(held_out, thresholds)
    validated = [p for p in PITCHES if held_table[p]["wrong"] == 0 and held_table[p]["coverage"] >= 0.5]

    print("symmetry order, held-out split, thresholds frozen on the calibration split")
    print(f"  {'pitch':>5} {'tau':>6} {'correct':>8} {'abstain':>8} {'wrong':>6} {'coverage':>9}")
    for p in PITCHES:
        t = held_table[p]
        print(f"  {p:>5} {t['threshold']:>6.3f} {t['correct']:>5}/{t['n']:<2} {t['abstained']:>8} "
              f"{t['wrong']:>6} {t['coverage']:>9.2f}  {'; '.join(t['wrong_examples'][:2])}")
    print(f"  validated domain (0 wrong, coverage >= 0.5): pitch in {validated}")

    rotation = {mode: _rotation(mode) for mode in ("batch", "legacy")}
    print("\nrotation read-back, 17-frame sweeps (deg/frame)")
    for mode, rows in rotation.items():
        errs = np.array([r["abs_error"] for r in rows])
        print(f"  {mode:<7} median |error| {np.median(errs):.4f}   max |error| {errs.max():.4f}"
              f"   ({len(rows)} sweeps, pitch 0-30)")

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({
            "canvas": CANVAS,
            "splits": SPLITS,
            "thresholds_frozen_on_calibration": thresholds,
            "held_out": held_table,
            "validated_pitch_domain": validated,
            "rotation": rotation,
            "calibration_rows": calibration,
            "held_out_rows": held_out,
        }, indent=1), encoding="utf-8")
        print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
