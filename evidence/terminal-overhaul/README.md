# Terminal overhaul screenshots

These are real renders of Debian 13's `xfce4-terminal` 1.1.4 (VTE 0.80) under Xvfb with `xfwm4`, at 1440 × 900 and scale 1. They were captured in a disposable `debian:trixie` container that had this branch's overlay and the Steins-Lab theme (built as `configure-system` builds it). `steins-worldline apply` ran as a fresh user created from `/etc/skel`. They are not VM or hardware captures.

| File | Source | Worldline |
| --- | --- | --- |
| `before-steins-gate.png` | `main` (eb54adf) | Steins Gate 1.048596 |
| `after-steins-gate.png` | `feature/terminal-overhaul` | Steins Gate 1.048596 |
| `six-worldlines.png` | `feature/terminal-overhaul`, window captures at 50% | All six reference numbers |

The container's own `os-release` (Debian), kernel and CPU appear in `steins-info`. In the installed image, the OS line reads Steins;OS.
