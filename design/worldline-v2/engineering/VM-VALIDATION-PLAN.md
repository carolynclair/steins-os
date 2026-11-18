# Repeatable isolated V2 VM validation

**Outcome available now:** a guarded cold-checkpoint/fork launcher, a replay/test plan, and fresh lead-engineer tests of the existing Plasma prototype in a separate V2 fork. Helper tests and actual guest tests remain distinct below; new design boards are not treated as installed applications.

The existing `SteinsOS-Test` libvirt domain and standalone `SteinsOS-Design-Prototype` remain untouched. The new helper uses **`SteinsOS-V2-Validation`**, private control sockets and new files under `evidence/v2-vm-validation/`. It does not edit a libvirt definition, host partition, bootloader, KDE configuration or original VM disk.

## Why a cold fork

An overlay directly backed by the writable original prototype is not a stable checkpoint if the original later changes. The helper instead copies the cold prototype overlay plus its UEFI variables into a read-only checkpoint, pins the SHA-256 of the unchanged standalone QA backing disk, and creates new run overlays against that checkpoint. Current captured overlay data is about 2 GiB; it does not duplicate the full 32-GiB virtual capacity.

The original QA backing must remain immutable and available. This external chain is a point-in-time lab recovery mechanism, not an independent portable backup or a reproducible clean ISO build. QEMU documents offline image operations and warns against modifying in-use images; its backing-file mechanism stores only changes unless a commit operation is deliberately used. This helper never commits/rebases or repairs a base. [QEMU image utility](https://www.qemu.org/docs/master/tools/qemu-img.html).

The copy is cold-only: the helper rejects a live recorded PID, any visible QEMU process, or a running libvirt guest; checks format/backing/owner/symlink boundaries; verifies source did not change during capture; records disk/NVRAM/backing hashes; and runs a non-repair `qemu-img check` on the new copy. Checkpoint names cannot overwrite prior checkpoints. Reset creates a new run and UEFI copy, retaining every previous run.

## Commands

From the repository root, after normally shutting down other guests:

```sh
python3 design/worldline-v2/engineering/vm_lab.py checkpoint baseline
python3 design/worldline-v2/engineering/vm_lab.py start baseline
python3 design/worldline-v2/engineering/vm_lab.py view
```

Capture hashes read several GiB before boot; this preflight work is not guest startup latency. No administrator command is required. The launcher uses the existing KVM membership via `sg kvm`, 6 GiB RAM/2 vCPUs, OVMF, VirtIO disk, 2D VirtIO video, user-mode NAT and local-only SPICE. It checks available RAM and storage. Clipboard/file transfer and host folders/devices are not exposed.

Normal shutdown and status:

```sh
python3 design/worldline-v2/engineering/vm_lab.py stop
python3 design/worldline-v2/engineering/vm_lab.py status
```

`stop` requests ACPI shutdown; it does not forcibly kill the guest and does not declare completion. If the desktop asks for confirmation, use its normal shutdown controls or the authenticated guest command. Wait for status `off` before reset. Closing the viewer only disconnects.

Cold reset to the saved baseline, preserving the previous run:

```sh
python3 design/worldline-v2/engineering/vm_lab.py reset baseline
python3 design/worldline-v2/engineering/vm_lab.py start
```

`baseline` captures the original installed prototype, before V2 fork-only hotfixes. Reset deliberately discards those later fork changes. Preserve the final fixed run for review. After starting/logging into a reset fork, run `python3 design/worldline-v2/engineering/apply_fork_fixes.py` to replay only the meter/service files; do not describe the original checkpoint as already containing the V2 fixes. The helper's checkpoint command captures the original prototype, not an arbitrary current V2 run.

Inspect the frozen checkpoint without changing it:

```sh
python3 design/worldline-v2/engineering/vm_lab.py verify baseline
```

This V2 guest is a standalone validation process, not a new persistent virt-manager entry. The original `SteinsOS-Test` entry continues to use its own lab commands. Do not run `lab/setup.sh` again just to launch a guest, and do not point its root checkpoint helper at these files.

## Guarded test controls

After the cloned guest reaches its serial login prompt:

```sh
python3 design/worldline-v2/engineering/vm_lab.py login
python3 design/worldline-v2/engineering/vm_lab.py guest 'uname -r; loginctl list-sessions --no-legend'
python3 design/worldline-v2/engineering/vm_lab.py query query-kvm
```

`login` uses only the existing public disposable `observer` / `SteinerTest42` fixture account, not Gary's host password; it prepares that guest's sudo cache. Every monitor and serial operation first verifies the exact V2 QEMU name. `guest` isolates stdin, waits for a unique completion marker and propagates the command's exit status. A timeout is a failure, not evidence that the command succeeded.

Use `screenshot NEW_PROJECT_PATH`, `key CHORD`, `text ASCII` and `click x,y,width,height` for owned-guest input/captures. These do not operate on the host keyboard or the review VM. The helper refuses screenshot overwrite and only writes inside the project.

`push_guest.py SOURCE` exposes one project/test file through a bounded loopback server, transfers it to a new `/tmp/v2-validation/` filename and stops the server. It refuses existing destination files. The old `prototype/guest.py` and `prototype/transfer.py` hardcode the original UART, so **do not use them for this fork**.

```sh
python3 design/worldline-v2/engineering/push_guest.py prototype/runtime_check.py
python3 design/worldline-v2/engineering/vm_lab.py guest \
  'export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus; python3 /tmp/v2-validation/runtime_check.py' --timeout 55
```

That runtime test deliberately changes divergence/meter settings inside the disposable fork and returns to Steins Gate. It does not implement or test native cinematic effects. Reboot clears `/tmp`; transfer test files again when needed.

## Graphics, Wayland and sound limits

The current baseline uses `virtio-vga`, not `virtio-vga-gl`, and no render node/EGL/GL display configuration. QEMU's 2D backend requires a guest software renderer for 3D. Virgl is a different accelerated backend with host/guest graphics requirements; KVM CPU acceleration does not prove GPU acceleration. Keep 2D as the deterministic functional baseline. A future accelerated fork needs capability/dependency/permissions review and separate A/B evidence before changing the configuration. [Official VirtIO GPU documentation](https://www.qemu.org/docs/master/system/devices/virtio/virtio-gpu.html).

The earlier guest did run Plasma Wayland and open SPICE main/display/cursor/input channels. Those results do not prove native distortion performance, fractional scaling or sound. Record KWin renderer information and software-renderer warnings; distinguish functional product defects from unqualified GPU performance. Input loss, mismatched state, unreadable controls and incorrect error reporting remain defects regardless of rendering mode.

No guest sound card is explicitly configured in the baseline. QEMU can auto-select the SPICE audio backend when SPICE is present, but that does not create/validate the complete guest device→session mixer→client playback path. Product source also lacks custom cue wiring. Do not report a cue integrated merely because a WAV exists or a SPICE display connects. An output-only virtual audio device/transport experiment may use a separate disposable fork with existing capabilities; new dependencies or broader deployment need approval. do not enable microphone forwarding. Then verify guest sink, mute/volume, output routing and actual optional cue events. [QEMU invocation/audio backends](https://www.qemu.org/docs/master/system/invocation.html).

## Required guest matrix

| Area | Actual check | Evidence / acceptance |
|---|---|---|
| Startup | Cold boot from recorded run/checkpoint; timestamp guest readiness | New QMP/KVM/versions and screenshot; separate hashing time from boot |
| Login | Lab autologin, then a deliberate lock/unlock with fixture credentials | Real authenticated session type; do not substitute mockup image for password test |
| Terminal | Open actual Konsole fallback, resize, copy/paste within guest, Unicode, shell job, full-screen TUI where installed | Actual PTY output/process continuity; do not claim new terminal frontend compatibility |
| Shell | Launcher/task switch/tray/settings/notification/power controls | Real captures and keyboard actions, normal focus/selection; new custom shell remains unbuilt |
| Worldline | GUI, meter, IBN/CLI entry paths; state/palette/wallpaper; explicit invalid/reapply cases | Same confirmed number and real surface state; report partial failures. No staged cinematic effect claim |
| Notifications | Send a local test notification if installed tooling supports it | Visible readable normal notification; no external message/account action |
| Audio | Inventory device/backend/sinks first | Mark transport/cue integration untested until an approved audio-capable run exists |
| Lock | Lock and authenticate normally; restore applications | Do not disable locking to claim it works; confirm return to same processes |
| Shutdown/reset | Normal guest shutdown; fresh retained reset; boot baseline again | QEMU exited, old overlay/NVRAM retained, new run differs and starts cleanly |

Run one heavy VM at a time on the N4500. Record exact artifact/package hashes, QEMU/firmware versions, renderer, memory and observed errors. A test not executed stays **untested**; an unavailable optional effect stays **unimplemented/unqualified**, not a passing transition.

## Reproducible installation gap

The current checkpoint can repeat the installed prototype, but its initial Plasma installation was assembled from recorded APT commands rather than a fully version-pinned image recipe. Existing source can rebuild the Steins native packages into a separate output directory; it does not yet produce the redesigned Plasma ISO.

A future replay recipe should start from the known v8 installed QA image, record Debian source/suite/package versions, review the proposed APT changes, install the exact prototype packages by SHA, apply guest-only session defaults and run the matrix before freezing a new checkpoint. New dependencies or a desktop migration need the owner's requested approval. Do not add host packages or overwrite the ordinary ISO export in order to make a quick visual test.

## Helper verification performed

`python3 design/worldline-v2/engineering/test_vm_lab.py` passed 8 tests using temporary 16-MiB qcow2 fixtures: capture preserves source bytes/permissions and pins backing; reset preserves old runs/UEFI variables; duplicate checkpoint refuses overwrite; backing/copy tampering is detected; path/symlink escape is rejected; and a failed cold guard prevents creation. No VM start occurred in those tests. The lead engineer's actual fork/boot/reset evidence belongs in a separate runtime ledger.

## Actual V2 fork checks now recorded

The lead engineer subsequently captured the cold baseline and booted the isolated V2 guest. `design/worldline-v2/evidence/vm-checkpoint.log` and `vm-start.log` identify that run; the original prototype and libvirt review VM were preserved. No new dependencies, virtual 3D backend or sound device were added.

The 21/21 runtime suite confirms normal Wayland/shared-state/worldline surface changes and notification acceptance on the inherited Plasma 6.3.6 guest. Actual Konsole/Bash tests confirm PTY I/O, Unicode/ANSI, resize with the same shell process, exact fixture copy/paste and a basic installed `vi` edit/save. Actual lock/password-unlock returned the ScreenSaver state from true to false. See `runtime-results.json`, `pty-live.log`, `pty-resize-clipboard.log`, `pty-copy.log`, `vi-live.log`, `lock-state.log`, `unlock-final.log` and the real guest captures in that evidence folder.

The two meter files were backed up and hotfixed **only inside the V2 fork**. `meter-live.log` verifies Full schedules its real GTK timer, Reduced cancels stale frames and retains confirmed digits, and Off stays static. This is a real expanded-meter fix; it does not add service-level cinematic stages or a native KWin effect. Source also contains a mode-aware Plymouth text helper, but no updated booted initramfs is claimed.

Cold reset also reproduced a startup dependency race: restored numeric state was correct, but wallpaper application failed before plasmashell registered its D-Bus name and the old service cached that failure. The source correction adds only bounded 1/2/4/8/16-second retries for the three specific transient wallpaper D-Bus errors. The 17 private-bus tests pass; they establish finite recovery policy, no state rewrite and stale-callback cancellation, not a live boot pass. The patched-service fresh boot passed. A controlled real-shell outage then produced the expected transient failure and recovered automatically after the shell returned, without changing divergence or issuing another reapply; `../evidence/live-startup-recovery.log`.

Audio inspection found no sound cards and only the `auto_null` PipeWire sink. Therefore physical audibility, cue delivery, mute/routing behaviour and a real login-ready sound remain untested. SSH, Zsh and Neovim were absent; the successful `vi` fixture cannot substitute for those tests or for a new terminal frontend's compatibility matrix.

Actual cold reset removed the persistent fixture canary and restored saved Hitogashima `3.072100` / meter enabled / Reduced. The final fixed run is retained for review. Read the final V2 ledger for shutdown, QCOW2 integrity and original-file preservation evidence.
