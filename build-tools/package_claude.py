#!/usr/bin/env python3
"""Package current source and selected visual evidence, excluding build/VM data."""
import argparse
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, default=ROOT / "dist/steins-os-claude-graphics-handoff.zip")
OUTPUT = parser.parse_args().output.resolve()
sources = {}
for directory in ("auto", "config", "build-tools", "packaging", "tests", "docs"):
    for path in (ROOT / directory).rglob("*"):
        if path.is_file() and "__pycache__" not in path.parts:
            sources[str(path.relative_to(ROOT))] = path
for name in ("README.md", "LICENSE", ".gitignore", "CLAUDE-CHANGES.md", "REMOVED-PATHS.txt"):
    sources[name] = ROOT / name
for name in ("worldline-tests.txt", "source-checks.txt", "worldline-image-checks.txt", "worldline-source.json", "claude-merge-tests.txt", "claude-merge-source.json", "claude-image-checks.txt", "claude-followup-tests-2026-10-31.txt"):
    path = ROOT / "evidence" / name
    if path.is_file():
        sources["evidence/" + name] = path
for name in ("plymouth.png", "installer-start.png", "installer-complete.png", "installed-greeter.png", "cicada.png", "uefi-base-desktop.png", "worldline-uefi-menu.png", "worldline-uefi-desktop.png", "claude-meter-default.png", "claude-meter-hinamizawa.png", "claude-greeter.png", "claude-alpha.png", "claude-hitogashima.png", "claude-lugunica.png", "claude-mitakihara.png", "claude-iso-desktop.png", "claude-iso-installed.png", "claude-bios-boot.png", "claude-iso-plymouth.png"):
    path = ROOT / "evidence/vm" / name
    if path.is_file():
        sources["evidence/visual/" + name] = path

# Current packaging evidence stays small; never include ISO/VM disk data.
for name in ("packaged-image-checks.txt", "packaged-tested-iso.txt", "packaged-source-and-package-hashes.json", "package-checks.txt", "package-migration-cases.txt", "package-worldline-tests.txt", "package-ui-tests.txt", "packaged-installed-validation.txt", "packaged-update-validation.txt", "packaged-gtk-runtime.txt", "packaged-qa-provenance.json", "package-installer-cleanup-test.txt", "packaged-v8-offline-baseline.txt", "packaged-v8-update-validation.txt", "packaged-v8-reboot-validation.txt"):
    path = ROOT / "evidence" / name
    if path.is_file():
        sources["evidence/" + name] = path
for pattern in ("packaged-v8-*.png", "packaged-upgrade-*.png", "packaged-before-offline-fix-failure.png"):
    for path in sorted((ROOT / "evidence/vm").glob(pattern)):
        sources["evidence/visual/" + path.name] = path

manifest = {
    "base_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    "description": "Working source including uncommitted fixes; graphics and bug-hunting handoff.",
    "sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in sorted(sources.items())},
}
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
temporary = OUTPUT.with_suffix(".zip.new")
with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for name, path in sorted(sources.items()):
        archive.write(path, "steins-os/" + name)
    archive.writestr("steins-os/START-HERE.md", (ROOT / "docs/CLAUDE-BRIEF.md").read_text())
    archive.writestr("steins-os/SOURCE-MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
temporary.replace(OUTPUT)
with zipfile.ZipFile(OUTPUT) as archive:
    assert archive.testzip() is None
print(f"Created {OUTPUT} ({OUTPUT.stat().st_size / 1024:.0f} KiB, {len(sources)} source/evidence files)")
