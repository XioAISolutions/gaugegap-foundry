#!/usr/bin/env python3
"""Gielis living-artwork batch: 4 shapes -> FLUX stills -> Wan drift drafts."""
import json, socket, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path.home() / '.hermes/scripts'))
import fandom_loops as loops
import gpu_gate
E = Path.home() / '.hermes/workspaces/fandom-news/flux-tests/gielis'
NEG = "blurry, distorted, deformed, static, low quality, watermark, text, logo"
SHAPES = [
 ("shape_b", 75.0, 28.0, 7.0, 1.6, 9902),
 ("shape_c", 150.0, 40.0, 3.0, 0.6, 9903),
 ("shape_d", 210.0, 20.0, 8.0, 2.2, 9904),
 ("shape_e", 300.0, 35.0, 6.0, 1.0, 9905),
]
# <<PART2>>


def flux_graph(name, yaw, pitch, m1, n1, seed):
    def n(kind, **inputs): return {"class_type": kind, "inputs": inputs}
    prompt = ("A monumental translucent crystal sculpture with soft curved lobes, standing on a dark "
              "gallery pedestal, iridescent teal and amber reflections, cinematic studio lighting, "
              "glossy surface, hyper-detailed, product photography.")
    return {
        "1": n("Gielis3DBatchRenderer", frames=1, resolution=256, img_size=1024,
               m1_start=m1, m1_end=m1, m2_start=0.0, m2_end=0.0, n1_1=n1, n1_2=1.0, n1_3=1.0,
               yaw_start=yaw, yaw_end=yaw, pitch=pitch),
        "2": n("ImageScale", image=["1", 0], upscale_method="bilinear", width=768, height=1344, crop="disabled"),
        "3": n("CheckpointLoaderSimple", ckpt_name="flux1-dev-fp8.safetensors"),
        "4": n("CLIPTextEncode", text=prompt, clip=["3", 1]),
        "5": n("FluxGuidance", conditioning=["4", 0], guidance=3.5),
        "6": n("CLIPTextEncode", text="", clip=["3", 1]),
        "7": n("ControlNetLoader", control_net_name="flux-depth-controlnet-v3.safetensors"),
        "8": n("ControlNetApplyAdvanced", positive=["5", 0], negative=["6", 0], control_net=["7", 0],
               image=["2", 0], strength=0.75, start_percent=0.0, end_percent=1.0),
        "9": n("EmptyLatentImage", width=768, height=1344, batch_size=1),
        "10": n("KSampler", model=["3", 0], positive=["8", 0], negative=["8", 1], latent_image=["9", 0],
                seed=seed, steps=20, cfg=1.0, sampler_name="euler", scheduler="simple", denoise=1.0),
        "11": n("VAEDecode", samples=["10", 0], vae=["3", 2]),
        "12": n("SaveImage", images=["11", 0], filename_prefix="gielisb/%s" % name),
    }


def wan_graph(seed, image_name, name):
    def n(kind, **inputs): return {"class_type": kind, "inputs": inputs}
    prompt = ("The translucent crystal sculpture slowly rotates, its soft lobes gently undulating, "
              "cinematic gallery light sweeping across its iridescent teal and amber surface, gentle sparkle.")
    return {
        "1": n("UNETLoader", unet_name="wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors", weight_dtype="default"),
        "2": n("UNETLoader", unet_name="wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors", weight_dtype="default"),
        "3": n("LoraLoaderModelOnly", model=["1", 0], lora_name="wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors", strength_model=1.0),
        "4": n("LoraLoaderModelOnly", model=["2", 0], lora_name="wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors", strength_model=1.0),
        "5": n("ModelSamplingSD3", model=["3", 0], shift=8.0),
        "6": n("ModelSamplingSD3", model=["4", 0], shift=8.0),
        "7": n("CLIPLoader", clip_name="umt5_xxl_fp8_e4m3fn_scaled.safetensors", type="wan"),
        "8": n("VAELoader", vae_name="wan_2.1_vae.safetensors"),
        "9": n("CLIPVisionLoader", clip_name="clip_vision_h.safetensors"),
        "10": n("LoadImage", image=image_name),
        "11": n("CLIPVisionEncode", clip_vision=["9", 0], image=["10", 0], crop="none"),
        "12": n("CLIPTextEncode", text=prompt, clip=["7", 0]),
        "13": n("CLIPTextEncode", text=NEG, clip=["7", 0]),
        "14": n("WanImageToVideo", positive=["12", 0], negative=["13", 0], vae=["8", 0], width=704, height=1280,
               length=81, batch_size=1, clip_vision_output=["11", 0], start_image=["10", 0]),
        "15": n("KSamplerAdvanced", model=["5", 0], add_noise="enable", noise_seed=seed, steps=4, cfg=1.0,
               sampler_name="euler", scheduler="simple", start_at_step=0, end_at_step=2,
               return_with_leftover_noise="enable", positive=["14", 0], negative=["14", 1], latent_image=["14", 2]),
        "16": n("KSamplerAdvanced", model=["6", 0], add_noise="disable", noise_seed=0, steps=4, cfg=1.0,
               sampler_name="euler", scheduler="simple", start_at_step=2, end_at_step=10000,
               return_with_leftover_noise="disable", positive=["14", 0], negative=["14", 1], latent_image=["15", 0]),
        "17": n("VAEDecode", samples=["16", 0], vae=["8", 0]),
        "18": n("CreateVideo", images=["17", 0], fps=16.0),
        "19": n("SaveVideo", video=["18", 0], filename_prefix="gielisb/%s" % name, format="mp4", codec="h264"),
    }


