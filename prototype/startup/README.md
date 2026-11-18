# Steins;OS V3 native Plymouth prototype

This is an **actual optional Plymouth script theme**, built as a separate Debian package. It is no longer just the V2 animation viewer. Its real script/parser/native-library tests pass, but physical/VM boot rendering, authentication prompting and initramfs deployment still require the guest qualification below. The working prototype, reference theme, host and known-good ISO remain untouched by this component.

## Design and implementation

The existing Steins;OS emblem is retained, with unchanged vector geometry. It resolves through a restrained clip/trace treatment on graphite, briefly shows the public illustrative calibration `1.048596`, then settles to a static mark, title and genuine status. It never reads a user's home, session D-Bus or personal divergence before authentication. No audio is played.

Three explicitly selected system-wide themes are included:

| Theme | Policy |
|---|---|
| `steins-lab-v3` | One 33-frame assembly at requested30Hz, nominal1.1seconds; then static |
| `steins-lab-v3-reduced` | Three opacity steps, nominal100ms, no travelling traces or digits |
| `steins-lab-v3-static` | Static mark immediately, no decorative animation |

These durations are **nominal frame budgets**, not a wall-clock or boot-time guarantee. The exact native24.004.60 API schedules refresh callbacks, not an elapsed-time argument. Slow scheduling can stretch decoration; it cannot hold up boot, readiness, shutdown or authentication. There are no sleeps, external processes, network calls or quit handlers. Plymouth may remove the splash at any time. The active callback drops to5Hz after settling and only reflows if geometry changes.

Password/question callbacks immediately settle the mark, remove transient imagery and take precedence over background status messages. Password text consists only of the supplied prompt plus masked bullet count. Ordinary status is restored after normal-display mode returns. Startup/shutdown/reboot/update/reset wording uses the verified native `Plymouth.GetMode()` API. These properties were executed through the real native script libraries; a real initramfs/password/TTY test remains necessary.

The assembly PNGs are small fixed assets, not video, shaders or a new renderer. Their original source SVGs are retained in `assets/`. `build.py` uses the existing Debian builder container's librsvg and the host's existing dpkg-deb; it installs no host package and never selects a theme.

## Build and native checks

From the repository root:

```sh
python3 prototype/startup/build.py
python3 prototype/startup/test_native.py
```

Output: `dist/v3/startup/steins-startup-prototype_0.1.0~v3.2_all.deb` plus `BUILD.json` with hashes/provenance.

The native test opens the installed Plymouth24.004.60 `script.so` directly, with an **empty display list**. It does not start plymouthd or open DRM/framebuffer/VT devices. Actual script parsing/execution, Image/PNG/text, Sprite state, refresh callbacks and password/question/normal/status callbacks are exercised across3policies×8modes×2scenarios: **48 cases pass**. They verify finite animation settlement, correct mode labels, no background-message or refresh overwrite of auth prompts, normal-status restoration and settled resize reflow to800×600. `evidence/native-tests.json` and `native-tests.log` retain the results. This is native-engine evidence, not a captured boot or successful disk-unlock authentication.

## Disposable guest qualification only

Do not run these commands on Parrot or select this theme on the host. Use the isolated `SteinsOS-V3-Integration` fork. The completed V2 validation run remains frozen. The package contains no maintainer scripts and does not select itself or rebuild initramfs automatically.

1. Boot/log into the already prepared disposable fork using `prototype/integration/vm_lab.py`, preserving previous retained runs. Transfer the `.deb` using `prototype/integration/push_guest.py`, with a unique guest filename under `/tmp/v3-integration/`. These helpers verify the V3 QEMU identity; use them for this deployment rather than the V2 helpers.
2. **Inside the disposable guest**, record current theme and kernel command line, install, select and rebuild only that guest's initramfs:

```sh
plymouth-set-default-theme
cat /proc/cmdline
sudo dpkg -i /tmp/v3-integration/steins-startup-v3.deb
sudo plymouth-set-default-theme steins-lab-v3
sudo update-initramfs -u -k "$(uname -r)"
```

The transfer helper's actual selected destination must match the path used above. A `splash` kernel option is needed to see graphics during normal boot. If absent, make any required GRUB setting only in the disposable guest, back it up there and run its normal update-grub. Never change host GRUB/firmware for this test. Keep the current `steins` theme installed as fallback.

3. Reboot normally and capture the native splash through the fork's private QMP display. Confirm it disappears when login is ready, verify normal desktop/worldline state and record the actual Plymouth package/version and selected initramfs contents. Repeat static/reduced selection plus guest initramfs update for motion-policy qualification as practical.
4. On a separate disposable run, exercise real Plymouth password/question/display-message/normal callbacks through its standard client while the splash is active; preserve normal text/TTY fallback. Do not simulate successful authentication merely by typing a dummy masked prompt. A failed parse, absent PNG, unreadable prompt or splash blocking handoff is a failure requiring rollback.
5. Capture normal shutdown/reboot mode wording. Confirm no audio process/device/mute change or fixed waiting was introduced.

