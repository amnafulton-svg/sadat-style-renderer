#!/usr/bin/env bash
# Downloads one video zip from the release and unpacks only its src/, public/ and video.json
# (the repo's own package.json, lock file and config always win).
set -euo pipefail
tag="$1"; zip="$2"
rm -rf incoming src public video.json
mkdir -p incoming
# 20 chunk jobs hit the release in the same second; GitHub now and then answers 500 or "release not found"
# (run 39473941832, 2026-10-20), so retry with a growing, jittered wait before giving up.
for try in 1 2 3 4 5 6; do
  gh release download "$tag" --repo "$GITHUB_REPOSITORY" --pattern "$zip*" --dir incoming --clobber && break
  [ "$try" = 6 ] && exit 1
  sleep $(( try * 10 + RANDOM % 10 ))
done
unzip -q -o "incoming/$zip" 'src/*' 'public/*' video.json
# a video over 2 GB comes in more parts (ship.py): each is a zip of more public/ files
for part in incoming/"$zip".part*; do
  if [ -e "$part" ]; then unzip -q -o "$part" 'public/*'; fi
done
rm -rf incoming
test -f src/index.ts
cat video.json
