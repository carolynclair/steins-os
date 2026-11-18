# Update audits and release work

Audit date: 2026-10-31. The installed VM came from ISO SHA-256 `5d19a142470a3eadc254f445a9c7fcad572eac47c08e69be069f2b621e60a98a`. Tests used a new copy-on-write disk, `evidence/vm/update-audit.qcow2`, backed by the prior disposable installation. The ISO was not attached and the original installed disk was preserved.

## Observed update behaviour

- Installed disk boot, personal user login, root on `/dev/vda2` and absence of the live `lab` account passed before updating. No failed systemd units were reported.
- APT refreshed its indexes successfully. Its plan offered 15 upgrades, zero installations and zero removals. Fourteen were security updates; `tzdata` came from trixie-updates.
- `unattended-upgrade --dry-run --debug` recognised Debian security origins and the available security packages. This verifies selection, not execution by the daily timer.
- The actual `apt-get full-upgrade` completed with exit status 0, keeping existing configuration files. Firefox ESR changed from `153.5.0esr-1~deb13u1` to `153.6.0esr-1~deb13u1`; WebKit changed from `2.54.0-1~deb13u2` to `2.54.0-1~deb13u3`.
- Worldline library and Hinamizawa pack hashes stayed unchanged; saved divergence stayed `2.198306`. Applying the saved theme succeeded. `dpkg --audit` and failed-unit checks reported no problems before reboot.

After the updates and identity correction, disk-only reboot and personal graphical login passed. Hinamizawa and divergence `2.198306` returned automatically (`evidence/vm/update-after-login.png`, `update-after-desktop.png`).

## Reproduced identity bug and correction

`base-files` owns `/etc/os-release` as a normal package file. Reinstalling version `13.8+deb13u7` replaced our custom identity with `Debian GNU/Linux 13 (trixie)` even when using `--force-confold`, because it is not a conffile.

The initial audit hook registered a local diversion to `/etc/os-release.debian` with **`--no-rename`** before writing Steins identity. This avoids temporarily moving a file from an Essential package. Repeating the base-files reinstall then succeeded while `/etc/os-release` retained SHA-256 `81ee7e3a13c052ef97e5ec8435359d4e12f13d1595663de74ef3b01a56d4fe47`; the diverted file contained Debian's identity. Repeating the diversion registration was idempotent.

The actual-image test now checks the diversion database, so a future ISO without this protection cannot pass artifact validation. This initial correction was tested in the audit VM. The current package implementation replaces the local diversion with package ownership; see below.

Evidence: `evidence/update-baseline.txt`, `update-plan-summary.txt`, `update-unattended-dry.txt`, `update-apply-summary.txt`, `update-before-reboot.txt`, and the full `evidence/vm/update-audit-serial.log`. The latter includes exploratory commands and failed attempts as well as successful runs. `evidence/update-identity-fix.sh` records the final identity snippet.

## Versioned package follow-up — 2026-10-31

Implemented four native packages: `steins-artwork`, `steins-branding`, `steins-desktop` and `steins-live-installer`. Runtime scripts now have package ownership under `/usr/bin` and `/usr/lib/steins`; the editable source layout remains unchanged. The branding package owns the identity diversion, derives the theme from installed Greybird and responds to package triggers. Debian conffiles remain under Debian ownership; the installer works from a separate generated configuration tree.

Actual installed-VM tests covered first install, upgrades, purge, ordinary remove/reinstall and a controlled `base-files` reinstall. The latter preserved Steins identity. Removal restored Debian identity; reinstallation restored Steins identity. Saved divergence 2.198306 and a custom GTK CSS comment survived, and disk-only reboot/login plus About launch passed. Tested installed design: 0.1.0-6; 0.1.0-7 adds the live-build temporary-diversion handover, exercised in a disposable container. See PACKAGING.md and `evidence/package-*`.

## Release work remaining

- Rebuild and validate the exact packaged ISO, including fresh installation, installer cleanup, disk-only boot and normal Debian updates. Current status and artifact checksum belong in VALIDATION.md.
- Establish a signed APT repository, publisher ownership and release cadence before advertising automatic Steins updates. The local `Packages` index is an inspection/install artifact; no public repository or signing infrastructure exists.
- Test USB boot, graphics, Wi-Fi, audio, Bluetooth and suspend on physical hardware. Major Debian-release upgrades require a separate tested Steins release.

The Debian installer generates sources containing main/non-free-firmware and optional trixie-backports, whereas the live build also enables contrib/non-free. Review and align that policy with the packages actually shipped. No tested upgrades came from backports in the original audit.

One successful update cycle does not prove all future updates, kernel upgrades, rollbacks or hardware combinations. The original 15-update audit used the earlier ISO with an identity fix applied; exact packaged-ISO results are tracked separately.

## Packaged VM follow-up — 2026-11-01 NZDT

The 0.1.0-7 packaged ISO (SHA-256 28f9692a6bc7fee2cd826b8ac847950c3f8f3ef8a2076ea8f86c044b23b7fccd) completed a fresh disconnected UEFI installation. Its installed disk booted without media, personal login and password-required sudo passed, and the live account/integration package were absent. The generic Calamares framework entry remained; 0.1.0-8 adds that framework to the target cleanup list. Module sequence and disk modules are preserved.

On this installed test disk, APT refresh/full-upgrade completed with zero upgrades and zero removals. The three persistent Steins packages then upgraded to 0.1.0-8 successfully. A base-files reinstall returned 0 and retained identity SHA-256 81ee7e3a13c052ef97e5ec8435359d4e12f13d1595663de74ef3b01a56d4fe47. Hinamizawa 2.198306 and a custom GTK comment survived. Disk-only reboot/login returned Hinamizawa automatically; no failed units or dpkg audit problems were reported. About, focus/Escape, optional meter and its ibm5100 launcher worked with package paths. Evidence: packaged-update-validation.txt, packaged-upgrade-reboot-validation.txt, packaged-gtk-runtime.txt and evidence/vm/packaged-v7-upgrade-serial.log.

Fresh 0.1.0-8 ISO installation/cleanup results are recorded separately in VALIDATION.md.

## Exact 0.1.0-8 image result — 2026-11-01 NZDT

ISO SHA-256 9216cfec7ddc39ad6b5559b74a60c8207317869c1733a2be6dac184d5ec33a31 completed an offline UEFI installation and disk-only boot/login. The generic installer cleanup fix passed: Calamares and both launcher entries are absent, while the three daily packages remain at 0.1.0-8. On this fresh installation APT refresh/full-upgrade returned 0 with zero upgrades/removals; controlled base-files reinstall returned 0 and preserved the identity hash above. Hinamizawa 2.198306 and custom GTK CSS survived, and a second disk-only reboot/login restored the saved theme. See packaged-v8-update-validation.txt, packaged-v8-reboot-validation.txt and VALIDATION.md. No claim about every future update or physical hardware follows from this VM cycle.
