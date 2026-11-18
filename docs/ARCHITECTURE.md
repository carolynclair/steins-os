# Architecture decision: Debian 13 / XFCE / live-build

Target: x86-64 PCs, BIOS and UEFI, hybrid USB/DVD image. Version 0.1 is a development preview.

Debian stable supplies signed repositories, long-lived package updates, firmware, live-boot and a tested Calamares integration. Ubuntu is viable but brings additional derivative/repository policy; Arch makes rolling updates and installer maintenance a larger commitment. XFCE is economical and exposes predictable desktop defaults without maintaining a desktop fork.

We retain the Linux kernel, APT, systemd, NetworkManager, PipeWire, LightDM, XFCE, GRUB/syslinux, Plymouth and Debian's Calamares module sequence. Debian's ID is retained for compatibility; human-readable system identity is Steins;OS. No private package repository or invented support endpoint is used.

Build: Debian trixie Docker toolchain and live-build. Editable overlay sources are transformed into four native Debian packages; live-build consumes those packages rather than copying unmanaged runtime files. A small branding hook finalises integration. Separate BIOS/UEFI media package lists supply Debian’s offline installer bootloader dependencies. See PACKAGING.md. The container needs mount privileges for debootstrap/chroot/live-build. Only this project is bind-mounted; no host block device is used as an installation destination. VM tests use newly created disk images. Host packages and boot configuration are never altered.

Original artwork uses procedural vector geometry and text. No anime screenshots, official logos or audio are included. Theme metrics derive from Debian's Greybird-dark package; Papirus icons, DMZ cursor and Debian-packaged fonts retain upstream licenses.

The build is repeatable from source, not yet bit-for-bit reproducible: the trixie package repositories and builder tag move over time. Published image checksums and package manifests identify each output. Release engineering must pin a Debian snapshot and builder digest, retain source packages, and verify a second clean build before claiming reproducibility.

Daily-use scope: browser, file manager, terminal, document editor, spreadsheet, PDF/image viewers, archive manager, printing, Bluetooth, sound, Wi-Fi, graphical package manager and automatic Debian security updates. Hardware acceleration, suspend, proprietary GPU support, Secure Boot, accessibility and upgrades need explicit release validation. Merely including signed boot packages does not prove Secure Boot compatibility.

The b43/b43legacy firmware download helpers and their externally extracted firmware are removed before image creation. Legacy Broadcom adapters requiring those payloads are not supported out of the box. Firmware distributed as Debian archive packages retains its packaged licensing documentation.

Primary references: [Debian Live](https://www.debian.org/devel/debian-live/), [Debian Live Manual](https://live-team.pages.debian.net/live-manual/html/live-manual.en.html), and the installed `calamares-settings-debian` package configuration captured in `evidence/calamares-upstream.txt`.
