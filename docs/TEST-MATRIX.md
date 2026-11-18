# Test matrix

QEMU/KVM, virtio graphics and Ethernet/NAT, 4 GiB RAM, disposable 32 GiB qcow2 disks. No host block device is attached.

## Current packaged image — 2026-11-01 NZDT

ISO SHA-256 `9216cfec7ddc39ad6b5559b74a60c8207317869c1733a2be6dac184d5ec33a31`; packages 0.1.0-8. Current evidence and earlier failure provenance are in VALIDATION.md.

| Check | Current result |
|---|---|
| Source / worldline / UI contracts | Source passed; 49 worldline tests; 18 UI passed, 1 optional Xvfb skip |
| Native package ownership / migration | Passed; edited overrides, backup conflicts, repeated migration and live-build diversion covered |
| ISO checksum / hybrid boot / exact code and assets | Passed |
| Offline BIOS/UEFI bootloader pool | Required packages and all archive hashes pass |
| BIOS live / UEFI live | Passed on this exact ISO |
| Offline automatic, unencrypted UEFI installation | Completed; carrier remained zero |
| Disk-only boot / personal login / lab removal / sudo password | Passed |
| Installer cleanup | Framework, live launcher and both desktop entries absent; three daily packages remain |
| APT refresh/full-upgrade / base-files reinstall | Exit 0; zero available upgrades/removals; identity retained |
| Hinamizawa / custom CSS / second reboot | Saved state and CSS retained; automatic restore passed |
| Packaged About / meter / terminal / GTK focus | Fresh About passed; upgrade audit passed meter/terminal and focus/Escape |
| Current BIOS installation, physical USB/hardware, Secure Boot, encryption, suspend, multi-monitor | Not verified; earlier BIOS installs are historical evidence |
| BIOS live ACPI power-button shutdown | Inconclusive; display went inactive and VM was terminated through QMP |
| Public signed Steins update feed | Not deployed |

## Earlier image checkpoints

The 2026-10-31 source UI review is in `docs/CLAUDE-UI-REVIEW.md`: all Calamares pages, slideshow, links and GTK focus/selection checked in a real VM. UI corrections are not yet rebuilt into the ISO.

| Check | Previous images | Merged source in installed XFCE | New graphics ISO |
|---|---|---|---|
| Source checks / worldline regression tests | 15 passed | 49 passed | Exact merged worldline code/assets match |
| ISO checksum and hybrid BIOS/UEFI structure | Passed | N/A | Passed; checksum rechecked 2026-10-31 |
| BIOS live boot / Plymouth | Passed | N/A | Menu and splash passed; desktop pending |
| UEFI live boot | Passed | N/A | Passed 2026-10-31, before applying UI overlay |
| Graphical Calamares installation | Passed BIOS and UEFI | New UI frontend passed | Completed UEFI with reviewed live UI overlay |
| Installed disk boot, personal login, lab removal, sudo password | Passed BIOS and UEFI | Passed UEFI baseline | Passed UEFI in audit clone, 2026-10-31 |
| Six worldline wallpapers, terminal/panel colours and Conky | Five old packs | Passed all six | Pending |
| Meter render / follow state / Enter / Escape | N/A | Passed | Pending |
| Login title visible at 1280x800 | Old title overlapped | Passed | Pending |
| Hardware, Secure Boot, encryption, suspend, multi-monitor | Untested | Untested | Untested |

The new graphics image's checks must refer to its own checksum. Results from transferring an overlay into an installed VM are identified separately. See VALIDATION.md for evidence paths and the excluded interrupted test.

Update audit: 15 Debian updates installed, identity reset reproduced/fixed, and disk-only reboot/login with saved Hinamizawa state passed. See UPDATES.md; the UI/identity source corrections still need an ISO rebuild.
