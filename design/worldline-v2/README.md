# Steins;OS V2 — review response and refinement

This pass responds to Burrito's [complete V2 review](OWNER-REVIEW.txt). The screenshots supplied with it were treated as inspiration; they were not traced, reused as product art, or treated as instructions overriding the written review.

**The new terminal, panel details, logo alternatives and cinematic boot are design previews.** Existing Linux functionality was separately tested in a real, isolated VM fork. Three low-risk source defects were fixed; the working prototype, its selected state, existing ISO, V1 designs and Parrot desktop were preserved.

## Start here

![Refined terminal preview](boards/terminal-floating-steins-gate-1920x1080.png)

- [Review response, priorities and dependencies](engineering/REVIEW-RESPONSE-AND-PLAN.md)
- [Implementation inventory: working / partial / mock-up / missing](engineering/IMPLEMENTATION-INVENTORY.md)
- [Current emblem and three original alternatives](identity/comparison-sheet.png) — none selected or installed
- [Boot storyboard and audio audit](startup/BOOT-AUDIO-AUDIT.md)
- [Repeatable VM process and limitations](engineering/VM-VALIDATION-PLAN.md)
- [Verification ledger](evidence/VALIDATION.md)

The illustrated Akihabara, Hinamizawa and island scenes are byte-for-byte copies of the V1 design assets. No replacement artwork was generated. The current logo remains the default in the previews; alternative marks appear only on their comparison sheet.

## Terminal refinement

The terminal now has a collapsible session rail, custom active/inactive tabs, a reserved tube readout, shared calibration-corner treatment, restrained palette and useful footer. The output area remains dominant. Rail and tabs are two views of one proposed session model, not separate process managers.

Authored states: [floating](boards/terminal-floating-steins-gate-1366x768.png), [tiled](boards/terminal-tiled-steins-gate-1366x768.png) and [maximised](boards/terminal-maximised-steins-gate-1280x800.png). The compact/tiled state collapses the rail instead of shrinking terminal text. The [neutral-background composition](boards/shell-plain-steins-gate-1920x1080.png) tests the shared shell grammar.

These are editable SVG mock-ups, not a new terminal executable. Current runtime uses Konsole's real PTY engine. An original frontend around a maintained component still needs the component/API/dependency decision and compatibility work. No QTermWidget or new development dependencies were installed. The existing KonsolePart/KF6 runtime on the host is not proof that a new frontend has been built or that bindings/development headers are available.

The runtime checks exercised existing Bash/PTY behaviour, ANSI true colour, Unicode, resizing while a process stayed alive, fixture copy/paste and a basic `vi` edit. They do not establish full Vim/Neovim, Zsh or SSH compatibility of the proposed frontend. SSH client, Zsh and Neovim were absent from this minimal guest; new dependencies remain an approval item.

## Boot, shift and audio boundaries

The native review viewer can play a contained **1,100-ms boot concept**: signal emergence, original emblem trace/fragment assembly, public illustrative digits, stabilisation and login handoff. Full is manually selected; Reduced uses a short static-mark fade, Off changes immediately. The sequence never reads a user's private pre-login worldline state.

This is not deployed Plymouth, an SDDM animation or an end-to-end boot. Real startup must be readiness-driven and never wait to finish the design timeline. Current Plymouth shows the original logo and a quiet activity pulse. There is no native KWin worldline effect or coordinated 800-ms transaction pipeline yet.

Original sound assets exist, but there is no custom cue playback integration. The test guest exposes no emulated sound card and uses an `auto_null` sink. SPICE presence alone is not evidence of audible output. No cue was automatically played; silence remains the default. See the audit for missing mute/volume/readiness/notification integration and appropriate boot/display-manager boundaries.

## What was fixed

1. **Reduced/Off meter motion:** the actual meter now reads the shared motion preference, stops active scrambling, rejects stale queued frames and shows the confirmed number. Atomic preference replacement is observed. Twelve regression tests and a real GTK-window test in the disposable fork passed. Legacy absent preferences retain their old behaviour; Plasma defaults to Reduced; corrupt/unreadable preferences fall back to Reduced.
2. **Plymouth status text:** a source patch uses the verified `Plymouth.GetMode()` API to distinguish startup, shutdown, reboot and update/reset labels. Password/question callbacks are unchanged. This patch is not installed into an ISO/initramfs and has not yet been visually qualified in a real Plymouth session.
3. **Early Plasma startup recovery:** the worldline service previously cached a failed wallpaper apply if plasmashell was not ready at login. It now retries only specific transient wallpaper D-Bus errors, at most five times, and cancels stale requests. Seventeen private-bus tests passed. The patched fork rebooted successfully; a controlled real-shell outage then recovered automatically without another ApplyCurrent call or any divergence-file change. See [live recovery evidence](evidence/live-startup-recovery.log).

The meter and service hotfixes were exercised only in the validation fork, with the packaged originals backed up. They are not silently deployed to the user's working prototype or published packages. Patches, pre-change copies and a portable source map are retained under `startup/`, `engineering/` and `patches/`.

## Open the read-only preview

```sh
/usr/bin/python3 '/home/developer/Documents/ChatGPT/Steins;OS/design/worldline-v2/preview/review.py'
```

Choose a terminal state, scene or logo comparison; use **Boot preview** or **Preview shift timing**. Those animations stay inside the review window and do not change the desktop, VM, worldline state or audio. V1 remains available separately.

The source renderer is `build_v2.py`; `common_board.py` is a helper. The viewer uses the host's existing PySide6 Qt Widgets. No packages or host configuration were installed for it.

## Isolated VM use

The prepared test fork is `SteinsOS-V2-Validation`, not `SteinsOS-Test` or the working standalone prototype. Checkpoint/reset are cold-only, retain old runs and verify hashes. All disk writes are QCOW2 files; no host block device, shared folder, clipboard bridge or USB device is exposed. Only one heavy VM should run on this two-core host.

```sh
python3 design/worldline-v2/engineering/vm_lab.py start baseline
python3 design/worldline-v2/engineering/vm_lab.py view
python3 design/worldline-v2/engineering/vm_lab.py stop
python3 design/worldline-v2/engineering/vm_lab.py status
# Once fully off, create a fresh run; previous runs remain retained:
python3 design/worldline-v2/engineering/vm_lab.py reset baseline
```

These commands require the already prepared local checkpoint/QA backing files; the review ZIP does not contain VM disks. [The VM plan](engineering/VM-VALIDATION-PLAN.md) distinguishes this repeatable local process from a not-yet-rebuilt Plasma ISO or a clean independent installation recipe.

Reset restores the inherited baseline, before these hotfixes. After starting and logging into a reset fork, `python3 design/worldline-v2/engineering/apply_fork_fixes.py` replays the tested meter/service files only into that named fork. The final retained run already contains them. Plymouth is deliberately excluded from this replay.

## Approval boundaries

Your review explicitly says to request approval for major architecture changes or new dependencies and to preserve the working environment. This pass therefore presents logo choices, the terminal frontend/component decision, native effect work and the final shell migration for approval. The requested low-risk fixes and isolated validation have been carried out. No default logo was replaced, no new dependency was installed and no working VM was migrated.

## Review package

Finalised 2026-11-02 NZDT. The ZIP contains these previews, the read-only viewer, audits, portable source snapshots and test evidence. It excludes VM disks, firmware-variable images and ISOs. `MANIFEST.json` records every included file hash; the adjacent ZIP SHA-256 and archive CRC/hash check verify the handoff. Extract into a separate folder for review; do not unzip over a working checkout as an update.
