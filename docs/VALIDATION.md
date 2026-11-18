# Validation ledger

Latest packaged-artifact checkpoint: 2026-11-01 NZDT. Earlier checkpoints remain below. Development preview; no physical-hardware or production-readiness claim.

## Current 0.1.0-8 ISO

`dist/steins-os-0.1-amd64.iso`, 2,145,386,496 bytes; SHA-256 `9216cfec7ddc39ad6b5559b74a60c8207317869c1733a2be6dac184d5ec33a31`. Full rebuild succeeded (`evidence/packaged-iso-build.log`); source/package hashes are in `packaged-source-and-package-hashes.json`.

Actual-ISO checks pass: hybrid BIOS/UEFI boot structure, checksum, offline bootloader pool and every indexed archive hash, all four configured packages at 0.1.0-8, identity diversion, exact runtime/worldline assets, installer style/config and explicit target Calamares cleanup (`evidence/packaged-image-checks.txt`). The original module sequence is preserved; only cleanup package parameters change (`package-installer-cleanup-test.txt`). BIOS and UEFI live desktops pass. A fresh UEFI installation with automatic unencrypted partitioning completed with network carrier zero throughout. Its disk booted with no ISO attached; personal graphical login, root on /dev/vda2, live-account removal and password-required sudo passed. All three persistent packages remain at 0.1.0-8; the live installer, Calamares binary and both installer desktop entries are absent. No failed units or dpkg audit problems were reported.

On that exact-image installation, APT refresh/full-upgrade returned 0 (zero upgrades/removals), and base-files reinstall returned 0 while preserving identity SHA-256 81ee7e3a13c052ef97e5ec8435359d4e12f13d1595663de74ef3b01a56d4fe47. Saved Hinamizawa 2.198306 and custom GTK CSS survived. A second disk-only boot/personal login restored Hinamizawa automatically; packaged About rendered correctly.

Evidence: packaged-v8-offline-baseline.txt, packaged-v8-offline-calamares.log, packaged-installed-validation.txt, packaged-v8-update-validation.txt, packaged-v8-reboot-validation.txt, the raw packaged-uefi[-disk]-serial.log files, and packaged-v8-* screenshots. The serial getty was enabled only on the installed test disk for automation; it is not an ISO default.

The installed upgrade audit separately passes package upgrade, base-files identity preservation and disk-only reboot/login with Hinamizawa 2.198306 and custom GTK CSS. See PACKAGING.md and UPDATES.md. There is no public signed Steins update repository.

Known polish/investigation items: blue login accents, startup wording appearing on shutdown, missing greeting in graphical terminals, and a BIOS QMP power-button shutdown that left display output inactive without exiting the VM (terminated through QMP; no successful BIOS shutdown claim). Normal installed-disk shutdown succeeded in the upgrade audit. No root cause is inferred for the ACPI case. These are included in Claude’s next brief.

## Earlier 0.1.0-7 checkpoint (2026-11-01 NZDT)

At this checkpoint the ISO was `dist/steins-os-0.1-amd64.iso`, 2,145,386,496 bytes, SHA-256 `28f9692a6bc7fee2cd826b8ac847950c3f8f3ef8a2076ea8f86c044b23b7fccd`. It embeds the reviewed UI and four versioned Steins packages at 0.1.0-7.

Full build succeeded (`evidence/packaged-v7-build.log`). A disconnected UEFI installation then reproduced missing GRUB frontend packages at the bootloader step. Separate BIOS/UEFI binary package lists now populate the stock Debian media repository, without changing Calamares' module sequence. Media reassembly succeeded and asserts the live rootfs SHA-256 stayed `23a4e22be02ec0c00e5c77f448a483b365d7bf9d379bda507ff365f15d94609f` (`packaged-media-rebuild.log`, `packaged-rootfs-preserved.txt`). The failed pre-fix image hash starts `5345c074`; its failure is retained as evidence and is not a passing install.

Actual-ISO inspection passes checksum, hybrid BIOS/UEFI structure, required bootloader pool packages and all indexed archive hashes, identity diversion, package ownership, launchers, exact merged runtime code and all six worldline assets (`evidence/packaged-v7-image-checks.txt`). Fresh UEFI live boot with network disconnected passes. Offline UEFI installation, disk-only boot/login and account cleanup passed. The generic Calamares framework entry remained after removing the live integration; 0.1.0-8 adds framework cleanup. That installed disk subsequently passed upgrade to the three 0.1.0-8 persistent packages, base-files reinstall, state preservation and reboot/login.

Package install/upgrade/remove/reinstall, base-files identity protection, legacy override migration and user-state preservation are recorded in PACKAGING.md. Source checks, 49 worldline tests and 18 UI tests pass; one optional host Xvfb test is skipped. There is no public signed Steins update feed.

The following sections retain historical results. Their “not rebuilt” and “pending” statements describe those earlier checkpoints, rather than the current packaged ISO.

## Earlier UI-review checkpoint (2026-10-31)

