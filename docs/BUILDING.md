# Build from source

The default image inputs build the **Debian 13 amd64 XFCE track**. The [V4 Plasma installer build](../prototype/iso-v4/README.md) uses a separate set of packages and live-build inputs.

Use a disposable Linux amd64 build host or builder VM with Docker and at least 30 GiB free. Keep important workstation files outside the build environment. The live-build stage needs a privileged container for mounts and chroots; a privileged Docker container has elevated host capabilities.

## Check the source

From the repository root:

```sh
python3 tests/check_source.py
python3 tests/check_worldlines.py
```

`check_source.py` also runs the UI contract checks. These checks do not install packages or prove an ISO boots. Optional graphical checks may need dependencies in the disposable builder.

## Build the XFCE ISO

```sh
docker build -t steins-os-builder:trixie build-tools
docker run --rm --privileged --ulimit nofile=4096:4096 \
  --mount "type=bind,src=$PWD,dst=/src" \
  steins-os-builder:trixie /src/build-tools/build.sh
```

Run from a clean checkout/build directory. The script writes project `build/`, `dist/` and `evidence/` paths and replaces the named ISO output after a successful export. Preserve a previous artifact elsewhere if it matters. Do not mount a physical installation disk into the builder.

Expected outputs:

| Output | Purpose |
| --- | --- |
| `dist/steins-os-0.1-amd64.iso` | Hybrid live/installable image |
| `dist/SHA256SUMS` | Image checksum |
| `dist/*.packages` | Recorded installed package list |
| `dist/packages/` | First-party Debian packages and local package index |
| `evidence/iso-build.log` | Build log |

The builder first generates four native packages from `config/` and `packaging/`, then prepares the live-build inputs. `build-tools/generate_artwork.py` regenerates original vector artwork; desktop defaults, hooks and installer integration are maintained directly in source.

The Debian repositories and builder tag are moving inputs. A successful build is repeatable in process, not a claim of byte-for-byte reproducibility. Pin a Debian snapshot and builder digest for a release, preserve the exact source/package manifests, and compare a second clean build.

## Package-only work

After building the Docker image:

```sh
docker run --rm --user "$(id -u):$(id -g)" \
  --mount "type=bind,src=$PWD,dst=/src" \
  steins-os-builder:trixie python3 /src/build-tools/build_packages.py
python3 tests/check_packages.py
```

Migration tests execute real package-maintenance behavior and belong only in the disposable container documented in [PACKAGING.md](PACKAGING.md). Do not run them against a workstation's package state.

## V4 component builds

V4 source is split into independently documented components:

| Component | Guide |
| --- | --- |
| Original icons and design tokens | [identity-v4](../prototype/identity-v4/README.md) |
| Worldline service and appearance adapter | [worldline-v4](../prototype/worldline-v4/README.md) |
| Native Plasma panel and theme | [panel-v4](../prototype/panel-v4/README.md) |
| Navigator and terminal surfaces | [surfaces-v4](../prototype/surfaces-v4/README.md) |
| Guarded local VM integration | [integration-v4](../prototype/integration-v4/README.md) |

The component build scripts produce packages under `dist/v4/`. The identity and terminal builders use the disposable Debian Docker image; package-only scripts need Debian packaging tools. Refer to each README for renderer/test dependencies and licensing details.

V4 packages are intended for the isolated test guest. Package installation alone does not select a panel/theme; explicit preset tools create backups and apply changes only in their guarded guest environment. Do not copy those VM-specific settings onto a daily desktop.

## Boot and installation verification

Verify the exported checksum, then follow [RELEASE.md](RELEASE.md). The image checker needs the builder's inspection tools; see [TEST-MATRIX.md](TEST-MATRIX.md) for coverage.

First boot and install onto a new disposable virtual disk. Boot the installed disk again with the ISO detached, and verify user-account cleanup, sudo authentication, networking, updates and shutdown. The XFCE live-image credentials are `lab` / `live`; installation creates a personal account.

The source repository deliberately omits ISO files, virtual disks, firmware state and local backing chains. The V4 lab commands work only after those local prerequisites have been provisioned. A clone alone is not a bootable V4 VM.
