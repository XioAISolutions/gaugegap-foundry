# Gielis 3D Superformula batch renderer for ComfyUI.
#
# Concept: procedural 3D supershapes -> depth-map frame batches for
# ControlNet / control-video conditioned generation.
#
# This file stays a single module on purpose: installation is "copy this file
# into ComfyUI/custom_nodes/". The rendering core below is pure numpy and has no
# torch import at module level, so it can be tested and benchmarked without
# ComfyUI, torch or a GPU (tests/test_superformula_depth.py). torch is imported
# only inside the node method that hands tensors to ComfyUI.
#
# Two render modes:
#
#   mode="legacy"  reproduces the original renderer bit for bit, so every
#                  published example stays reproducible. It has four measured
#                  defects: at the node's defaults the silhouette is ~97% holes
#                  (16k points splatted onto 1M pixels); holes and background
#                  share the value 0, so the interior reads as punched through;
#                  z is renormalised per frame, so a fixed world depth maps to a
#                  different grey in different frames; and x and y are
#                  normalised independently per frame, so the shape is stretched
#                  anisotropically and its scale pumps as it rotates.
#
#   mode="batch"   (default) samples the surface densely enough for the canvas,
#                  fills the remaining gaps inside the silhouette, keeps the
#                  background distinct from the farthest surface, and fixes one
#                  isotropic world->pixel transform and one depth mapping for the
#                  whole batch. Every frame of a sequence is then on the same
#                  scale, which is what a control *video* needs.
#
# width/height render the depth map at the generator's aspect ratio directly.
# Stretching a square depth map to a portrait latent (the original batch graph
# scaled 1024x1024 to 768x1344 with crop disabled) squashes the geometry 0.571x
# horizontally before the model ever sees it.
import numpy as np

GAMMA = 1e-9
MODES = ("batch", "legacy")


# --------------------------------------------------------------------------
# geometry
# --------------------------------------------------------------------------

def superformula_radius(phi, m, n1, n2, n3):
    """Gielis superformula with a = b = 1; GAMMA guards the 0 ** negative case."""
    t1 = np.abs(np.cos(m * phi / 4.0))
    t2 = np.abs(np.sin(m * phi / 4.0))
    return (t1 ** n2 + t2 ** n3 + GAMMA) ** (-1.0 / n1)


def _pitch_matrix(pitch_deg):
    pr = np.radians(pitch_deg)
    return np.array([[np.cos(pr), 0.0, np.sin(pr)],
                     [0.0, 1.0, 0.0],
                     [-np.sin(pr), 0.0, np.cos(pr)]])


def _yaw_matrix(yaw_deg):
    cy, sy = np.cos(np.radians(yaw_deg)), np.sin(np.radians(yaw_deg))
    return np.array([[cy, -sy, 0.0], [sy, cy, 0.0], [0.0, 0.0, 1.0]])


def surface_points(u_res, v_res, m1, m2, n1, n2, n3, yaw_deg, pitch_deg, sanitize=True):
    """Rotated supershape surface samples as a (3, u_res * v_res) array.

    The view looks down the z axis: pitch 0 is top-down, so yaw is then an
    exact image-plane rotation. Larger z is nearer the viewer. `sanitize`
    replaces any non-finite coordinate with 0; the legacy renderer turns it off
    so that it stays bit-identical to the original, which did not.
    """
    u = np.linspace(-np.pi, np.pi, u_res)
    v = np.linspace(-np.pi / 2.0, np.pi / 2.0, v_res)
    U, V = np.meshgrid(u, v)
    r1 = superformula_radius(U, m1, n1, n2, n3)
    r2 = superformula_radius(V, m2, n1, n2, n3)
    X = r1 * np.cos(U) * r2 * np.cos(V)
    Y = r1 * np.sin(U) * r2 * np.cos(V)
    Z = r2 * np.sin(V)
    pts = np.stack([X.ravel(), Y.ravel(), Z.ravel()])
    pts = _pitch_matrix(pitch_deg) @ (_yaw_matrix(yaw_deg) @ pts)
    return np.nan_to_num(pts, nan=0.0, posinf=0.0, neginf=0.0) if sanitize else pts


def frame_parameters(frames, m1_start, m1_end, m2_start, m2_end, yaw_start, yaw_end):
    """Deterministic linear interpolation of the animated parameters."""
    denom = max(1, frames - 1)
    out = []
    for f in range(frames):
        t = f / denom
        out.append({
            "m1": m1_start + (m1_end - m1_start) * t,
            "m2": m2_start + (m2_end - m2_start) * t,
            "yaw": yaw_start + (yaw_end - yaw_start) * t,
        })
    return out


# --------------------------------------------------------------------------
# raster helpers (numpy only: no scipy dependency inside ComfyUI)
# --------------------------------------------------------------------------

_NEIGHBOURS = [(dy, dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy, dx) != (0, 0)]


def _shift(a, dy, dx, fill):
    """Shift a 2D array by (dy, dx), filling the vacated border with `fill`."""
    out = np.full_like(a, fill)
    h, w = a.shape
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = a[ys, xs]
    return out


