"""Superformula depth conditioning: the renderer fixes and the controllability ruler.

Runs with numpy only — no torch, ComfyUI or GPU — because the node's rendering
core imports torch lazily and the ruler is plain numpy.
"""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1] / "superformula"
sys.path.insert(0, str(ROOT / "node"))
sys.path.insert(0, str(ROOT / "bench"))

import controllability as ruler  # noqa: E402
import gielis_comfy_node as node  # noqa: E402


# -- oracle: the original renderer, verbatim minus the torch conversion ------

def original_render(frames, resolution, img_size, m1_start, m1_end, m2_start, m2_end,
                    n1_1, n1_2, n1_3, yaw_start, yaw_end, pitch):
    GAMMA = 1e-9

    def _radius(phi, m, n1, n2, n3):
        t1 = np.abs(np.cos(m * phi / 4.0))
        t2 = np.abs(np.sin(m * phi / 4.0))
        return (t1 ** n2 + t2 ** n3 + GAMMA) ** (-1.0 / n1)

    u = np.linspace(-np.pi, np.pi, resolution)
    v = np.linspace(-np.pi / 2.0, np.pi / 2.0, resolution)
    U, V = np.meshgrid(u, v)
    pr = np.radians(pitch)
    R_pitch = np.array([[np.cos(pr), 0.0, np.sin(pr)], [0.0, 1.0, 0.0], [-np.sin(pr), 0.0, np.cos(pr)]])
    imgs, msks = [], []
    denom = max(1, frames - 1)
    for f in range(frames):
        t = f / denom
        m1 = m1_start + (m1_end - m1_start) * t
        m2 = m2_start + (m2_end - m2_start) * t
        yaw = np.radians(yaw_start + (yaw_end - yaw_start) * t)
        r1 = _radius(U, m1, n1_1, n1_2, n1_3)
        r2 = _radius(V, m2, n1_1, n1_2, n1_3)
        X = r1 * np.cos(U) * r2 * np.cos(V)
        Y = r1 * np.sin(U) * r2 * np.cos(V)
        Z = r2 * np.sin(V)
        cy, sy = np.cos(yaw), np.sin(yaw)
        R_yaw = np.array([[cy, -sy, 0.0], [sy, cy, 0.0], [0.0, 0.0, 1.0]])
        pts = R_pitch @ (R_yaw @ np.stack([X.ravel(), Y.ravel(), Z.ravel()]))
        Xr, Yr, Zr = pts[0], pts[1], pts[2]
        x0, x1 = Xr.min(), Xr.max()
        y0, y1 = Yr.min(), Yr.max()
        z0, z1 = Zr.min(), Zr.max()
        xs = ((Xr - x0) / ((x1 - x0) or 1.0) * (img_size - 1)).astype(np.int64)
        ys = ((Yr - y0) / ((y1 - y0) or 1.0) * (img_size - 1)).astype(np.int64)
        zs = (Zr - z0) / ((z1 - z0) or 1.0)
        flat = ys * img_size + xs
        depth = np.zeros(img_size * img_size)
        np.maximum.at(depth, flat, zs)
        count = np.zeros(img_size * img_size)
        np.add.at(count, flat, 1.0)
        depth = np.nan_to_num(depth, nan=0.0, posinf=1.0, neginf=0.0)
        imgs.append(depth.reshape(img_size, img_size).astype(np.float32))
        msks.append((count.reshape(img_size, img_size) > 0).astype(np.float32))
    return np.stack(imgs), np.stack(msks)


SHAPE = dict(m1_start=6.0, m1_end=6.0, m2_start=0.0, m2_end=0.0,
             n1_1=1.0, n1_2=1.0, n1_3=1.0, pitch=10.0)


def render(**kw):
    args = dict(frames=4, resolution=96, width=256, height=256,
                yaw_start=0.0, yaw_end=90.0, **SHAPE)
    args.update(kw)
    return node.render_frames(**args)


