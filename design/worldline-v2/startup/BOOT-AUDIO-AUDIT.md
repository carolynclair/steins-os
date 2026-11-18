# V2 startup, transition and audio audit

2026-11-01. This is a source/asset audit and an improved **design preview specification**, plus the explicitly authorised meter reduced-motion source correction described below. No theme, display manager, compositor effect, audio service or VM device was installed by this component of the review. The existing working VM and ISO were not modified. Parent integration tests a separate V2 fork; its evidence is reported independently.

## Implementation inventory: what actually exists

| Area | Confirmed source/asset evidence | Actual status |
|---|---|---|
| Plymouth boot splash | `config/includes.chroot/usr/share/plymouth/themes/steins/steins.plymouth:4–7` selects the script plugin/theme. `steins.script` draws the current logo and status. Its `refresh_callback()` that changes a three-dot sprite's opacity | **Implemented lightweight animation**, not wholly static. The logo itself is static. There is no assembly, calibration-digit sequence or cinematic handoff |
| Password/questions/status | `steins.script` registers password, normal-display, question and status callbacks | Real theme callbacks exist. They must remain authoritative/legible during any future animation; they are not decorative labels |
| Mode-specific normal text | At audit start `steins.script:14,23` always said `INITIALISING LABORATORY`; the V2 source now uses `normal_message()` both initially and on normal-display restoration | Confirmed defect corrected in source by parent using the verified mode API. This source fix is separate from cinematic integration and does not by itself prove a booted initramfs has been updated |
| Theme packaging/initramfs | `build-tools/build_packages.py:164–165` renders the existing emblem as `logo.png`. `packaging/configure-system:67–76` selects the theme and rebuilds initramfs when its digest changes | Implemented package integration. Merely editing a loose theme or a design image does not show that the booted initramfs uses it |
| Reference greeter | `config/includes.chroot/etc/lightdm/lightdm-gtk-greeter.conf:1–10`, package list lines 11–12 | The reference distro uses a branded LightDM GTK greeter. It is separate from the Plasma experiment |
| Plasma experiment login | `prototype/README.md:35`, `evidence/plasma-prototype/VALIDATION.md` document lab SDDM autologin/idle-lock settings | SDDM was installed in the disposable guest; this is not a shipped original SDDM login theme or production authentication configuration |
| V1 boot/login/lock boards | `design/worldline-v1/build_boards.py`; exported PNG/SVG boards | **Mockups.** No evidence of a new authenticating login surface, end-to-end boot choreography or lock-screen implementation follows from those images |
| V1 animated review | `design/worldline-v1/preview/review.py:25–46,100–119` draws images, a contained crossfade and diagrammatic curves with Full/Reduced/Off timing | A working **review-window animation**, not a Plymouth animation, login transition or KWin effect |
| Worldline state/apply | `prototype/worldline/lib/worldline_service.py` methods `SetDivergence()` and `apply()` prepare assets, save the number and apply; bounded retry now handles only transient wallpaper service errors. `steinsplasma.py:61–83` invokes Qt colour scheme, wallpaper and GTK selection operations | Functional partial integration. It applies supported surfaces sequentially; no staged native scene transaction or ripple is present |
| Meter movement | V2 source `steins-meter:102–155` observes the saved value and preserves fifteen 40-ms scramble/settle frames only for Full | Real digit animation existed; the V2 low-risk source fix now enforces Reduced/Off immediately and invalidates stale callbacks. Twelve headless flow tests pass; the parent also recorded a real GTK-window test in the separate fork (`../evidence/meter-live.log`) |
| Motion preference | `worldline_service.py` defaults and `SetPreference()` store `off`, `reduced` or `full`; `meterlib.motion_profile` reads that same preferences file; adapter `apply_prepared` still has no compositor effect | V2 source enforces the preference in the optional meter. It does not establish a reduced/native compositor transition pipeline |
| Original audio assets | `design/worldline-v1/engineering/audio/manifest.json` plus four WAVs; source generator explicitly writes files without playing them | **Assets, not integration.** Activation, meter, stabilise and combined 800-ms shift preview exist as original samples |
| Runtime playback | No playback call or custom sound-event wiring found in the audited `config/`, `prototype/`, packaging or V1 viewer | The custom worldline/startup cues are **not integrated**. Existing DE/terminal bell/user sounds are separate and were not changed or assessed here |
| Base audio stack | `config/package-lists/steins.list.chroot:17–19` includes PipeWire audio, WirePlumber and pavucontrol | Package intent/capability, not proof of an audible device, selected output, sound policy or cue playback |
| Standalone VM sound | `prototype/vm.py:44–53` includes GPU, tablet, NAT, serial/QMP and SPICE, but no emulated sound card; SPICE may auto-select an audio backend | The fork reports no cards and an `auto_null` sink. An explicit output-device/transport experiment in the disposable fork and audible-path test are needed; new dependencies or broader deployment require approval |

