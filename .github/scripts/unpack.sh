#!/usr/bin/env bash
# Downloads one video zip from the release and unpacks only its src/, public/ and video.json
# (the repo's own package.json, lock file and config always win).
set -euo pipefail
tag="$1"; zip="$2"
rm -rf incoming src public video.json
mkdir -p incoming
gh release download "$tag" --repo "$GITHUB_REPOSITORY" --pattern "$zip" --dir incoming
unzip -q -o "incoming/$zip" 'src/*' 'public/*' video.json
rm -rf incoming
test -f src/index.ts
cat video.json
