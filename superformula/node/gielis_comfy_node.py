# Gielis 3D Superformula batch renderer for ComfyUI — hardened build.
# Concept: procedural 3D supershapes -> depth-map frame batches for
# ControlNet/image conditioned generation. Hardening over the community
# draft: vectorized z-buffer rasterization (no python pixel loops),
# NaN/inf guards inside the superformula, deterministic interpolation.
import numpy as np
import torch

GAMMA = 1e-9

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
            }
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "render_batch"
    CATEGORY = "GielisGeometry"
    @staticmethod
    def _radius(phi, m, n1, n2, n3):
        t1 = np.abs(np.cos(m * phi / 4.0))
        t2 = np.abs(np.sin(m * phi / 4.0))
        return (t1 ** n2 + t2 ** n3 + GAMMA) ** (-1.0 / n1)

    def render_batch(self, frames, resolution, img_size, m1_start, m1_end, m2_start,
                     m2_end, n1_1, n1_2, n1_3, yaw_start, yaw_end, pitch):
        frames, resolution, img_size = int(frames), int(resolution), int(img_size)
        u = np.linspace(-np.pi, np.pi, resolution)
        v = np.linspace(-np.pi / 2.0, np.pi / 2.0, resolution)
        U, V = np.meshgrid(u, v)
        pr = np.radians(pitch)
        R_pitch = np.array([[np.cos(pr), 0.0, np.sin(pr)],
                            [0.0, 1.0, 0.0],
                            [-np.sin(pr), 0.0, np.cos(pr)]])
        imgs, msks = [], []
        denom = max(1, frames - 1)
        for f in range(frames):
            t = f / denom
            m1 = m1_start + (m1_end - m1_start) * t
            m2 = m2_start + (m2_end - m2_start) * t
            yaw = np.radians(yaw_start + (yaw_end - yaw_start) * t)
            r1 = self._radius(U, m1, n1_1, n1_2, n1_3)
            r2 = self._radius(V, m2, n1_1, n1_2, n1_3)
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
            img = np.repeat(depth.reshape(img_size, img_size, 1), 3, axis=2)
            imgs.append(torch.from_numpy(img.astype(np.float32)))
            msks.append(torch.from_numpy((count.reshape(img_size, img_size) > 0).astype(np.float32)))
        return (torch.stack(imgs, 0), torch.stack(msks, 0))


NODE_CLASS_MAPPINGS = {"Gielis3DBatchRenderer": Gielis3DBatchRenderer}
NODE_DISPLAY_NAME_MAPPINGS = {"Gielis3DBatchRenderer": "3D Gielis Superformula Batch Renderer"}
