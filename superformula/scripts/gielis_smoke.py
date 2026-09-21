#!/usr/bin/env python3
"""Gielis node smoke: 4 depth frames, fetch, tile locally."""
import json, socket, subprocess, sys, time
from pathlib import Path
SCRIPTS = Path.home() / '.hermes/scripts'
sys.path.insert(0, str(SCRIPTS))
import fandom_loops as loops
import gpu_gate

OUT = Path.home() / '.hermes/workspaces/fandom-news/flux-tests/gielis'
GRAPH = {
    "1": {"class_type": "Gielis3DBatchRenderer", "inputs": {"frames": 4, "resolution": 256, "img_size": 512,
          "m1_start": 5.0, "m1_end": 5.0, "m2_start": 0.0, "m2_end": 0.0, "n1_1": 1.0, "n1_2": 1.0,
          "n1_3": 1.0, "yaw_start": 0.0, "yaw_end": 360.0, "pitch": 30.0}},
    "2": {"class_type": "SaveImage", "inputs": {"images": ["1", 0], "filename_prefix": "gielis/smoke"}},
}
def main():
    host, port = gpu_gate.endpoint()
    OUT.mkdir(parents=True, exist_ok=True)
    tunnel = None
    try:
        try:
            socket.create_connection(('127.0.0.1', 18188), timeout=2).close()
        except OSError:
            tunnel = subprocess.Popen(['ssh', '-N', '-o', 'BatchMode=yes', '-o', 'ExitOnForwardFailure=yes',
                                       '-o', 'ServerAliveInterval=20', '-L', '18188:127.0.0.1:8188',
                                       '-p', str(port), host], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        for i in range(20):
            try:
                loops.get('/queue', timeout=5)
                break
            except Exception:
                if i == 19:
                    raise
                time.sleep(1)
        pid = loops.post('/prompt', {'prompt': GRAPH})['prompt_id']
        t0 = time.monotonic()
        entry = None
        while time.monotonic() - t0 < 300:
            h = loops.get('/history/' + pid)
            if pid in h:
                entry = h[pid]
                break
            time.sleep(2)
        if entry is None:
            raise SystemExit('timeout')
        st = entry.get('status', {})
        if st.get('status_str') != 'success':
            raise SystemExit(json.dumps(st)[:400])
        items = [i for x in entry.get('outputs', {}).values() for i in x.get('images', [])]
        print('items', len(items), flush=True)
        for k, item in enumerate(items[:4]):
            dst = OUT / ('frame_%02d.png' % k)
            loops.fetch(item, dst)
            print('got', dst.name, dst.stat().st_size, flush=True)
    finally:
        if tunnel:
            tunnel.terminate()
            tunnel.wait(timeout=10)
    print('GIELIS-SMOKE DONE', flush=True)


if __name__ == '__main__':
    main()
