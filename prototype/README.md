# Project Worldline — running Plasma prototype

For the newer native terminal/panel/boot integration in a separate resettable lab, see [V3 native integration](integration/README.md). The original VM described below remains preserved.

Started 2026-11-01 at Gary's request while Claude is unavailable. This is a **working disposable desktop prototype**, not a replacement release ISO. Debian/live-build/Calamares remain the distribution foundation. The known-good XFCE ISO and `SteinsOS-Test` libvirt VM are preserved.

## What exists

- Plasma 6.3.6 **Wayland**, Konsole, Dolphin and Thunderbird 153.6.0 ESR installed in a separate QCOW2 overlay of our earlier installed-system QA disk.
- Per-user `org.steinsos.Worldline1` D-Bus service. The existing `~/.local/state/steins/divergence` remains authoritative; there is no second saved divergence. Preferences live beside it in `preferences.json`.
- Native Qt Quick navigator with six selectable worlds, keyboard focus/navigation, explicit retry/error reporting and an optional original tube meter. Monitoring stays off. The existing meter opens IBN 5100 in Konsole when the prototype backend is enabled.
- Three original environmental wallpapers: urban summer (`steins-gate`), rural valley (`hinamizawa`) and island harbour (`hitogashima`). No product text or controls baked into these scenes. The other three worlds deliberately retain their previous artwork for now.
- Qt colour schemes, managed GTK selection CSS and worldline-specific Konsole profiles generated from the existing pack registry. Existing Konsole profiles/defaults are preserved. Newly opened Laboratory Terminal windows use the current worldline; recolouring existing terminal windows is not implemented.
- A separate D-Mail launcher using upstream Thunderbird and an original optional **static theme XPI**. No message/account permissions, privileged theme experiments, userChrome hacks, mail engine or credential store. Upstream application identity and security controls remain visible. This is a supported-theme prototype, not a complete custom inbox layout.
- An isolated localhost-only synthetic mail fixture using **Dovecot IMAP + aiosmtpd SMTP**. Thunderbird sent and received a message through it, with two attachment copies verified by SHA-256. No personal mail account was connected. Real mail sending did not change divergence. The old terminal `dmail` remains local.

## Launch the saved VM

From this repository:

```sh
python3 prototype/vm.py start
python3 prototype/vm.py view
```

Close the viewer to disconnect. Request a normal guest shutdown with:

```sh
python3 prototype/vm.py stop
python3 prototype/vm.py status
```

The launcher uses Gary's existing KVM membership through `sg kvm`; no root command, package installation or libvirt definition is required. It refuses to start alongside a running libvirt guest and checks RAM/free space. The SPICE socket is local, clipboard/file transfer are disabled, and no host disk/device or shared folder is exposed. This VM is **not** the `SteinsOS-Test` entry in virt-manager.

Storage: `evidence/plasma-prototype/system.qcow2`, with read-only backing `evidence/vm/packaged-uefi.qcow2` and its own `OVMF_VARS.fd`. **Do not move, delete or boot that backing disk writable while this overlay is in use.** No RAM snapshot was taken. The original backing disk is a recovery point; the prototype overlay contains these experiments.

The disposable QA account is `observer` with test password `SteinerTest42`. This public fixture password is not Gary's host password. SDDM autologin and disabled idle locking are **lab-only settings**, not production security defaults.

Launch `Worldlines`, `Laboratory Terminal`, `D-Mail` and Dolphin from the guest panel/application menu. The normal D-Mail launcher uses Thunderbird's normal profile/account setup and leaves existing profiles alone. It does not silently activate a theme or import test accounts.

For the populated **synthetic mail demonstration** inside the guest:

```sh
sudo systemctl start dovecot
python3 /tmp/mail_fixture.py --serve > /tmp/mail-smtp.log 2>&1 &
thunderbird --no-remote --profile "$HOME/.local/share/steins-mail-fixture/thunderbird"
```

Only start one fixture SMTP process. If prompted, its IMAP username is `observer@lab.invalid`, password `fixture-only`. IMAP listens on `127.0.0.1:1143`, SMTP on `127.0.0.1:1025`; SMTP accepts only the two synthetic `.invalid` recipients and never relays externally. Fixture packages/configuration/profile are **not shipped in the prototype Debian package**. `/tmp/mail_fixture.py` is a convenience copy; the maintained source is `prototype/mail_fixture.py`. Stop test services after using them.

## Build and source boundaries

```sh
docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/work" -w /work \
  steins-os-builder:trixie python3 build-tools/build_packages.py \
  --output dist/prototype/packages --version '0.1.0-9~prototype1'
python3 prototype/build.py
```

Outputs are under `dist/prototype/`. The reference `dist/packages/`, ISO export, packaging version and ISO checksum index are unchanged. Do not run the ordinary ISO export script for an experimental build: it currently replaces the normal export filename.

The experimental package intentionally coexists with XFCE for comparison. It still depends on the original desktop package; this is **not** the final package split/migration. The only current runtime changes to the old source are an explicit `STEINS_DESKTOP_BACKEND=plasma` adapter hook and the corresponding meter terminal entry point. Without that opt-in, the reference XFCE path is unchanged.

`steins-prototype-session` only replaces a panel layout if that specific user has explicitly opted in through `~/.config/steins-prototype/allow-layout`. Gary's host has neither the package nor that marker. The current panel/launcher/window decorations are configured upstream Plasma components; a bespoke shell/launcher is future work.

## Tests and evidence

```sh
python3 tests/check_source.py
python3 tests/check_worldlines.py
GIO_USE_VFS=local dbus-run-session -- /usr/bin/python3 prototype/worldline/tests/test_service.py
```

`prototype/runtime_check.py` runs **inside the prepared guest only**, and checks actual Plasma state and the session API. See `evidence/plasma-prototype/VALIDATION.md` for results, screenshots, errors and limitations. QMP/serial helpers are guarded to this standalone experiment; they do not operate on the review VM or host desktop.

## Next engineering work

1. Qualify proper package boundaries, session defaults/login integration and migration of existing user state. A later rebuilt ISO must pass installation/update tests again.
2. Replace the stock launcher/shell interactions with the agreed original design. Add a discoverable keyboard shortcut to the navigator and settings integration.
3. Complete six environments, typography/accessibility/scaling and all Qt/GTK surfaces. Native compositor transitions and motion controls have not shipped. Horror anomalies remain off/unimplemented.
4. Decide how much of the real mail UI can meet the intended design through supported APIs. The static theme deliberately leaves some native colours/layouts; worldline-driven mail appearance and provider OAuth/update tests are outstanding.
5. Test 1366×768/1920×1080, large text, multi-monitor, suspend and hardware graphics. Software rendering in this 2-vCPU VM is not a compositor performance benchmark.

## Assets and licenses

New code: MIT, matching the repository. Original prototype wallpapers and D-Mail icon: CC-BY-4.0, attribution **Steins;OS contributors**. Wallpaper provenance/hashes are in `worldline/share/wallpapers/PROVENANCE.json`; they were generated for this project without reference screenshots or third-party input assets. Native scene size is 1672×941; higher-resolution production exports remain to be qualified. Upstream desktop/client/fonts/icons retain their licenses.