def _dilate(mask, radius):
    for _ in range(radius):
        grown = mask.copy()
        for dy, dx in _NEIGHBOURS:
            grown |= _shift(mask, dy, dx, False)
        mask = grown
    return mask


def _erode(mask, radius):
    for _ in range(radius):
        shrunk = mask.copy()
        for dy, dx in _NEIGHBOURS:
            shrunk &= _shift(mask, dy, dx, False)
        mask = shrunk
    return mask


def fill_interior(depth, occupied, radius, max_iter=64):
    """Close the silhouette, then fill its empty pixels from valid neighbours.

    Returns (filled_depth, silhouette). Pixels outside the closed silhouette are
    background and stay 0. A fill value is the mean of the already-known
    8-neighbours, grown inward one ring per iteration, so it interpolates the
    surrounding surface instead of inventing a new one.
    """
    silhouette = _erode(_dilate(occupied, radius), radius) | occupied
    vals = np.where(occupied, depth, 0.0)
    known = occupied.copy()
    for _ in range(max_iter):
        todo = silhouette & ~known
        if not todo.any():
            break
        total = np.zeros_like(vals)
        count = np.zeros_like(vals)
        for dy, dx in _NEIGHBOURS:
            k = _shift(known, dy, dx, False)
            total += np.where(k, _shift(vals, dy, dx, 0.0), 0.0)
            count += k
        new = todo & (count > 0)
        if not new.any():
            break
        vals[new] = total[new] / count[new]
        known |= new
    return np.where(silhouette, vals, 0.0), silhouette


# --------------------------------------------------------------------------
# renderers
# --------------------------------------------------------------------------

def _legacy_frame(resolution, img_size, m1, m2, n1, n2, n3, yaw, pitch):
    """The original renderer, preserved exactly (see the header for its defects)."""
    Xr, Yr, Zr = surface_points(resolution, resolution, m1, m2, n1, n2, n3, yaw, pitch, sanitize=False)
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
    meta = {
        "z_range": [float(z0), float(z1)],
        "px_per_unit": [float((img_size - 1) / ((x1 - x0) or 1.0)),
                        float((img_size - 1) / ((y1 - y0) or 1.0))],
    }
    return (depth.reshape(img_size, img_size),
            count.reshape(img_size, img_size) > 0, meta)


def auto_grid(width, height, resolution):
    """Surface sampling dense enough that neighbouring samples land ~1.5 px apart.

    Around the equator u spans the full circumference (about pi * extent pixels)
    and v half of it, so u needs roughly twice the samples of v. The user's
    `resolution` is a floor, never lowered.
    """
    extent = max(width, height)
    v_res = int(max(resolution, np.ceil(extent / 1.5)))
    u_res = int(max(resolution, np.ceil(2.0 * extent / 1.5)))
    return min(u_res, 4096), min(v_res, 2048)


def render_frames(frames=16, resolution=128, width=1024, height=1024,
                  m1_start=5.0, m1_end=5.0, m2_start=0.0, m2_end=5.0,
                  n1_1=1.0, n1_2=1.0, n1_3=1.0,
                  yaw_start=0.0, yaw_end=360.0, pitch=30.0,
                  mode="batch", fill_holes=True, hole_radius=3,
                  surface_floor=0.08, margin=0.04, density="auto"):
    """Render a depth-frame batch. Returns (depth[N,H,W] f32, mask[N,H,W] bool, meta).

    depth is 1.0 at the nearest surface point and decreases away from the
    viewer; in batch mode the farthest surface point sits at `surface_floor`
    and only background is 0.0. `meta` records the transform used for every
    frame, so an output can be traced back to the exact mapping it came from.
    """
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}, got {mode!r}")
    frames, resolution = int(frames), int(resolution)
    width, height = int(width), int(height)
    params = frame_parameters(frames, m1_start, m1_end, m2_start, m2_end, yaw_start, yaw_end)

    if mode == "legacy":
        if width != height:
            raise ValueError("legacy mode renders square frames only (it used img_size)")
        depths, masks, per_frame = [], [], []
        for p in params:
            d, m, meta = _legacy_frame(resolution, width, p["m1"], p["m2"],
                                       n1_1, n1_2, n1_3, p["yaw"], pitch)
            depths.append(d)
            masks.append(m)
            per_frame.append(meta)
        return (np.stack(depths).astype(np.float32), np.stack(masks),
                {"mode": mode, "grid": [resolution, resolution], "frames": per_frame})

    u_res, v_res = auto_grid(width, height, resolution) if density == "auto" else (resolution, resolution)
    clouds = [surface_points(u_res, v_res, p["m1"], p["m2"], n1_1, n1_2, n1_3, p["yaw"], pitch)
              for p in params]

    # One isotropic transform and one depth mapping for the whole batch.
    lo = np.min([c.min(axis=1) for c in clouds], axis=0)
    hi = np.max([c.max(axis=1) for c in clouds], axis=0)
    span = np.where(hi - lo > 0, hi - lo, 1.0)
    usable_w = (width - 1) * (1.0 - 2.0 * margin)
    usable_h = (height - 1) * (1.0 - 2.0 * margin)
    scale = min(usable_w / span[0], usable_h / span[1])
    off_x = (width - 1 - scale * span[0]) / 2.0
    off_y = (height - 1 - scale * span[1]) / 2.0

    depths, masks, per_frame = [], [], []
    for cloud in clouds:
        xs = np.clip(np.rint((cloud[0] - lo[0]) * scale + off_x), 0, width - 1).astype(np.int64)
        ys = np.clip(np.rint((cloud[1] - lo[1]) * scale + off_y), 0, height - 1).astype(np.int64)
        zs = surface_floor + (1.0 - surface_floor) * (cloud[2] - lo[2]) / span[2]
        flat = ys * width + xs
        depth = np.zeros(width * height)
        np.maximum.at(depth, flat, zs)
        occupied = np.zeros(width * height, dtype=bool)
        occupied[flat] = True
        depth, occupied = depth.reshape(height, width), occupied.reshape(height, width)
        filled_px = int(occupied.sum())
        if fill_holes:
            depth, mask = fill_interior(depth, occupied, int(hole_radius))
        else:
            mask = occupied
        depths.append(depth)
        masks.append(mask)
        per_frame.append({"sampled_px": filled_px, "silhouette_px": int(mask.sum())})

    meta = {
        "mode": mode,
        "grid": [u_res, v_res],
        "px_per_unit": [float(scale), float(scale)],
        "z_range": [float(lo[2]), float(hi[2])],
        "surface_floor": float(surface_floor),
        "frames": per_frame,
    }
    return np.stack(depths).astype(np.float32), np.stack(masks), meta


