# V4 native panel and icon milestone

This is a real installed Debian/Plasma Wayland fork, `SteinsOS-V4-Design`.
It is an experimental review checkpoint, not a new ISO or daily-use release.
`dist/v4/BUILD-SET.json` pins the exact first-party packages and SHA-256 values.
V3 sources, packages, exports and native checkpoint remain separate.

## Actual checks

- The native bottom panel is 46px. Its 176×34px instrument is clickable, with
  restrained world accents. Tasks, tray, clock and launcher remain native.
  Guest geometry fits every applet; saved order is `18;31;19;20;21;29`, with
  exactly one V4 instrument and no V3 duplicate.
- SteinsLab provides 35 original semantic icons and 61 aliases, preserving the
  existing emblem byte-for-byte and inheriting upstream symbols for other apps.
  The identity evidence records 565 checks, including native Qt rendering and
  fallback lookup at 16/24/32px, bounds, and contrast.
- Six real world changes pass service-state, wallpaper URI/PNG hash and stable
  Bash PID/start-time checks in `six-world-runtime-final.json`. Shared graphite
  colours stay constant; artwork remains unchanged. Final Hinamizawa and
  Hitogashima pictures show the prepared desktop.
- Four style and 23 private-bus service tests pass. Actual Qt and GTK3 selection
  and focus were inspected. Generated Qt scheme IDs include the palette hash,
  fixing KDE's same-name apply no-op on the first V3-to-V4 login.
- The maintained QTermWidget frontend passes six substantive PTY/session/close
  tests (eight QtTest entries including setup/cleanup). Four token tests and
  actual navigator QML layout/keyboard checks at 880/650px pass. Native VM input
  created a fixture file through Bash; its PID survived world changes. See
  `native-input-proof.json` and the terminal screenshot.
- Actual mouse input opened meter controls, selected Hitogashima and launched
  V4 Worldlines through the service. Native tasks, Dolphin, launcher via Meta,
  calendar and tray were exercised. Qualification JSON records exact installed
  versions, working KVM/Wayland, no package-audit output and zero failed units.
- Native KSvg raster tests caught border seams missed by bounds-only checks.
  Final slices/stretch hints pass six cases with zero edge gaps: two popup
  sizes, widget, panel, task and list. Popups are opaque; panel alpha retains
  its intended 239/255 minimum. Before/after white-underlay proof and full
  loader/migration results are retained under `prototype/panel-v4/evidence/`.
- Native Plasma screen locking and real fixture-password unlocking pass.
  `lock-prompt-four-seconds.png` shows readable controls. Earlier clock-only
  shots caught the transition/idle state; a Space wake entered the hidden
  password buffer and caused one failure. Clearing it succeeded. No
  administrative unlock, replacement locker or authentication change was used.

## Migration and lab profile

The explicit panel preset backs up settings. `--replace-v3` changes only the
project instrument and project Navigator/Terminal aliases, deduplicating those
project pins. Plain apply preserves pins; third-party order and duplicates are
tested. Bounded indexed access supports actual Qt `V4Sequence` values. Window
presets preserve button layouts and shortcuts. No package selects themes at
installation.

The inherited X11 Light Locker failed under Wayland. The explicit guest lab
step backs it up and adds only KDE to `NotShowIn`, after confirming Plasma's
locker exists. Other desktops remain supported. The new boot has no failed
locker unit. KDE's `.local/state/plasmasessionrestorestaterc` retained three old
review apps; the lab now selects `emptySession`, backing up the setting and
retaining the old saved state.

Four tiny-QCOW2 tests cover seed/freeze/reset preservation, tamper detection,
duplicates and running guards. Serial protocol tests reject echoed commands,
stale/partial/non-numeric markers; real commands use unique start/end frames.
One manual harness invocation lacked Wayland environment and aborted the theme
utility; rerunning with the guest environment succeeded. No desktop crash was
observed in that case.

## Host wallpaper incident

A new style test initially mocked the Qt command but missed its desktop D-Bus
call, changing two host wallpaper Image values to a temporary test path. The
user identified Parrot Echo as the previous wallpaper. Both live values were
restored to `/usr/share/backgrounds/echo.jpg`; the recovery config diff contains
only those two Image lines. The test now mocks the adapter and uses a private
session bus. `host-wallpaper-recovery.json` records recovery; its host backup
stays outside this capsule. No host disk, bootloader, packages, shortcuts or
panel layout was changed.

## Remaining limits

QMP screenshots are real 1280×800/100% guest captures; isolated asset/QML/KSvg
proofs are labelled separately. Software graphics do not qualify GPU speed or
blur performance. Fractional scaling, wider resolutions, screen readers, IME,
hardware suspend and physical GPUs remain unqualified. V3's earlier mixed
manual-VT/Plymouth session-loss occurrence remains tracked in its own ledger;
V4 does not establish its cause or claim it fixed. No audio/compositor effect
was added.

The known-good XFCE ISO remains intact. A rebuilt and install-tested Plasma ISO,
future update/rollback qualification and hardware coverage remain release work.
This checkpoint is a reversible visual milestone with source, evidence and a
launch guide. The final checkpoint and preservation receipts accompany it.

## Frozen milestone and preservation

The cold `native-v4` checkpoint was captured after normal guest shutdown and
passed QCOW2 and complete backing-chain hash checks. Its disk SHA-256 is
`fd78cb81fc4dba02b74bdc5716c5ab1f12597b7388f9abdb6761456b24058576`;
NVRAM SHA-256 is
`b2e0f6cb677d0866cd5c088fcc99d6711fcb608c001fbd36647a923d09b9cefb`.
`freeze-native-v4.json` records the immutable ancestor pins.

`preservation-final.json` verifies the original prototype disk/NVRAM, ISO, V3
native disk/NVRAM and V3 review archive unchanged. All 401 source/package/evidence
members recorded by the V3 archive still match their original hashes. The
existing `SteinsOS-Test` libvirt VM is shut off and retained.


A fresh run booted from `native-v4`, passed the complete inventory again in
`qualification-reset-boot.json`, and shut down normally. Its current run image
passes `qemu-img check`; frozen disk/NVRAM hashes still match. The VM is left
off; earlier runs remain retained. The QA inventory now waits for the Plasma
bus owner and completed appearance, since a serial getty can be ready before
the graphical desktop. On this laptop the first serial-login wait also needed
a retry after the boot completed; no failed OS boot was observed.