The direct answer to the review's audio question is: **the custom sound files exist; the sound system has not been wired to Steins worldline/login/notification/error events.** No audio was played while performing this audit.

## Low-risk meter correction applied to source

Only `config/includes.chroot/usr/local/bin/steins-meter` and `config/includes.chroot/usr/local/lib/steins/meterlib.py` were changed by this component, under the parent's explicit assignment. Pre-change copies are retained in `meter-before/`.

- Read the service's existing `preferences.json`; do not create another worldline/motion state file.
- Reduced/Off cancels any active GLib animation and writes the confirmed number immediately, **including when the confirmed number equals `self.shown` but an in-flight scramble remains visible**.
- Directory monitoring now recognises atomic replacements through either event path. Preference events refresh synchronously; divergence changes retain the existing short debounce.
- Every animation has a generation guard. A removed/superseded callback already queued for dispatch cannot overwrite stable digits or clear the new timer.
- Plasma with no preference file defaults to Reduced. Legacy sessions with no file preserve Full for compatibility. Corrupt/unreadable preferences fail safely to Reduced. Explicit Full retains the original tube style and fifteen 40-ms frames.

Executed `GIO_USE_VFS=local /usr/bin/python3 design/worldline-v2/startup/test_meter_motion.py`: **12 tests pass**. These call the actual unbound `MeterWindow.refresh`, `animate` and file-event methods using fake GTK state/captured GLib callbacks, not a duplicated animation implementation. They cover same-value cancellation, stale/superseded callback rejection, Full completion, atomic preference events and safe defaults. `python3 tests/check_worldlines.py`: **49 existing tests pass**. Logs are `meter-motion-tests.log` and `legacy-worldline-tests.log`. No host GTK window was opened, and these tests alone do not prove behaviour of the separately booted V2 guest.

## Proposed startup refinement

The reference image suggests a stronger visual focus and assembled light, but its metallic portal, composition and symbol are not copied. `boot-storyboard.svg` is original vector composition using the **unchanged current project emblem**. Candidate marks elsewhere in V2 are approval options; this sequence does not choose one automatically.

`BOOT-SEQUENCE.json` is the machine-readable contract. The contained Full preview targets 1,100 ms, bounded to 1,200 ms. It is not a claim about measured Linux boot time:

| Time | Treatment |
|---|---|
| 0–120 ms | A few low-contrast signal traces emerge on graphite; no repeated scanning flash |
| 120–480 ms | Trace fragments resolve into the existing mark |
| 480–720 ms | One brief provisional calibration-digit treatment, then stable public theme digits |
| 720–940 ms | Mark settles; temporary traces/digits recede |
| 940–1,100 ms | Background/mark continuity into the greeter **only when the real greeter is ready** |

Real readiness always wins. A fast boot may skip/shorten the sequence. A slow boot must not claim login ready at a fixed timestamp; it may hold a quiet static mark with genuine status. Never sleep the boot/authentication path to finish an animation. Password/question/error handling interrupts or suppresses decoration immediately. Reduced uses a 150-ms fade or static mark; Off keeps only a static mark and genuine status. Both avoid rolling digits, assembly travel and scanning.

