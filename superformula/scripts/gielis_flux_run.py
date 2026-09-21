#!/usr/bin/env python3
"""FLUX smoke test: render Gleam as a still via the all-in-one flux1-dev-fp8."""
import json, socket, subprocess, sys, time
from pathlib import Path
SCRIPTS = Path.home() / '.hermes/scripts'
sys.path.insert(0, str(SCRIPTS))
import fandom_loops as loops
import gpu_gate

OUT = Path.home() / '.hermes/workspaces/fandom-news/flux-tests'
PROMPT = ("Full-body character image: a small oval tan potato with dark freckles, round black eyes, a friendly smile, short brown arms and feet, wearing a plain red cloth cape tied at the chest, holding a simple wooden spoon upright in his right hand, standing on a plain light-wood table, muted teal wall behind, warm light from the left, matte finish, centered composition.")
SEED = 7712

def graph():
    def n(kind, **inputs): return {"class_type": kind, "inputs": inputs}
    return {
        "1": n("CheckpointLoaderSimple", ckpt_name="flux1-dev-fp8.safetensors"),
        "2": n("CLIPTextEncode", text=PROMPT, clip=["1", 1]),
        "3": n("FluxGuidance", conditioning=["2", 0], guidance=3.5),
        "4": n("CLIPTextEncode", text="", clip=["1", 1]),
        "5": n("EmptyLatentImage", width=768, height=1344, batch_size=1),
        "6": n("KSampler", model=["1", 0], positive=["3", 0], negative=["4", 0], latent_image=["5", 0],
               seed=SEED, steps=20, cfg=1.0, sampler_name="euler", scheduler="simple", denoise=1.0),
        "7": n("VAEDecode", samples=["6", 0], vae=["1", 2]),
        "8": n("SaveImage", images=["7", 0], filename_prefix="gielis-flux/run"),
    }

def telemetry(host, port):
    p = subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','-p',str(port),host,
        'nvidia-smi --query-gpu=temperature.gpu,utilization.gpu,power.draw --format=csv,noheader,nounits'],
        capture_output=True, text=True, timeout=25, check=True)
    t,u,w = map(float, p.stdout.strip().split(','))
    print('GPU', json.dumps({'t':t,'util':u,'w':w}), flush=True)
    if t >= 84: raise SystemExit('STOP: 84C')

def main():
    host, port = gpu_gate.endpoint()
    OUT.mkdir(parents=True, exist_ok=True)
    dst = OUT / 'gielis_flux_test.png'
    if dst.exists(): raise SystemExit('exists: ' + str(dst))
    tunnel = None
    try:
        try:
            socket.create_connection(('127.0.0.1', 18188), timeout=2).close()
        except OSError:
            tunnel = subprocess.Popen(['ssh','-N','-o','BatchMode=yes','-o','ExitOnForwardFailure=yes',
                '-o','ServerAliveInterval=20','-L','18188:127.0.0.1:8188','-p',str(port),host],
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        for i in range(20):
            try:
                q = loops.get('/queue', timeout=5); break
            except Exception:
                if i == 19: raise
                time.sleep(1)
        if q.get('queue_running') or q.get('queue_pending'): raise SystemExit('busy')
        telemetry(host, port)
        pid = loops.post('/prompt', {'prompt': json.loads((Path.home() / '.hermes/tmp/gielis_flux_graph.json').read_text())})['prompt_id']
        t0 = time.monotonic()
        while time.monotonic() - t0 < 900:
            h = loops.get('/history/' + pid)
            if pid in h: entry = h[pid]; break
            time.sleep(4)
        else:
            raise SystemExit('timeout')
        st = entry.get('status', {})
        if st.get('status_str') != 'success': raise SystemExit(json.dumps(st)[:300])
        items = [i for x in entry.get('outputs', {}).values() for i in x.get('images', [])]
        loops.fetch(items[0], dst)
        data = dst.read_bytes()
        assert data[:8] == b'\x89PNG\r\n\x1a\n', 'not a png'
        (OUT / 'gielis_flux_test.json').write_text(json.dumps(
            {'file': str(dst), 'prompt_id': pid, 'seed': SEED, 'bytes': len(data)}, indent=1) + '\n')
        telemetry(host, port)
        print('DONE', dst, len(data), flush=True)
    finally:
        if tunnel:
            tunnel.terminate(); tunnel.wait(timeout=10)

if __name__ == '__main__':
    main()