# --------------------------------------------------------------------------
# ComfyUI node
# --------------------------------------------------------------------------

class Gielis3DBatchRenderer:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "frames": ("INT", {"default": 16, "min": 1, "max": 300, "step": 1}),
                "resolution": ("INT", {"default": 128, "min": 32, "max": 512, "step": 16}),
                "img_size": ("INT", {"default": 1024, "min": 512, "max": 2048, "step": 64}),
                "m1_start": ("FLOAT", {"default": 5.0, "min": 0.0, "max": 20.0, "step": 0.1}),
                "m1_end": ("FLOAT", {"default": 5.0, "min": 0.0, "max": 20.0, "step": 0.1}),
                "m2_start": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 20.0, "step": 0.1}),
                "m2_end": ("FLOAT", {"default": 5.0, "min": 0.0, "max": 20.0, "step": 0.1}),
                "n1_1": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 10.0, "step": 0.1}),
                "n1_2": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 10.0, "step": 0.1}),
                "n1_3": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 10.0, "step": 0.1}),
                "yaw_start": ("FLOAT", {"default": 0.0, "min": -360.0, "max": 360.0, "step": 1.0}),
                "yaw_end": ("FLOAT", {"default": 360.0, "min": -360.0, "max": 360.0, "step": 1.0}),
                "pitch": ("FLOAT", {"default": 30.0, "min": -90.0, "max": 90.0, "step": 1.0}),
            },
            # Optional inputs keep every existing graph valid. width/height of 0
            # mean "square img_size", which is what the original node rendered.
            "optional": {
                "mode": (list(MODES), {"default": "batch"}),
                "width": ("INT", {"default": 0, "min": 0, "max": 2048, "step": 16}),
                "height": ("INT", {"default": 0, "min": 0, "max": 2048, "step": 16}),
                "fill_holes": ("BOOLEAN", {"default": True}),
                "surface_floor": ("FLOAT", {"default": 0.08, "min": 0.0, "max": 0.5, "step": 0.01}),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "render_batch"
    CATEGORY = "GielisGeometry"

    def render_batch(self, frames, resolution, img_size, m1_start, m1_end, m2_start,
                     m2_end, n1_1, n1_2, n1_3, yaw_start, yaw_end, pitch,
                     mode="batch", width=0, height=0, fill_holes=True, surface_floor=0.08):
        import torch  # ComfyUI provides it; the numpy core above does not need it

        depth, mask, _ = render_frames(
            frames=frames, resolution=resolution,
            width=width or img_size, height=height or img_size,
            m1_start=m1_start, m1_end=m1_end, m2_start=m2_start, m2_end=m2_end,
            n1_1=n1_1, n1_2=n1_2, n1_3=n1_3,
            yaw_start=yaw_start, yaw_end=yaw_end, pitch=pitch,
            mode=mode, fill_holes=fill_holes, surface_floor=surface_floor,
        )
        images = torch.from_numpy(np.repeat(depth[..., None], 3, axis=3))
        return images, torch.from_numpy(mask.astype(np.float32))


NODE_CLASS_MAPPINGS = {"Gielis3DBatchRenderer": Gielis3DBatchRenderer}
NODE_DISPLAY_NAME_MAPPINGS = {"Gielis3DBatchRenderer": "3D Gielis Superformula Batch Renderer"}
