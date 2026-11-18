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

The [V4 ledger](../evidence/v4-design/VALIDATION.md) distinguishes actual guest screenshots from isolated renderer proofs. The existing ISO and previous checkpoints were preserved. **V4 is not present in a rebuilt release ISO.** The VM launch helper depends on local backing disks; those images are excluded from this source repository.

## Remaining release gates

1. Integrate the selected Plasma package set into a complete live image and rebuild it from a recorded source revision.
2. Repeat BIOS/UEFI live boot, offline installation, disk-only reboot/login, networking, desktop, lock/unlock and shutdown tests on that exact image.
3. Qualify package upgrades, rollback and identity/state preservation on the installed Plasma system.
4. Test encrypted/manual installation, localization, accessibility and additional display sizes/scaling.
5. Establish a hardware matrix for USB boot, real graphics, Wi-Fi, Bluetooth, audio and suspend/resume. Secure Boot requires independent verification.
6. Define a maintained signed Steins package feed and release ownership; retain matching source and licensing records.
7. Pin build inputs and compare clean builds before claiming bit-for-bit reproducibility.

Debian updates use Debian repositories. There is no public signed Steins update repository or promised support cadence. The project should be treated as a development preview until those release gates are met.