Pre-login digits must be a **public theme calibration/default**, or be omitted. The initramfs/unauthenticated greeter must not read a personal divergence file, encrypted home or session bus. Actual user-worldline state belongs in the authenticated session. The storyboard's `1.048596` is illustrative/public, not evidence of the user's saved worldline.

## Correct integration boundaries

### Plymouth: early boot and shutdown

Plymouth's script plugin is already the maintained integration point. Port a small bounded sprite/trace treatment into that theme, retaining current password, question, normal and status callbacks and text/TTY recovery. Keep the first implementation asset-light; do not introduce a video decoder or GPU compositor dependency into initramfs. Do not infer a supported wall-clock animation API from the current frame-counter pulse: exact refresh/timing behaviour must be checked against the shipped plugin when implementing it.

The mode-label correction is independent and can be reviewed/tested first. Exact upstream **24.004.60** source, obtained from the official Debian pool, registers native `Plymouth.GetMode()` and returns `boot`, `shutdown`, `reboot`, `updates`, `system-upgrade`, `firmware-upgrade`, `system-reset` or `unknown`. Suggested normal-state wording: shutdown → `SHUTTING DOWN LABORATORY`; reboot → `RESTARTING LABORATORY`; updates/system-upgrade → `APPLYING SYSTEM UPDATES`; firmware-upgrade → `APPLYING FIRMWARE UPDATE`; reset → `RESETTING SYSTEM`; boot/unknown → existing startup text. A helper should be used both at first display and when returning from a prompt. Preserve explicit external status messages and auth callbacks.

