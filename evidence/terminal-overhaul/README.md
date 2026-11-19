# Terminal overhaul screenshots

These are real renders of Debian 13's `xfce4-terminal` 1.1.4 (VTE 0.80) under Xvfb with `xfwm4`, at 1440 × 900 and scale 1. They were captured in a disposable `debian:trixie` container that had this branch's overlay and the Steins-Lab theme (built as `configure-system` builds it). `steins-worldline apply` ran as a fresh user created from `/etc/skel`. They are not VM or hardware captures.

| File | Source | Worldline |
| --- | --- | --- |
| `before-steins-gate.png` | `main` (eb54adf) | Steins Gate 1.048596 |
| `after-steins-gate.png` | `feature/terminal-overhaul` | Steins Gate 1.048596 |
| `six-worldlines.png` | `feature/terminal-overhaul`, window captures at 50% | All six reference numbers |

The container's own `os-release` (Debian), kernel and CPU appear in `steins-info`. In the installed image, the OS line reads Steins;OS.

## Live ISO guest captures

These were captured from QEMU 8.2 in software emulation (no KVM): BIOS boot, 4 vCPUs, 4 GiB, `-vga std` at 1280 × 800, scale 1. The live session's own autologin user was used, the default divergence was in effect, and Ctrl+Alt+T opened the terminal.

| File | ISO built from | Notes |
| --- | --- | --- |
| `live-iso-before-fix.png` | `d77111a` | First-login bug (also present on `main`): the first session's worldline apply created the xfconf channel, so the skeleton `terminalrc` was never migrated. The result was a visible menubar, no login shell and no prompt, plus a wrapped `steins-info` line at 80 columns. |
| `live-iso-after-fix.png` | `d5560bc` | Profile applied at login: greeting, prompt, exit status, timing, JetBrains Mono, margin and shell-set title. The garbled first command is the test's key-sender, which lacks `(` and `_` mappings. |
| `first-login-main-vs-branch.png` | `main` / `d5560bc` | Container reproduction of the same first-login sequence (channel saved before the terminal starts), shown at 900 × 560. |

Local build note: the build container's TLS-intercepting proxy CA is not trusted inside the live-build chroot. `firmware-b43-installer` and `firmware-b43legacy-installer` therefore cannot download firmware during the build. For these local verification ISOs only, two empty same-name stand-in packages were placed in `config/packages.chroot`; they are not committed. The project hook `0900-steins.hook.chroot` purges both packages anyway, and the image check confirmed neither is installed.
