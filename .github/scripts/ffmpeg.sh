#!/usr/bin/env bash
# Install FFmpeg without hanging on a slow Ubuntu mirror (Alaska 2026-10-23: the azure mirror stalled the
# combine job for 9+ min; it normally takes 20 s). Each try is capped at 4 min; tries 2-3 use the main mirror.
set -uo pipefail
command -v ffmpeg >/dev/null && command -v ffprobe >/dev/null && exit 0
opts=(-o Acquire::http::Timeout=30 -o Acquire::Retries=3)
for try in 1 2 3; do
  if [ "$try" -gt 1 ]; then
    echo "::warning::FFmpeg install try $((try-1)) timed out; switching to archive.ubuntu.com"
    sudo sed -i "s#http://azure.archive.ubuntu.com#http://archive.ubuntu.com#g" \
      /etc/apt/sources.list /etc/apt/sources.list.d/*.sources /etc/apt/sources.list.d/*.list 2>/dev/null || true
  fi
  if timeout -k 20 240 sudo apt-get "${opts[@]}" update && \
     timeout -k 20 240 sudo apt-get "${opts[@]}" install -y --no-install-recommends ffmpeg; then
    ffmpeg -hide_banner -version | head -1; exit 0
  fi
done
echo "::error::FFmpeg install failed 3 times"; exit 1
