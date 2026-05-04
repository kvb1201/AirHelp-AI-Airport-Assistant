#!/usr/bin/env bash
# Download default English Piper ONNX voice from Hugging Face.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/backend/app/data/piper_voices"
BASE="https://huggingface.co/rhasspy/piper-voices/resolve/main"

mkdir -p "$DEST"

download_pair() {
  local rel="$1"
  local onnx="$DEST/$(basename "$rel")"
  local json="${onnx}.json"
  if [[ -f "$onnx" && -f "$json" ]]; then
    echo "OK (already present): $onnx"
    return
  fi
  echo "Downloading $(basename "$rel")..."
  curl -fsSL "$BASE/$rel" -o "$onnx"
  curl -fsSL "$BASE/$rel.json" -o "$json"
}

download_pair "en/en_US/lessac/medium/en_US-lessac-medium.onnx"

echo "Done. English voice in: $DEST"
ls -la "$DEST"
