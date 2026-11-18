# Steins;OS V3 — native integration lab

V3 replaces selected review-only concepts with real components in **SteinsOS-V3-Integration**. It preserves the working standalone prototype, the frozen V2 review, the `SteinsOS-Test` libvirt domain and the known-good XFCE ISO. It is an experimental installed-system fork, not a newly qualified release ISO.

## Implemented

- Native everyday terminal around Debian's maintained QTermWidget6: real PTY, linked tabs/session rail, compact tiled mode, dynamic worldline/ANSI colours without restarting shells, search/zoom, clipboard and confirmation before closing running sessions. Konsole remains available.
- Native Plasma worldline instrument with actual shared-state digits, six-world selection, meter/motion controls and partial/disconnected/stale feedback. Existing widgets/launchers remain. Its Open Worldlines action uses a fixed GIO DesktopAppInfo launch through the session service.
- Plasma CLI, IBN and local fictional D-Mail use the same service for ordinary changes. D-Mail arithmetic and previous-state reporting occur inside the serialized service operation. Headless/XFCE and explicit no-apply/dry-run paths remain available. The real Thunderbird mail client is unchanged.
- Six original illustrated environments. The approved urban/rural/coastal PNGs are byte-preserved. Alpha, Lugunica and Mitakihara add original rainy-electronics, canal-twilight and observatory-night scenes. Their prompts/provenance are in `prototype/artwork-v3/`.
- Actual Plymouth Full/Reduced/static themes, normal boot/reboot wording and prompt priority; original current emblem retained, silent. Reduced is the final lab default. Nominal animation frame budgets never delay real boot readiness.
- Original restrained GRUB background, with stock readable menu/font/entries and retained rollback backups.
- Maintained Breeze login with public Steins artwork/clock/emblem presets. Its actual password controls remain upstream SDDM; the missing-theme fallback was corrected. No private worldline/home state is read before authentication.

## Launch the prepared native checkpoint

From `/home/developer/Documents/ChatGPT/Steins;OS`:

```sh
python3 prototype/integration/vm_lab.py start native-v3
python3 prototype/integration/vm_lab.py view
```

Close the viewer to disconnect. Use the normal guest shutdown or `python3 prototype/integration/vm_lab.py stop`, then check `status` until fully off. The standalone VM uses KVM, 6GiB/2vCPUs, UEFI, VirtIO disk/NAT and local SPICE. No host block device, shared folder, USB passthrough, clipboard bridge or microphone is exposed. It is separate from virt-manager's existing guest.

To discard only changes after the frozen native checkpoint, while every VM is off:

```sh
python3 prototype/integration/vm_lab.py reset native-v3
python3 prototype/integration/vm_lab.py start native-v3
```

Old runs remain retained. The original `baseline` checkpoint predates all V3 packages; resetting to it deliberately restores the older inherited desktop. `native-v3` preserves this tested milestone, including its own UEFI variables. Backing ancestors must remain available and unchanged; this local chain is not an independent portable backup. The helper verifies hashes/paths/ownership and the exact QEMU identity. `freeze NAME` captures the current cold run without overwriting earlier checkpoints; current-run freeze/reset has separate temporary-image tests.

## Replay and package boundaries

`dist/v3/BUILD-SET.json` pins the selected local DEBs by SHA-256. `python3 prototype/integration/deploy.py` installs that exact set into the running named V3 guest only; it refuses removals. Dependencies come from the guest's signed Debian repository metadata. It never installs on Parrot. Existing UI processes need a normal relogin or explicit guest-only service/shell reload to consume updated code.

The first-party terminal, panel, startup and greeter builders live in their matching `prototype/` folders. `prototype/build.py --output dist/v3/packages --version '0.1.0~prototype6' --artwork-dir prototype/artwork-v3` builds the updated service/assets. The base desktop package was built separately as `0.1.0-10~worldline2`; ordinary package/ISO exports and `packaging/VERSION` were left alone. New terminal runtime dependencies are ordinary unmodified Debian packages. QA additionally installed Zsh, Neovim and OpenSSH client in this fork; no SSH server is shipped.

Panel attachment and optional boot/greeter activation require explicit guest operations documented in their component READMEs. The source helpers retain backups and never automatically select a theme during package installation. The final frozen native checkpoint already has the qualified settings, so normal review does not require replaying them.

## Verification and remaining work

See `evidence/v3-integration/VALIDATION.md` for exact real runtime tests, helper/source checks, screenshot provenance and limitations. The native frontend passed real Bash/PTY, Unicode, resize/process continuity, clipboard, Neovim file save, interactive Zsh and synthetic local SSH/remote resize checks. A controlled wrong-password attempt and actual fixture-password login exercised the maintained greeter. The local SSH fixture was removed, including generated keys; no personal account was used.

One earlier mixed manual-VT/Plymouth test lost SDDM's primary session while detached Plasma/terminal processes remained. Its cause is not established; no kernel OOM or compositor crash was recorded. Clean-boot copy/paste and normal logout/password-login retests passed; the longer repeated-switch result is recorded in the ledger. Do not label the earlier occurrence fixed or claim release stability from this alpha.

The VM still uses software graphics and has no emulated sound card/custom cue dispatcher. Native compositor distortion, coordinated staged transitions, fractional scaling/IME/screen-reader coverage, hardware suspend/GPU tests and a separately rebuilt/install-tested Plasma ISO remain release work. Current free host storage is about13GiB: a fresh image build needs a deliberate disk budget and must preserve the known-good export. No additional animation or audio is presented as integrated merely because a design asset exists.
