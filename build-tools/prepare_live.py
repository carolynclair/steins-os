#!/usr/bin/env python3
"""Snapshot live-build inputs; install Steins payload only through local .debs."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
build = ROOT / 'build'
build.mkdir(exist_ok=True)
for name in ('auto', 'config'):
    destination = build / name
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(ROOT / name, destination, ignore=shutil.ignore_patterns('__pycache__'))
# Source layout is editable; the runtime must only contain package-owned files.
shutil.rmtree(build / 'config/includes.chroot')
(build / 'config/includes.chroot').mkdir()
packages = build / 'config/packages.chroot'
packages.mkdir(parents=True, exist_ok=True)
manifest = json.loads((ROOT / 'dist/packages/manifest.json').read_text())
for package in manifest['packages']:
    source = ROOT / 'dist/packages' / package['file']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == package['sha256']
    shutil.copyfile(source, packages / source.name)
assets = build / 'config/steins-assets'
assets.mkdir(exist_ok=True)
shutil.copyfile(ROOT / 'config/includes.chroot/usr/share/backgrounds/steins/boot.svg', assets / 'boot.svg')
print('Prepared live-build input with four package-owned Steins components')
