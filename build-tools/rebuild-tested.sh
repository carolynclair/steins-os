#!/bin/bash
# Re-run overlay integration and rebuild using the retained package cache.
set -euo pipefail
ulimit -n 4096
cd /src/build
lb clean
# Replace the input snapshot so removed packs cannot survive in the next image.
python3 /src/build-tools/build_packages.py
python3 /src/build-tools/prepare_live.py
lb config
lb build 2>&1 | tee /src/evidence/iso-rebuild.log
cp steins-os-0.1-amd64-amd64.hybrid.iso /src/dist/.steins-os-0.1-amd64.iso.new
mv -f /src/dist/.steins-os-0.1-amd64.iso.new /src/dist/steins-os-0.1-amd64.iso
cp steins-os-0.1-amd64-amd64.packages /src/dist/steins-os-0.1-amd64.packages
cd /src/dist
sha256sum steins-os-0.1-amd64.iso > SHA256SUMS
chown -R "$(stat -c %u:%g /src)" /src/dist
