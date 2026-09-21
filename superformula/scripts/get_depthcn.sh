#!/bin/bash
# Fetch XLabs FLUX depth ControlNet v3 to the box (resumable, logged).
mkdir -p /workspace/slava/comfy-house/ComfyUI/models/controlnet
cd /workspace/slava/comfy-house/ComfyUI/models/controlnet || exit 1
URL="https://huggingface.co/XLabs-AI/flux-controlnet-depth-v3/resolve/main/flux-depth-controlnet-v3.safetensors"
OUT="flux-depth-controlnet-v3.safetensors"
nohup curl -L -C - --retry 5 -o "$OUT" "$URL" >> /workspace/slava/depthcn-download.log 2>&1 &
echo "started: $(date) -> $OUT"
sleep 4
ls -l "$OUT" 2>/dev/null || echo "not visible yet (starting)"