Claude's second UI ZIP is imported. Real Calamares 3.3.14 and GTK checks are recorded in `docs/CLAUDE-UI-REVIEW.md`. Verified all installer pages, hidden welcome links and automatic slideshow playback through an actual VM installation. Fixed partition legends, checkbox/radio indicators, keyboard-preview dependency, progress-label contrast, slideshow framing and missing dark-variant GTK overrides. Final QML/progress corrections were verified in a separate native Calamares renderer preview with sleep-only jobs.

Source checks and 49 worldline tests pass; UI tests report 18 passed and one optional host Xvfb test skipped. Direct GTK focus/Escape smoke tests passed in the VM. These source changes have not been rebuilt into the ISO. The UI-review source hashes at that checkpoint and screenshot provenance are in `evidence/ui-review/provenance.json` and the review report.

## Earlier update-audit checkpoint (2026-10-31)

A copy-on-write clone of the new installed disk booted without the ISO and accepted the personal user's login. APT installed 15 available Debian updates successfully. A separate base-files reinstall reproduced an identity reset; the source hook now registers an os-release diversion, and repeating the reinstall preserved the exact Steins identity checksum. Disk-only reboot/login then passed and Hinamizawa at 2.198306 returned automatically. Source checks pass; artifact tests now require the diversion database entry. See `docs/UPDATES.md` for evidence, scope and the packaging/repository work still required. This audit did not rebuild the ISO.

## Earlier graphics and robustness merge

Imported `steins-os-claude-changes.zip` with the six place-named worlds and optional GTK3 meter. The unmodified imported changes passed 48 tests. Integration adds non-finite pack-range rejection and strict full-string validation; the resulting 49 worldline tests and source checks pass (`evidence/claude-merge-tests.txt`). Regenerating artwork reproduces every SVG/JSON byte-for-byte. Build input hashes match `evidence/claude-merge-source.json`.

Installed XFCE runtime checks passed after transferring the merged overlay into the earlier UEFI installation:

- All six worlds render through librsvg and switch the wallpaper, terminal colours, top-panel RGBA and Conky number/colours. `cicada` selects Hinamizawa at 2.198306.
- Meter renders its eight glyphs, follows divergence/palette changes, Enter opens `ibm5100`, and Escape closes it. The earlier GTK import-version warning is fixed in source.
- At 1280x800 the greeter title is fully visible above the login controls.
- Evidence: `evidence/vm/claude-worldline-switches.txt`, `claude-meter-default.png`, `claude-meter-hinamizawa.png`, `claude-greeter.png`, and `claude-{alpha,hitogashima,lugunica,mitakihara}.png`.

The new ISO build completed successfully (`evidence/iso-rebuild.log`). Actual-image inspection passed: checksum, hybrid boot report, identity, launchers, all six pack assets and exact merged worldline code; the three removed packs are absent (`evidence/claude-image-checks.txt`). Artifact at that checkpoint: `dist/steins-os-0.1-amd64.iso`, SHA-256 `5d19a142470a3eadc254f445a9c7fcad572eac47c08e69be069f2b621e60a98a` (rechecked on 2026-10-31).

The exact ISO reached its branded BIOS menu and Plymouth splash (`evidence/vm/claude-bios-boot.png`, `claude-iso-plymouth.png`). On 2026-10-31 its fresh UEFI live desktop passed (`evidence/vm/claude-iso-desktop.png`). After applying the new source UI overlay and hook, Calamares completed installation of that ISO filesystem to a disposable disk (`ui-calamares-finish.png`). This is a frontend integration test; the UI source is not embedded in that ISO. Disk-only boot and user login were subsequently verified in the update-audit clone. A rebuild with the UI and identity corrections remains pending.

## Previous image evidence

- First image: BIOS live boot and graphical installation passed. Boot from its installed disk with the ISO removed passed; personal user login, live `lab` user removal, password-required sudo, networking and no failed system units were observed.
- Corrected base: branded UEFI menu and live desktop passed. One UEFI installation run was invalidated because the export overwrote its mounted ISO; export now uses atomic rename. That interrupted run is excluded from installation results.
- Previous worldline image (retained as `dist/steins-os-0.1-amd64-pre-claude.iso`): checksum, BIOS/UEFI hybrid structure and assets passed. UEFI Calamares installation completed successfully. Its disk-only boot and personal login were verified on 2026-10-19 before applying the new overlay: root `/dev/vda2`, EFI firmware present, no live medium, no `lab` account, sudo requires a password, and no failed units (`evidence/vm/worldline-uefi-calamares-complete.txt`, `claude-uefi-baseline.txt`, `pre-merge-uefi-disk.png`).

## Remaining scope

Physical USB/hardware compatibility, Secure Boot, real audio/Wi-Fi/Bluetooth hardware, multi-monitor layouts, suspend, accessibility, encryption/manual partitioning and managed Steins-specific upgrades remain untested. This build uses current Debian repositories, not a pinned package snapshot; byte-for-byte ISO reproducibility is not claimed.
