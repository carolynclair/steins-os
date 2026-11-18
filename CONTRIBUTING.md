# Contributing to Steins;OS

Steins;OS combines a Debian live/install system with an evolving native Plasma desktop. Read the [project status](docs/PROJECT-STATUS.md) before choosing a task: the existing XFCE ISO and V4 Plasma milestone have different validation histories.

Useful contributions include reproducible bug reports, build and installer testing, accessible interface improvements, and original icons or artwork. Discuss large changes first so their maintenance and integration costs are clear.

## Local source checks

From the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 tests/check_source.py
PYTHONDONTWRITEBYTECODE=1 python3 tests/check_worldlines.py
PYTHONDONTWRITEBYTECODE=1 python3 prototype/surfaces-v4/tests/test_tokens.py
PYTHONDONTWRITEBYTECODE=1 python3 prototype/panel-v4/test_theme.py
PYTHONDONTWRITEBYTECODE=1 python3 prototype/integration-v4/test_serial.py
```

These check source contracts and temporary fixtures. They do not establish that an ISO boots or installs, that a real desktop renders correctly, or that hardware is supported. Optional GTK construction checks skip when their dependencies are unavailable. See component READMEs for Qt, D-Bus, rendering and storage tests, and [building](docs/BUILDING.md) for the distribution toolchain.

Run desktop integration and installer experiments in a disposable VM. Use image-backed storage, retain a known-good checkpoint, and keep physical host disks outside the guest. Do not run live appearance helpers against your everyday desktop to obtain a screenshot.

## Design and implementation

Use mature Debian/KDE applications and services. Keep icons recognisable, share the V4 design tokens, respect reduced-motion settings and preserve user choices during upgrades. New branding should use original or appropriately licensed material; official anime imagery, logos, music and voice clips are not project assets.

Keep pull requests focused. Explain the resulting behaviour, include relevant checks, and state what remains untested. Visual evidence should identify the build, worldline, resolution and scaling, and distinguish real guest screenshots from concepts or isolated renders.

Do not commit ISO images, VM disks, NVRAM, build caches, personal profiles, credentials or private logs. Preserve existing license notices and add attribution for new third-party material. The root license does not override component licenses.