def coverage(depth, mode, **kw):
    """Fraction of the TRUE silhouette on which the render carries a depth value.

    The truth is a dense render (2048 samples per axis) under the same mode and
    transform, with sub-pixel gaps closed. Two cheaper metrics were tried first
    and both were wrong, in opposite directions: counting empty pixels between
    a row's first and last hit scores a star's real concavities as holes, and
    counting background that cannot reach the border scores a sparse dot cloud
    as nearly hole-free, because the gaps between dots leak outward.
    """
    dense = dict(kw, resolution=2048)
    if mode == "batch":
        dense.update(fill_holes=False, density="fixed")
    ref_depth, ref_occ, _ = node.render_frames(mode=mode, **dense)
    _, truth = node.fill_interior(ref_depth[0], ref_occ[0], 2)
    return ((depth[0] > 0) & truth).sum() / truth.sum()


# -- backwards compatibility -------------------------------------------------

@pytest.mark.parametrize("params", [
    dict(frames=3, resolution=64, img_size=256, m1_start=5.0, m1_end=5.0, m2_start=0.0, m2_end=5.0,
         n1_1=1.0, n1_2=1.0, n1_3=1.0, yaw_start=0.0, yaw_end=360.0, pitch=30.0),
    dict(frames=2, resolution=48, img_size=192, m1_start=3.0, m1_end=8.0, m2_start=2.0, m2_end=2.0,
         n1_1=0.6, n1_2=1.4, n1_3=0.9, yaw_start=-40.0, yaw_end=75.0, pitch=-20.0),
])
def test_legacy_mode_is_bit_identical_to_the_original(params):
    """Every published example must stay reproducible."""
    want_depth, want_mask = original_render(**params)
    got_depth, got_mask, _ = node.render_frames(
        mode="legacy", width=params["img_size"], height=params["img_size"],
        **{k: v for k, v in params.items() if k != "img_size"})
    assert np.array_equal(got_depth, want_depth)
    assert np.array_equal(got_mask.astype(np.float32), want_mask)


def test_existing_graphs_stay_valid():
    """New inputs are optional, so a graph written for the original node still loads."""
    spec = node.Gielis3DBatchRenderer.INPUT_TYPES()
    assert list(spec["required"]) == [
        "frames", "resolution", "img_size", "m1_start", "m1_end", "m2_start", "m2_end",
        "n1_1", "n1_2", "n1_3", "yaw_start", "yaw_end", "pitch"]
    assert set(spec["optional"]) == {"mode", "width", "height", "fill_holes", "surface_floor"}
    assert node.Gielis3DBatchRenderer.RETURN_TYPES == ("IMAGE", "MASK")


def test_the_core_imports_without_torch():
    assert "torch" not in node.__dict__


def test_legacy_rejects_non_square():
    with pytest.raises(ValueError):
        render(mode="legacy", width=256, height=384)


def test_unknown_mode_is_rejected():
    with pytest.raises(ValueError):
        render(mode="fast")


# -- the four defects, measured on the original, fixed in batch mode ---------

def test_defect_1_legacy_leaves_most_of_the_silhouette_without_depth():
    # 64 samples on a 512 canvas is the node defaults' ratio (128 on 1024).
    kw = dict(frames=1, width=512, height=512, yaw_start=0.0, yaw_end=0.0, **SHAPE)
    legacy, _, _ = node.render_frames(mode="legacy", resolution=64, **kw)
    fixed, _, _ = node.render_frames(mode="batch", resolution=64, **kw)
    assert coverage(legacy, "legacy", **kw) < 0.10
    assert coverage(fixed, "batch", **kw) > 0.99


def test_defect_2_background_is_distinct_from_the_farthest_surface():
    depth, mask, meta = render()
    assert depth[~mask].max() == 0.0
    assert depth[mask].min() >= meta["surface_floor"] - 1e-6
    assert meta["surface_floor"] > 0


def test_defect_3_one_depth_mapping_for_the_whole_batch():
    """A constant world depth must map to the same grey in every frame."""
    _, _, legacy = render(mode="legacy")
    ranges = {tuple(f["z_range"]) for f in legacy["frames"]}
    assert len(ranges) > 1, "fixture should exercise the legacy per-frame renormalisation"
    _, _, batch = render()
    assert "z_range" in batch and all("z_range" not in f for f in batch["frames"])