`PLYMOUTH-SOURCE-EVIDENCE.json` records the official archive URL/hash and inspected member. This proves source API availability, not that a modified theme has been executed in a booted guest. The local host reports Plymouth `24.004.60-5`; a guest/package-version query and guest boot/shutdown capture are still required for a new theme. [Official Debian source archive](https://deb.debian.org/debian/pool/main/p/plymouth/plymouth_24.004.60.orig.tar.xz), [Debian source browser](https://sources.debian.org/src/plymouth/24.004.60-5/src/plugins/splash/script/script-lib-plymouth.c/).

Early-boot motion policy cannot simply consume an authenticated user's desktop preference. A future package-controlled static/default motion mode must be included in the initramfs theme; a session preference may separately govern greeter/session animation. Configure that deliberately rather than inventing a session-bus connection from early boot.

### SDDM: greeter and authentication

An original SDDM Qt Quick theme can carry the palette, mark placement and a brief nonblocking reveal. It must use SDDM's real user/session/keyboard models and authentication proxy; successful animation is never successful login. Include auth errors, Caps Lock, keyboard layout, session/account switching, focus and accessible password controls. Test the greeter's display backend separately from the user's Wayland desktop; a Wayland session does not prove the greeter also runs Wayland.

SDDM documents the login proxy and success/failure signals and has a greeter test mode whose actions do not authenticate or shut down the system. Theme-preview success therefore cannot replace an actual disposable-guest login test. Local host inventory lists SDDM `0.21.0+git20250502.4fe234b-2`; APIs/imports must be checked against the guest's exact package. No new SDDM theme was installed here. [Official SDDM theming documentation](https://github.com/sddm/sddm/wiki/Theming).

### Authenticated session: worldline and optional audio

Keep early boot silent. If the owner enables a readiness cue, play it once after authenticated session readiness, through the user's existing audio stack. Do not make initramfs, greeter or password entry depend on an audio server. The scene/background can align with the greeter, but a seamless framebuffer handoff is not guaranteed by matching colours: GPU modesetting, display-server startup and software-rendered VM behaviour need real testing.

## Audio integration still required

The four V1 assets were rechecked read-only with Python `wave`/SHA-256; all match their manifest, are 48-kHz/16-bit mono, have zero boundary samples and encoded peaks around −29.12 dBFS. This is quiet digital headroom, not a calibrated acoustic guarantee or perceptual approval. `AUDIO-ASSET-EVIDENCE.json` records the actual checks. No new sound samples are necessary for this refinement pass.

Recommended event policy:

- **Successful shift:** one optional stabilisation cue after confirmed supported appearance application; no success cue for partial failure.
- **Initiation/meter:** optional and rate-limited; prefer either a quiet initiation or completion cue in daily use, not mandatory audio at every stage or every digit.
- **Login readiness:** optional once per authenticated session; reuse the restrained stabilisation family rather than adding a fanfare.
- **Notifications:** retain the DE's notification/sound policy; do not add another cue for the same event.
- **Rejected command/error:** visual/accessible feedback first. Optional single quiet error cue under the same user preference; never a loud simulated alarm.
- **Mute/volume:** audio off by default; honour the existing default output and global mute, never call unmute/set-volume as a side effect of shifting, and do not treat absent output as a shift failure. No microphone capture is needed.

Use one bounded user-session cue dispatcher subscribed to explicit committed/applied events. It needs a sound preference/gain, a per-event enable map, deduplication/cancellation, stale-event suppression on login/resume and a way to report missing audio capabilities without blocking UI. The current `StateChanged`/`ApplyFinished` API can inform an experiment, but legacy CLI writes/partial applies need the staged transaction proposal before claiming coordinated audio/visual success. The stored motion key is not a sound policy.

PipeWire documents `pw-play` playback and media-role properties; WirePlumber documents read-only volume/mute inspection and separate mutation commands. These establish integration primitives, not permission to change the user's sound settings. Current upstream docs describe PipeWire 1.6/WirePlumber 0.5.19, while this host inventory lists PipeWire 1.4.2/WirePlumber 0.5.8, so use supported options from the actual guest. No playback tool was invoked here. [PipeWire playback manual](https://pipewire.pages.freedesktop.org/pipewire/page_man_pw-cat_1.html), [WirePlumber wpctl manual](https://pipewire.pages.freedesktop.org/wireplumber/man/wpctl.html).

## Required verification before claiming implementation

1. Package the mode-label-only change separately, then capture boot, shutdown and reboot in a fresh disposable overlay; verify status/password/question callbacks and fallback.
2. Prototype the assembly treatment in the review viewer; label it as a preview. Then port/test the theme in a separately versioned guest package/initramfs. Test fast/slow boot, display sizes, prompt interruption and static/reduced modes.
3. Preview an SDDM theme without changing the active greeter, then qualify actual login/auth-error/session/keyboard/accessibility states in the disposable VM. Preserve a known-good login/TTY path.
4. Add an output-only virtual sound device/backend only to a separate disposable test configuration using existing capabilities; request approval for new dependencies or broader deployment, and test a local synthetic PCM fixture through guest→SPICE/host output at user-selected volume. Do not infer silence is a product defect when the VM has no sound hardware configured.
5. Integrate the optional cue dispatcher only after the transaction/result contract is clear. Test muted output, no sink, unavailable player, repeated requests, failure, logout/resume and real-app continuity. An audio failure cannot undo a successful state change or prevent boot.

All image references are inspiration only. The supplied portal/HUD/terminal imagery was inspected but is not redistributed or copied into the new storyboard. Current artwork and existing functionality remain preserved.

## Final runtime supplement

The lead engineer tested the meter with a real GTK window and the patched service in the isolated fork. Fresh reboot restored Hitogashima `3.072100`, meter enabled and Reduced, with `applied=true`. A controlled temporary stop of `plasma-plasmashell.service` produced the actual transient wallpaper D-Bus error; after the shell restarted, the service retried and reached `applied=true` without a manual reapply or divergence-file change. `../evidence/live-startup-recovery.log` records retry scheduling and recovery. The 17 service regression tests also cover finite exhaustion, permanent/mixed failures and stale callbacks. These results do not qualify cinematic boot or sound.
