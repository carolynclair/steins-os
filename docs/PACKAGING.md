# Steins Debian packages

The editable runtime sources remain in `config/includes.chroot` for continuity with Claude's patches. `build-tools/build_packages.py` transforms them into four native Debian packages. The live-build snapshot does **not** copy the overlay directly: `prepare_live.py` supplies the packages through `config/packages.chroot` instead.

| Package | Owns |
|---|---|
| `steins-artwork` | Original wallpapers, SVG sources, icon and Plymouth assets |
| `steins-branding` | Distribution identity, greeter drop-in, security/update defaults and theme configuration helper |
| `steins-desktop` | XFCE defaults, guide, worldline/meter/About tools and their private Python libraries |
| `steins-live-installer` | Live launcher, installer UI assets and generated Calamares configuration |

Runtime executables are under `/usr/bin`, libraries under `/usr/lib/steins`. No package payload installs into `/usr/local`. The source's `usr/local` layout is an input convention, not the delivered filesystem layout.

## Build and inspect

Use the documented builder image, which supplies librsvg, the licensed fonts and Debian packaging tools:

```sh
docker build -t steins-os-builder:trixie build-tools
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/src" steins-os-builder:trixie python3 /src/build-tools/build_packages.py
python3 tests/check_packages.py
docker run --rm -e STEINS_DISPOSABLE_CONTAINER=1 -v "$PWD:/src:ro" steins-os-builder:trixie python3 /src/tests/check_migration.py
```

Output is `dist/packages/`: four `.deb` files, a SHA-256/source manifest and a local `Packages` index. Superseded experiments are archived outside that index. `packaging/VERSION` sets the package version; `SOURCE_DATE_EPOCH` can override the recorded source epoch. Package hashes are retained with the ISO evidence. The index is not a signed or publicly hosted update feed.

## Identity and configuration

`steins-branding` registers a package-owned, no-rename diversion of `/etc/os-release` to `/etc/os-release.debian`. Its own identity is ordinary versioned metadata, **not a conffile**: this ensures a first installation replaces Debian's identity. Debian's machine-readable ID and trixie codename remain intact. Removing the package restores the prior identity and releases the diversion. During ISO construction it explicitly hands over live-build’s temporary `.debootstrap` reservation; arbitrary third-party diversions are rejected.

Debian-owned conffiles are not diverted. LightDM uses a separate `90-steins.conf` drop-in. Calamares configuration is generated under `/var/lib/steins/installer/config`, copying the installed Debian settings and changing branding plus final confirmation. It includes the required QML link and adds the Calamares framework to the target package cleanup list, preventing a dead generic installer menu entry. Disk modules and their sequence are preserved. A generated copy of Debian's wrapper retains its fstab handling, graphical authorization and cleanup, adding only Calamares' supported `--config` option. A changed upstream wrapper invocation fails configuration for review rather than silently dropping authentication steps.

Greybird remains a Debian dependency. The branding package regenerates `Steins-Lab` when upstream theme files or Steins overrides change, applying overrides to **both** GTK stylesheet variants. Edit `/etc/steins/theme-overrides.css` for system customisations; the generated theme directory is replaceable output. Plymouth changes rebuild the initramfs when the Steins splash is active. A user-selected alternative splash is preserved on subsequent upgrades.

## Preview migration and user state

The pre-package preview used unmanaged `/usr/local` files. Maintainer scripts recognise the recorded hashes of those releases and back them up under `/var/lib/steins/legacy` before removing the shadowing paths. Edited overrides, symlinked paths or differing backups keep the entire legacy script/library group intact and emit a warning; packaged commands remain available explicitly under `/usr/bin`.

Migration removes only the old hook's exact greeting line from `bash.bashrc`, retaining a backup and all other contents. Fresh profiles use the terminal's login-shell setting and `/etc/profile.d` instead of modifying Debian's Bash configuration. Existing open shells may need logout/login or `hash -r` after this one-time path migration.

Packages never own users' divergence state, cached wallpapers or personal GTK CSS. Normal conffile handling preserves locally edited system settings. Native install/upgrade/removal tests retain a saved Hinamizawa number and a custom GTK comment. The installer package is separate so removal of Debian's installer settings also removes Steins' live installer; the everyday desktop does not depend on it. No dead installer shortcut is added to every user's Desktop.

## Update-channel status

Local package install, upgrade and removal are testable now. There is no public Steins repository, signing infrastructure or promised release cadence. A signed feed, publisher ownership and hardware/release testing remain necessary before advertising a maintained production distribution. Debian package updates continue to use Debian repositories.

## Recorded package tests — 2026-10-31

Four packages at 0.1.0-8 pass archive ownership, executable/conffile, relocated CLI and six-world checks (`evidence/package-checks.txt`). Disposable-container tests execute the actual migration script against edited overrides, recognised files, repeated runs, conflicting backups and live-build’s identity reservation (`evidence/package-migration-cases.txt`).

The installed UEFI audit clone exercised first installation, version upgrades, remove/reinstall and `base-files` reinstall. The final 0.1.0-6 design restores Debian identity on removal and Steins identity on reinstallation, retaining divergence 2.198306 and a custom GTK comment. Disk-only reboot/login and packaged About launch passed; no failed system units were reported (`evidence/package-reboot-validation.txt`, `evidence/vm/packaged-about.png`). Version 0.1.0-7 adds the build-time diversion handover, verified in the container. Earlier prototype failures remain in raw logs and are not passing evidence. Exact-ISO results are recorded separately in VALIDATION.md.

## Offline bootloader media

Calamares uses Debian’s unchanged `calamares-sources-media` helper to expose the ISO’s `dists/` and `pool/` repository in the target chroot. Separate `grub-pc.list.binary` and `grub-efi.list.binary` inputs ask live-build to download each conflicting frontend and its dependencies into that pool. This supplies the bootloader helper’s firmware-specific APT installation without a network. Merely shipping the `-bin` packages in the live root is insufficient: a disconnected UEFI test reproduced that failure before this correction.

A normal full build includes the binary lists. `rebuild-media.sh` is restricted to media-only corrections after a successful build: it preserves rootfs stage markers, reruns only the pool/checksum/ISO stages, and asserts that the squashfs hash is unchanged. Runtime changes require the full rebuild script. ISO inspection verifies the required pool packages and every indexed archive’s SHA-256.

The 2026-11-01 follow-up installed the 0.1.0-7 ISO offline in UEFI mode, then upgraded its three persistent packages to 0.1.0-8. APT refresh/full-upgrade returned zero upgrades and zero removals; the local Steins upgrade and base-files reinstall returned 0, preserving identity, Hinamizawa state and custom GTK CSS. Disk-only reboot/login returned Hinamizawa automatically. Packaged About, keyboard focus/Escape, meter render and meter-to-ibm5100 launch passed. The test VM alone enabled a serial getty for automation; this is not an ISO setting. Fresh 0.1.0-8 ISO results are recorded separately in VALIDATION.md.
