# Project status

Steins;OS has two distinct engineering tracks. Their assets and results should not be confused when reviewing screenshots, building packages or testing an installation.

## Installable XFCE track

The existing Debian 13 amd64 image uses XFCE, LightDM, Plymouth, Calamares and a hybrid BIOS/UEFI boot layout. Four native Debian packages own the first-party artwork, branding, desktop tools and live-installer integration.

The recorded 0.1.0-8 artifact is `dist/steins-os-0.1-amd64.iso`, SHA-256:

```text
9216cfec7ddc39ad6b5559b74a60c8207317869c1733a2be6dac184d5ec33a31
```

Recorded tests cover BIOS and UEFI live desktops; offline UEFI automatic unencrypted installation; disk-only boot and personal graphical login; removal of the live account and installer; password-required sudo; persistence of worldline state; and identity preservation across `base-files` reinstallation. These results apply to that exact artifact, which is not stored in Git. A new build from moving Debian repositories may differ.

See [the validation ledger](VALIDATION.md), [packaging](PACKAGING.md) and [update notes](UPDATES.md) for evidence and limits.

## V4 Plasma track

V4 is a separately packaged, native Plasma/Wayland desktop running in an installed-system KVM guest. It adds:

- A 46px bottom panel with a clickable divergence instrument, native tasks, launcher, tray and clock.
- A 35-icon original family, inherited upstream fallbacks and shared design tokens.
- Six atmosphere accents on consistent neutral surfaces.
- Matching terminal chrome, worldline cards, selection colors and supported Breeze window decorations.

The frozen milestone passed real mouse/keyboard interactions, six-world state and wallpaper checks, terminal shell input, native screen lock/unlock, a fresh checkpoint boot and package/service qualification. Asset and private-bus tests additionally cover small icon rendering, contrast, SVG slice seams, migration behavior and failure states.

The [V4 installer build](../prototype/iso-v4/README.md) integrates these packages into its own hybrid live ISO. The existing XFCE ISO and V4 installed-guest checkpoints are separate artifacts. The VM launch helper for the earlier checkpoint depends on local backing disks.

## Remaining release gates

1. Extend installer coverage to BIOS installation, encrypted/manual partitioning, localization, accessibility, and additional display sizes and scaling.
2. Qualify networking, lock/unlock, shutdown, package upgrades, rollback and identity/state preservation on the installed Plasma system.
3. Test physical USB boot, graphics, Wi-Fi, Bluetooth, audio, suspend/resume and Secure Boot.
4. Define a maintained signed Steins package feed and release ownership, and retain matching source and licensing records.
5. Pin build inputs and compare clean builds before claiming bit-for-bit reproducibility.

Debian updates use Debian repositories. There is no public signed Steins update repository or promised support cadence. The project should be treated as a development preview until those release gates are met.
