#!/usr/bin/env python3
"""Data sonification and the sampling limit: the honest core behind "LHC data sounds
like Saturn's rings".

Shows (1) two INDEPENDENT datasets, sonified with the same band-limited mapping, score
high spectral similarity -- so auditory resemblance is NOT evidence of a shared source;
and (2) the Nyquist aliasing fold: a tone above f_s/2 folds to an in-band impostor,
with a discharged Lean 4 / Coq certificate.

CLAIM BOUNDARY: a finite, exact signal-processing demonstration. Sonification is a
data-to-audio mapping; there is no special LHC<->Saturn link. The sampling/aliasing
statements are exact Fourier theorems.
"""
from __future__ import annotations
import argparse, json, sys, warnings
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]; SRC = ROOT / "src"
if str(SRC) not in sys.path: sys.path.insert(0, str(SRC))
warnings.filterwarnings("ignore")
from gaugegap.quantum.sonification import (
    analyze_sonification, alias_frequency, demo_datasets, power_spectrum, sonify)
from gaugegap.visualization.svg import SVGCanvas


def _plot_spectra(path, sample_rate, f_min, f_max, seed):
    a, b = demo_datasets(seed=seed)
    fa, pa = power_spectrum(sonify(a, sample_rate=sample_rate, f_min=f_min, f_max=f_max),
                            sample_rate)
    fb, pb = power_spectrum(sonify(b, sample_rate=sample_rate, f_min=f_min, f_max=f_max),
                            sample_rate)
    mask = fa <= f_max * 1.3
    fa, pa, pb = fa[mask], pa[mask], pb[: mask.sum()]
    W = H = 520; pad = 60
    c = SVGCanvas(W, H)
    fmax = fa.max() or 1.0; pmax = max(pa.max(), pb.max()) or 1.0
    c.line(pad, H - pad, W - pad, H - pad, stroke="#30363d")
    c.line(pad, pad, pad, H - pad, stroke="#30363d")
    def tf(fr, p):
        return (pad + fr / fmax * (W - 2 * pad), (H - pad) - p / pmax * (H - 2 * pad))
    c.polyline([tf(x, y) for x, y in zip(fa, pa)], stroke="#58a6ff", stroke_width=1.4)
    c.polyline([tf(x, y) for x, y in zip(fa, pb)], stroke="#f0c674", stroke_width=1.4)
    c.text(W / 2, 26, "Two UNRELATED datasets, sonified", size=14)
    c.text(W / 2, H - 22, "frequency (Hz)  -  spectra resemble each other anyway",
           size=11, fill="#8b949e")
    c.write(path)


