# Controllability protocol — not yet run

**Nothing in this file has been executed on a generator. There are no results
to cite.** It is written before the run so the design cannot be adjusted after
the numbers are known, and so anyone with a GPU can run it without asking.

## Question

The superformula track gives a generator a shape whose parameters are known
exactly at every frame. **Does the generated video do what it was told?**

The current pipeline cannot be asked this. It conditions one still on one
depth frame (`frames=1`), then hands that still to Wan 2.2 image-to-video with a
text prompt ("slowly rotates"). The video model never sees the parametric
motion, so whatever rotation it produces is its own invention. The commanded
parameters control frame one and nothing after it.

## Arms

All arms share the FLUX still, seed, prompt, resolution (768x1344) and length.

| arm | video conditioning |
|---|---|
| `i2v` | the current pipeline: start image + text only |
| `control` | start image + a per-frame depth control video from the renderer in `mode="batch"` |
| `control-legacy` | as `control`, but the control video comes from `mode="legacy"` |

`control` needs a depth-controllable Wan 2.x workflow (Fun Control or VACE both
take a per-frame control video). The exact node names depend on the ComfyUI
install and are **not** verified here; the renderer's output batch is the
part this repository can check.

`control-legacy` isolates the renderer fix. On clean renders the legacy
renderer's own frames already misreport rotation by up to 0.438°/frame, against
0.0032°/frame for batch mode (`results/calibration.json`) — so a model that
followed it faithfully would still move wrongly.

## Measurement

1. Estimate depth on every generated frame with a monocular depth model, record
   its name and version with the results, and threshold to a silhouette.
2. **Estimator ceiling first.** Run step 1 on the FLUX still, whose parameters
   are known, and score it with the ruler. If the ruler cannot read `m` back
   from the still, the benchmark would measure the depth estimator, not the
   video model — stop and report that.
3. Score every frame with `controllability.symmetry_order`, using the per-pitch
   thresholds frozen in `results/calibration.json`, and every sequence with
   `controllability.rotation_per_frame`.

## Domain

Commanded views must stay inside what the ruler was validated on:

- pitch in the calibration's `validated_pitch_domain` — currently **0°, 10°, 20°**
  (zero wrong commitments on the held-out split, coverage ≥ 0.5);
- `m` from 3 to 12, with `n1_2 == n1_3`;
- rotation below 0.8 x 180/m degrees per frame — above 180/m the lobes alias
  and the direction of motion is unrecoverable.

## Metrics

- **rotation error** — |recovered − commanded| degrees per frame;
- **rotation jitter** — `residual_deg`, the RMS departure of per-frame steps from
  their mean;
- **shape retention** — fraction of frames where the committed `m` equals the
  commanded one, reported against frame index so drift over time is visible;
- **abstention rate** — reported, never folded into accuracy.

## Pre-registered predictions

Recorded now so they can be wrong.

1. `i2v` rotation error is large and uncorrelated with the commanded rate,
   because the model never received it. *(High confidence.)*
2. `control` rotation error is well below `i2v`'s. *(Moderate.)*
3. `control-legacy` shows more jitter than `control`. *(Moderate.)*
4. `i2v` shape retention falls with frame index; `control` holds it. *(Low to
   moderate.)*
5. The depth estimator is the bottleneck on translucent, glossy renders and
   step 2 fails for some shapes. *(Low — and if it fails for all of them, this
   benchmark needs a different read-out before it measures anything.)*

## Reporting rules

Publish the per-frame JSON for every arm, including arms that lose. Retain
negative results. If `control` does not beat `i2v`, that goes in the track
README's first paragraph.
