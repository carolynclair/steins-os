# Steins;OS V4 — panel and icon milestone

V4 applies Burrito's taskbar review to a separate installed-system VM fork.
It is an experimental native Plasma desktop, not a replacement release ISO.
The original ISO, V3 package set and frozen `native-v3` checkpoint remain intact.

The native bottom panel uses a 46px profile, a 176×34px clickable worldline
instrument, restrained graphite translucency with an opaque fallback, normal
Plasma application tasks/tray and a familiar Applications launcher. SteinsLab
adds original icons with consistent 24px geometry and recognizable folder,
terminal and mail silhouettes. Other applications inherit maintained upstream
icons. The current original Steins;OS emblem remains unchanged.

Panel, terminal, Worldlines cards, GTK selection and supported Breeze window
decoration colours share the same token source. Six quiet atmosphere accents
change the meter and small focus/active details; the layout and icon silhouettes
stay stable. The existing original wallpapers are reused unchanged. No new
application, Easter egg, compositor effect or audio dependency is introduced.

## Launch

From `/home/developer/Documents/ChatGPT/Steins;OS`, after other VMs are shut down:

```sh
python3 prototype/integration-v4/vm_lab.py start native-v4
python3 prototype/integration-v4/vm_lab.py view
```

Use the guest's normal shutdown, or `python3 prototype/integration-v4/vm_lab.py
stop`, and check `status` until off. Closing the viewer disconnects it. To create
a fresh run from the frozen milestone while all VMs are off:

```sh
python3 prototype/integration-v4/vm_lab.py reset native-v4
python3 prototype/integration-v4/vm_lab.py start native-v4
```

Old runs are retained. This local backing chain requires the existing immutable
V4 seed, V3 checkpoints and QA base; it is not a portable independent VM image.
Do not delete or rename those ancestors. The helper pins and verifies their
hashes, ownership and paths. `seed v3-base` was a one-time cold capture of the
verified V3 native milestone; it never overwrites an existing checkpoint.

The VM uses KVM, 6GiB RAM, two vCPUs, UEFI, a dynamic VirtIO virtual disk, NAT
and private Unix SPICE/QMP/serial sockets. There is no physical disk passthrough,
host folder share, USB device passthrough or clipboard bridge. No host packages
or Plasma settings are changed by the integration scripts.

## Replay

`dist/v4/BUILD-SET.json` pins first-party DEBs by SHA-256. The guarded
`deploy.py` installs only those packages in the named running guest, with
`apt-get --no-remove`. Explicit panel and window presets keep per-user backups;
their rollback commands are described in each component README. They are never
run on the host. The frozen checkpoint already contains the applied settings.

See `evidence/v4-design/VALIDATION.md` for actual runtime checks, screenshot
provenance and remaining limits. The V3 unresolved mixed VT/Plymouth session
loss remains tracked in its validation ledger. Software graphics in this lab
do not qualify GPU performance, hardware suspend, fractional scaling or release
stability. A separately rebuilt and install-tested Plasma ISO remains future
distribution work.

The explicit `configure_guest.py` lab step backs up the session setting and
selects an empty login, retaining KDE's old session-restore state. It excludes
X11 Light Locker only in KDE, where the maintained Plasma locker is used and
tested. Other desktops retain their original locker entry.

The public disposable account is `observer`, password `SteinerTest42`. This is
a test fixture, not a host credential or release account policy. Use Meta for
Applications and the panel instrument for worldlines. The frozen checkpoint
already includes these explicit guest profile settings.