def main():
    host, port = gpu_gate.endpoint()
    E.mkdir(parents=True, exist_ok=True)
    tunnels = []
    tunnel = None
    try:
        try: socket.create_connection(('127.0.0.1', 18188), timeout=2).close()
        except OSError:
            tunnel = subprocess.Popen(['ssh','-N','-o','BatchMode=yes','-o','ExitOnForwardFailure=yes',
                '-o','ServerAliveInterval=20','-L','18188:127.0.0.1:8188','-p',str(port),host],
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            time.sleep(3)
        for name, yaw, pitch, m1, n1, seed in SHAPES:
            still = E / (name + '.png')
            if not still.exists():
                pid = loops.post('/prompt', {'prompt': flux_graph(name, yaw, pitch, m1, n1, seed)})['prompt_id']
                t0 = time.monotonic(); entry = None
                while time.monotonic() - t0 < 900:
                    h = tick(host, port, tunnels, pid)
                    if pid in h: entry = h[pid]; break
                    time.sleep(4)
                if entry is None or entry.get('status', {}).get('status_str') != 'success':
                    print('STILL-FAIL', name, flush=True); continue
                items = [i for x in entry.get('outputs', {}).values() for i in x.get('images', [])]
                loops.fetch(items[0], still)
                print('STILL', name, still.stat().st_size, flush=True)
            else:
                print('still exists', name, flush=True)
        for name, yaw, pitch, m1, n1, seed in SHAPES:
            still = E / (name + '.png')
            dst = E / (name + '_drift.mp4')
            if not still.exists() or dst.exists():
                print('skip drift', name, flush=True); continue
            remote = name + '.png'
            with open(still, 'rb') as f:
                subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-p',str(port),host,
                                'cat > /workspace/slava/comfy-house/ComfyUI/input/%s' % remote], stdin=f, check=True)
            for _ in range(60):
                q = loops.get('/queue')
                if not q.get('queue_running') and not q.get('queue_pending'): break
                time.sleep(10)
            pid = loops.post('/prompt', {'prompt': wan_graph(seed, remote, name + '_drift')})['prompt_id']
            t0 = time.monotonic(); entry = None
            while time.monotonic() - t0 < 1800:
                h = tick(host, port, tunnels, pid)
                if pid in h: entry = h[pid]; break
                time.sleep(8)
            if entry is None or entry.get('status', {}).get('status_str') != 'success':
                print('DRIFT-FAIL', name, flush=True); continue
            items = [i for x in entry.get('outputs', {}).values() for i in x.get('images', []) + x.get('videos', [])]
            loops.fetch(items[0], dst)
            subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(dst),'-f','null','-'], check=True)
            print('DRIFT', name, dst.stat().st_size, flush=True)
    finally:
        if tunnel:
            tunnel.terminate()
            try:
                tunnel.wait(timeout=10)
            except Exception:
                pass
        for t in tunnels:
            t.terminate()
        for t in tunnels:
            try:
                t.wait(timeout=10)
            except Exception:
                pass
    print('GIELIS-BATCH DONE', flush=True)


if __name__ == '__main__':  # guard moved to EOF (tunnel helpers appended below)
    pass


def ensure_tunnel(host, port, tunnels):
    try:
        socket.create_connection(('127.0.0.1', 18188), timeout=2).close()
        return
    except OSError:
        pass
    tunnels.append(subprocess.Popen(['ssh', '-N', '-o', 'BatchMode=yes', '-o', 'ExitOnForwardFailure=yes',
                                     '-o', 'ServerAliveInterval=20', '-L', '18188:127.0.0.1:8188',
                                     '-p', str(port), host], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE))
    time.sleep(3)


def tick(host, port, tunnels, pid):
    try:
        return loops.get('/history/' + pid)
    except Exception:
        ensure_tunnel(host, port, tunnels)
        time.sleep(2)
        return loops.get('/history/' + pid)


if __name__ == '__main__':
    main()