def test_defect_4_one_isotropic_pixel_scale_for_the_whole_batch():
    _, _, legacy = render(mode="legacy")
    scales = np.array([f["px_per_unit"] for f in legacy["frames"]])
    assert np.ptp(scales[:, 0]) > 0 or np.any(scales[:, 0] != scales[:, 1])
    _, _, batch = render()
    sx, sy = batch["px_per_unit"]
    assert sx == sy


def test_renders_at_the_generator_aspect_instead_of_being_stretched_to_it():
    depth, mask, _ = render(frames=1, width=192, height=336, yaw_end=0.0)
    assert depth.shape == (1, 336, 192)
    ys, xs = np.nonzero(mask[0])
    # A 6-lobed top-down-ish supershape is about as wide as it is tall; a square
    # map squashed to 192x336 would make it 1.75x taller than wide.
    assert 0.8 < (np.ptp(xs) + 1) / (np.ptp(ys) + 1) < 1.25


def test_hole_filling_does_not_grow_the_silhouette():
    depth, mask, _ = render(fill_holes=False)
    grown = node._dilate(mask[0], 3)
    _, filled, _ = render()
    assert np.all(grown | ~filled[0])


def test_batch_render_is_deterministic():
    a = render()
    b = render()
    assert np.array_equal(a[0], b[0]) and np.array_equal(a[1], b[1])


# -- the ruler ----------------------------------------------------------------

@pytest.mark.parametrize("m", [3, 4, 5, 7, 9, 12])
def test_recovers_lobe_count_top_down(m):
    _, mask, _ = render(frames=1, m1_start=m, m1_end=m, pitch=0.0, yaw_start=33.0, yaw_end=33.0)
    got = ruler.symmetry_order(mask[0])
    assert got["m"] == m, got


def test_abstains_on_a_round_outline():
    yy, xx = np.mgrid[:128, :128]
    disc = (yy - 64) ** 2 + (xx - 64) ** 2 < 40 ** 2
    assert ruler.symmetry_order(disc)["m"] is None


def test_abstains_on_an_empty_mask():
    assert ruler.symmetry_order(np.zeros((32, 32), dtype=bool))["m"] is None


def test_whitening_undoes_a_square_to_portrait_stretch():
    """The ruler must be immune to the stretch the generator is not."""
    _, mask, _ = render(frames=1, m1_start=5, m1_end=5, pitch=0.0, yaw_start=0.0, yaw_end=0.0)
    squashed = np.repeat(mask[0], 2, axis=0)[:, ::1]  # 2x taller
    assert ruler.symmetry_order(squashed)["m"] == 5


def test_recovers_commanded_rotation():
    _, masks, _ = render(frames=13, m1_start=5, m1_end=5, pitch=0.0, yaw_start=0.0, yaw_end=36.0)
    got = ruler.rotation_per_frame(masks, 5)
    assert got["deg_per_frame"] == pytest.approx(3.0, abs=0.02)
    assert got["residual_deg"] < 0.1
    assert got["aliasing_limit_deg"] == pytest.approx(36.0)


def test_rotation_beyond_the_aliasing_limit_is_not_recovered():
    """Stated limit, asserted: above 180/m deg per frame the lobes alias."""
    m = 6
    _, masks, _ = render(frames=6, m1_start=m, m1_end=m, pitch=0.0, yaw_start=0.0, yaw_end=5 * 40.0)
    got = ruler.rotation_per_frame(masks, m)
    assert abs(got["deg_per_frame"] - 40.0) > 5.0


def test_shipped_calibration_has_no_wrong_commitments_inside_its_domain():
    data = json.loads((ROOT / "bench" / "results" / "calibration.json").read_text())
    assert data["validated_pitch_domain"], "calibration validated no pitch at all"
    for pitch in data["validated_pitch_domain"]:
        assert data["held_out"][str(pitch)]["wrong"] == 0