Rollback is guest-only: reselect the previously recorded theme (normally `steins`), run guest `update-initramfs -u -k "$(uname -r)"`, and reboot normally. A cold `python3 prototype/integration/vm_lab.py reset baseline` returns to the inherited checkpoint and discards this guest installation while retaining the previous run. No qemu-img commit/rebase is needed. The packaged generic README directs reviewers to this source document. Version0.1.0~v3.2 adds the GRUB assets/helper below; the validated Plymouth scripts and artwork bytes remain unchanged.

## Scope and source evidence

- The `.deb` contains the optional Plymouth themes, original GRUB backgrounds/SVG sources, one explicitly invoked guest-only apply/rollback helper, and documentation. It has no maintainer scripts, hooks, services or automatically enabled configuration.
- Real boot/prompt/font/DRM/multi-output/low-resolution/TTY fallback results belong to the lead engineer's guest ledger. These are not inferred from48headless cases.
- `evidence/upstream.json` records the exact official Debian source archive and hash. Preserved upstream source extracts retain their GPL-2.0-or-later headers; `upstream-COPYING` provides the license. Project scripts are MIT; original emblem/derived raster artwork is CC-BY-4.0, Steins;OS contributors.
- [Official Debian24.004.60 source archive](https://deb.debian.org/debian/pool/main/p/plymouth/plymouth_24.004.60.orig.tar.xz), [upstream script library](https://gitlab.freedesktop.org/plymouth/plymouth/-/tree/main/src/plugins/splash/script).

## Optional GRUB continuity — package0.1.0~v3.2

Original graphite/amber backgrounds are included at1280×800 and1366×768. Their main menu region is uniform dark graphite; a tiny unchanged current emblem sits in the top-right header margin, with restrained calibration corners. No instructions, menu entries or fake progress are baked into the art. Source SVGs remain beside the PNGs under `/usr/share/steins/startup/` and in this source folder's `assets/grub/`.

The explicitly invoked helper changes only `/etc/default/grub.d/steins-lab.cfg`, selecting this background and stock gfxterm. It sets an empty `GRUB_THEME` so an existing graphical theme does not mask the background. It keeps stock GRUB fonts/default high-contrast menu colors and leaves kernel arguments, timeout, default entry and graphics resolution alone. Debian's installed00_header/05_debian_theme scripts were inspected: `GRUB_BACKGROUND` is supported; unsupported `GRUB_COLOR_*` variables were deliberately avoided.

Installing the package does **not** enable this. Run only **inside the named V3 guest**, after its normal package installation:

```sh
printf '%s\n' 'SteinsOS-V3-Integration' | sudo tee /run/steins-startup-v3-allow >/dev/null
sudo /usr/lib/steins/startup/grub-lab.py apply --resolution 1280x800
```

Choose `1366x768` instead when that matches the test's GRUB framebuffer. The asset remains uncluttered if the existing framebuffer scales it. The helper refuses bare-metal/non-QEMU hosts, non-root execution, an absent/wrong explicit `/run` marker, symlink/unsafe config paths and a second active opt-in. It calls the guest's normal `update-grub`; no grub-install, EFI write, partition command, host path or initramfs rebuild is used for this background operation.

Before changing its own cfg, it retains exact previous bytes/mode (or records absence), hashes and a copy of the generated `/boot/grub/grub.cfg` under `/var/lib/steins-startup-prototype/grub-backups/<timestamp-id>/`. If generation fails, it restores the previous own cfg and generated menu. Backups are retained. Root-owned package files are normalized to0644 and the helper to0755; workstation group-writable umask is not propagated.

Rollback, **inside the V3 guest**, recreates the `/run` opt-in after reboot and restores the last backup:

```sh
printf '%s\n' 'SteinsOS-V3-Integration' | sudo tee /run/steins-startup-v3-allow >/dev/null
sudo /usr/lib/steins/startup/grub-lab.py rollback
```

Later manual edits to `steins-lab.cfg` cause refusal instead of silent overwrite. Roll back before applying a different size. The guarded V3 cold reset remains the broader recovery option, with previous runs retained. `test_grub_helper.py` exercises temporary files and a fake generation callback only; it never runs host update-grub. Eight tests cover exact restoration, absence/neighbour preservation, generation-failure recovery, subsequent-edit/tamper/symlink guards and ordinary-user CLI rejection. Actual GRUB menu readability/loading still requires the lead engineer's V3 reboot capture.
