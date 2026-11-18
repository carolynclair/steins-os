#!/bin/bash
set -euo pipefail
ulimit -n 4096
cd /src
mkdir -p build dist evidence
# Build state lives only in the dedicated project folder.
python3 build-tools/build_packages.py
python3 build-tools/prepare_live.py
cd build
lb config
lb build 2>&1 | tee /src/evidence/iso-build.log
image=$(find . -maxdepth 1 -name '*.iso' -print -quit)
[ -n "$image" ]
cp "$image" /src/dist/.steins-os-0.1-amd64.iso.new
mv -f /src/dist/.steins-os-0.1-amd64.iso.new /src/dist/steins-os-0.1-amd64.iso
cp ./*.packages /src/dist/ 2>/dev/null || true
cd /src/dist
sha256sum steins-os-0.1-amd64.iso > SHA256SUMS
chown -R "$(stat -c %u:%g /src)" /src/dist
