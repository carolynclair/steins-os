# V4 worldline adapter

This is a separate source copy of the qualified V3 adapter, built as the next
`steins-plasma-prototype` package only for the disposable V4 guest. V3 sources,
packages, checkpoints and the existing XFCE ISO are retained.

`v4style.py` reads the original identity package's shared tokens. The service,
generated Qt colour schemes, supported Breeze decorations, GTK selection and
Konsole profile backgrounds share stable graphite colours. Only the restrained
world accent changes. Artwork, divergence math, pack metadata and ANSI semantic
colours retain their original data. Invalid or unavailable tokens have a readable
neutral fallback. No pack registry is mutated.

The existing session bus, single divergence file, serialized mutation methods,
bounded startup retries and explicit partial-failure reporting remain. The
Worldlines action launches the fixed V4 desktop entry, with the original
navigator as a package-level fallback. The familiar old launcher also delegates
to V4 when it is installed. No account, mail profile or host settings are read.

Build with `python3 prototype/worldline-v4/build.py`. Tests run in temporary
homes/private session buses:

```sh
dbus-run-session -- /usr/bin/python3 prototype/worldline-v4/tests/test_style.py
dbus-run-session -- /usr/bin/python3 prototype/worldline-v4/tests/test_service.py
```

Install the complete pinned set from `dist/v4/BUILD-SET.json` in the guarded
guest, rather than selecting unrelated development DEBs. A normal guest relogin
or reboot activates updated application/service code. This package does not
select a panel, login or boot theme during installation.

Generated Qt scheme IDs include the effective palette hash. A token update therefore bypasses KDE’s same-scheme short circuit and refreshes title-bar/selection colours on the first login. Human-readable appearance names remain unchanged.
