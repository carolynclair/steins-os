# Steins;OS V4 Plasma installer

Prepare the V4 ISO inside a Debian 13 live-build guest. Use the prepared XFCE
live-build tree for the existing Debian boot and Calamares integration. Use a
package tree containing the four version-matched base packages and the tested
V4 core, identity, panel, surfaces and terminal packages. Build the V4 core
with the artwork manifest that matches the intended wallpaper set.

From an empty working directory inside the builder guest:

```sh
/path/to/iso-v4/prepare.sh /path/to/prepared-xfce-build /path/to/dist
sudo lb config
sudo lb build
```

The V4 image selects Plasma through SDDM. It keeps the underlying XFCE
packages because the current V4 core shares runtime code and package
dependencies with the XFCE edition. A fresh Plasma account starts with the
V4 panel, including the divergence meter, and the SteinsLab Plasma and icon
themes. Debian's live-config handles live autologin, and Calamares configures
the installed user's login.

Validate the resulting hybrid ISO with a disposable BIOS guest and an offline
UEFI guest with an empty virtual disk. Check the V4 panel and wallpaper in the
live session, then complete the offline installation and boot the installed
disk by itself.

## Local build, 2026-11-19

The image is `steins-os-v4-amd64.iso` (3,301,883,904 bytes). Its SHA-256 is
`258914e7378a1e0e51a5a080ebf6416fe5bcc32da26042343fbf6971a3c5deba`.
The image checks verified the hybrid boot entries, nine Steins packages,
the offline GRUB pool, and all six wallpaper hashes. BIOS and UEFI reached
the V4 live desktop, and all six live worldline switches passed. Calamares
completed automatic unencrypted UEFI installation without a network adapter.
The installed disk booted with the ISO detached and accepted a password
login into Plasma Wayland with the V4 panel and default wallpaper.
The live account and Calamares were removed during install. The terminal
prompt still displayed `(live)` after installation even though the root
filesystem was mounted from the virtual disk.
