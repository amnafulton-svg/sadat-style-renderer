#!/usr/bin/env bash
# Install FFmpeg without hanging on a slow Ubuntu mirror (Alaska 2026-10-23: the azure mirror stalled the
# combine job for 9+ min; it normally takes 20 s). Each apt try is capped at 4 min. When apt fails (credit cards
# 2026-10-25: 2 chunks failed all 3 apt tries), a static build comes from GitHub (fast from a runner), then
# johnvansickle.com, then apt once more from the main mirror.
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

apt_try && done_ok
echo "::warning::FFmpeg apt install failed; trying a static build"
static_try https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz && done_ok
static_try https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz && done_ok
echo "::warning::static FFmpeg failed too; apt from archive.ubuntu.com"
sudo sed -i "s#http://azure.archive.ubuntu.com#http://archive.ubuntu.com#g" \
  /etc/apt/sources.list /etc/apt/sources.list.d/*.sources /etc/apt/sources.list.d/*.list 2>/dev/null || true
apt_try && done_ok
echo "::error::FFmpeg install failed every way"; exit 1
