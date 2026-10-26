#!/usr/bin/env bash
# FFmpeg without apt: the Ubuntu mirror stalled chunk after chunk (Alaska 2026-10-23 9+ min, credit cards 2026-10-25
# 2 chunks failed, zniti2 2026-10-26 chunk 005 stuck in apt). First Remotion's own FFmpeg, which every chunk already
# has in node_modules after npm ci (it has libx264, aac, pcm, mpegts/mp4/matroska, concat and h264_mp4toannexb);
# the combine job (no npm ci) fetches just that package from npm. Then a static build from GitHub, then
# johnvansickle.com, and apt only as the last resort, each apt try capped at 4 min.
set -uo pipefail
command -v ffmpeg >/dev/null && command -v ffprobe >/dev/null && exit 0
opts=(-o Acquire::http::Timeout=30 -o Acquire::Retries=3)

apt_try() {
  timeout -k 20 240 sudo apt-get "${opts[@]}" update && \
    timeout -k 20 240 sudo apt-get "${opts[@]}" install -y --no-install-recommends ffmpeg
}

static_try() {  # $1 = url of a .tar.xz holding ffmpeg and ffprobe
  local dir; dir="$(mktemp -d)"
  if timeout -k 10 180 curl -fsSL --retry 3 --retry-delay 5 "$1" | tar -xJ -C "$dir"; then
    local bin; bin="$(dirname "$(find "$dir" -type f -name ffmpeg -perm -u+x | head -1)")"
    if [ -x "$bin/ffmpeg" ] && [ -x "$bin/ffprobe" ]; then
      sudo install -m 755 "$bin/ffmpeg" "$bin/ffprobe" /usr/local/bin/ && return 0
    fi
  fi
  return 1
}

done_ok() { ffmpeg -hide_banner -version | head -1; exit 0; }

remotion_try() {  # $1 = a node_modules dir: wrap its @remotion/compositor-linux-x64-gnu ffmpeg + ffprobe
  local dir="$1/@remotion/compositor-linux-x64-gnu" b
  [ -x "$dir/ffmpeg" ] && [ -x "$dir/ffprobe" ] || return 1
  for b in ffmpeg ffprobe; do
    printf '#!/bin/sh
LD_LIBRARY_PATH="%s${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" exec "%s/%s" "$@"
' "$dir" "$dir" "$b"       | sudo tee "/usr/local/bin/$b" >/dev/null && sudo chmod 755 "/usr/local/bin/$b" || return 1
  done
  ffmpeg -hide_banner -bsfs 2>/dev/null | grep -q h264_mp4toannexb
}

remotion_try "$PWD/node_modules" && done_ok
ver="$(node -p "require('./package.json').dependencies.remotion" 2>/dev/null || true)"
if [ -n "$ver" ] && timeout -k 10 180 npm install --silent --no-save --no-audit --no-fund --prefix /tmp/remotion-ffmpeg      "@remotion/compositor-linux-x64-gnu@$ver" >/dev/null 2>&1; then
  remotion_try /tmp/remotion-ffmpeg/node_modules && done_ok
fi
echo "::warning::Remotion's FFmpeg not usable; trying a static build"
static_try https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz && done_ok
static_try https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && done_ok
echo "::warning::static FFmpeg failed too; apt"
apt_try && done_ok
echo "::warning::apt failed; apt from archive.ubuntu.com"
sudo sed -i "s#http://azure.archive.ubuntu.com#http://archive.ubuntu.com#g" \
  /etc/apt/sources.list /etc/apt/sources.list.d/*.sources /etc/apt/sources.list.d/*.list 2>/dev/null || true
apt_try && done_ok
echo "::error::FFmpeg install failed every way"; exit 1