def _plot_aliasing(path, sample_rate):
    fs = sample_rate
    fin = np.linspace(0, fs, 400)
    fapp = np.array([alias_frequency(f, fs) for f in fin])
    W = H = 520; pad = 60
    c = SVGCanvas(W, H)
    def tf(x, y):
        return (pad + x / fs * (W - 2 * pad), (H - pad) - y / (fs / 2) * (H - 2 * pad))
    c.line(pad, H - pad, W - pad, H - pad, stroke="#30363d")
    c.line(pad, pad, pad, H - pad, stroke="#30363d")
    # Nyquist line
    xn = pad + 0.5 * (W - 2 * pad)
    c.line(xn, pad, xn, H - pad, stroke="#8b949e", stroke_width=1.0, opacity=0.5)
    c.polyline([tf(x, y) for x, y in zip(fin, fapp)], stroke="#7ee787", stroke_width=2.0)
    c.text(W / 2, 26, "Aliasing fold: apparent vs true frequency", size=14)
    c.text(xn, pad + 14, "Nyquist f_s/2", size=10, fill="#8b949e", anchor="middle")
    c.text(W / 2, H - 22, "true frequency  ->  folds back below Nyquist", size=11,
           fill="#8b949e")
    c.write(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sample-rate", type=float, default=8000.0)
    ap.add_argument("--f-min", type=float, default=200.0)
    ap.add_argument("--f-max", type=float, default=2000.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--output-dir", type=Path, default=ROOT / "results" / "sonification")
    ap.add_argument("--skip-audit", action="store_true")
    args = ap.parse_args()

    r = analyze_sonification(sample_rate=args.sample_rate, f_min=args.f_min,
                             f_max=args.f_max, seed=args.seed)
    print("=" * 72)
    print("Sonification & the sampling limit")
    print("=" * 72)
    print(f"  sample rate / Nyquist     : {r.sample_rate:.0f} Hz / {r.nyquist:.0f} Hz")
    print(f"  content band f_max         : {r.f_max_used:.0f} Hz (within band: "
          f"{r.within_band})")
    print(f"  aliasing fold             : {r.alias_example_freq:.0f} Hz tone -> "
          f"{r.alias_example_alias:.0f} Hz impostor")
    print(f"  self-similarity (control) : {r.self_similarity:.3f}")
    print(f"  UNRELATED-pair similarity : {r.unrelated_similarity:.3f}  "
          f"(spurious: {r.similarity_is_spurious})")
    print("  => high spectral similarity between independent datasets means "
          "'sounds alike' is NOT evidence of shared physics.")

    out = args.output_dir; out.mkdir(parents=True, exist_ok=True)
    payload = dict(r.to_dict())
    payload["lean4_certificate"] = r.lean4
    payload["coq_certificate"] = r.coq
    (out / "sonification.json").write_text(json.dumps(payload, indent=2, sort_keys=True))
    (out / "aliasing_fold.lean").write_text(r.lean4)
    (out / "aliasing_fold.coq").write_text(r.coq)
    _plot_spectra(out / "unrelated_spectra.svg", args.sample_rate, args.f_min,
                  args.f_max, args.seed)
    _plot_aliasing(out / "aliasing_fold.svg", args.sample_rate)

    holes = ("sorry" in r.lean4) or ("Admitted" in r.coq)
    (out / "sonification.md").write_text(
        "# Sonification & the sampling limit\n\n"
        "The honest core behind \"LHC data sounds like Saturn's rings\". Sonification "
        "(CERN's LHCsound, NASA's Chandra/Cassini) maps data to audio -- a real, useful "
        "technique -- but it is a **mapping**, not physics. Two **independent** datasets, "
        "sonified with the same band-limited mapping, score "
        f"**{r.unrelated_similarity:.2f}** spectral cosine similarity (vs the self-"
        f"similarity control of {r.self_similarity:.2f}); high resemblance between "
        "unrelated data means *auditory similarity is not evidence of a shared source*. "
        "The rigorous, certifiable content is the **Nyquist-Shannon sampling limit**: a "
        f"tone above the Nyquist frequency ({r.nyquist:.0f} Hz) folds to an in-band "
        f"impostor ({r.alias_example_freq:.0f} Hz -> {r.alias_example_alias:.0f} Hz), "
        "with a discharged Lean 4 / Coq certificate of the fold "
        "`f_s/2 < f < f_s => 0 < f_s - f < f_s/2`. **Claim boundary:** a finite, exact "
        "signal-processing demonstration; there is no special LHC<->Saturn link; the "
        "sampling/aliasing statements are exact Fourier theorems. Not a "
        "continuum/Millennium claim.\n\n"
        f"- Nyquist = {r.nyquist:.0f} Hz; content within band = {r.within_band}\n"
        f"- aliasing fold {r.alias_example_freq:.0f} Hz -> {r.alias_example_alias:.0f} "
        f"Hz; certificate hole-free = {not holes}\n"
        f"- unrelated-pair spectral similarity = **{r.unrelated_similarity:.3f}** "
        f"(spurious resemblance)\n\n"
        "![unrelated spectra](unrelated_spectra.svg)\n\n"
        "![aliasing fold](aliasing_fold.svg)\n\n"
        "_Generated by `scripts/run_sonification.py`._\n")
    print(f"\nReport: {out / 'sonification.json'} (+ .md, .svg, .lean, .coq)")
    print(f"  certificate hole-free: {not holes}")

    if not args.skip_audit:
        import subprocess
        rel = (out / "sonification.md").resolve().relative_to(ROOT)
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "claim_boundary_audit.py"),
             "--include", str(rel), "--strict"], capture_output=True, text=True)
        print(f"  claim-boundary audit: "
              f"{'PASS (0 high)' if proc.returncode == 0 else 'FAIL'}")
        if proc.returncode != 0:
            sys.stderr.write(proc.stdout + proc.stderr)
            return 1
    return 0 if (r.similarity_is_spurious and not holes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
