# Steins;OS Terminal — native V3 experiment

This is a real Qt6 application around **unmodified QTermWidget 2.1**, the terminal engine maintained by LXQt. Terminal emulation, PTYs, Unicode, bracketed paste, selection, scrollback and text search remain upstream infrastructure. This package does not replace Konsole, the existing `steins-terminal` launcher, user shell files or default-terminal settings.

Implemented original chrome: shared session rail/tabs, compact rail under 900 logical pixels, a worldline instrument button, readable dark surfaces and an unobtrusive status strip. Native window-manager decorations remain, preserving ordinary Wayland move/resize/maximise and accessibility behaviour. Chrome is static; no compositor effect or sound is claimed.

The frontend subscribes to `org.steinsos.Worldline1.StateChanged` and reads `GetState` asynchronously. Existing sessions receive the current supported palette and sixteen ANSI colours without restarting the shell. Service loss leaves the PTY usable. Colour-scheme files are content-addressed in this application's cache because QTermWidget caches loaded schemes by path; Konsole profiles and the authoritative divergence/preferences files are never edited.

## Launch

Desktop ID: `steins-terminal-v3`. Executable: `/usr/bin/steins-terminal-v3`.

```sh
steins-terminal-v3
steins-terminal-v3 --workdir "$HOME/Projects"
steins-terminal-v3 -- /bin/bash --noprofile --norc -i
steins-terminal-v3 -e /bin/bash -c 'printf "hello\n"; exec /bin/bash'
```

Arguments are passed directly to the selected executable; the application does not concatenate user arguments into shell commands. `SHELL` is honoured when executable, otherwise `/bin/bash` is used. Without a command, an interactive login shell runs on a real PTY. A normal shell exit closes its session. Closing a running session/window requires a confirmation whose default is Cancel. This conservative check asks even for an idle shell; it does not pretend to detect every unsaved application state.

Shortcuts: Ctrl+Shift+T new, Ctrl+Shift+W close, Ctrl+Shift+C/V copy/paste, Ctrl+Shift+F scrollback search, Ctrl+PgUp/PgDown or Alt+1…9 session selection, Ctrl+Plus/Minus/0 text size and Ctrl+Shift+B session rail. Upstream multiline-paste confirmation covers engine paste paths. Bracketed paste stays enabled. Konsole is available from Session → Open Konsole fallback.

## Isolated build

`python3 prototype/terminal/build.py` creates a private temporary container from the existing `steins-os-builder:trixie` image, installs build dependencies **inside that container**, builds/tests/packages, then removes only its own container. No host package or configuration is installed. Outputs stay under `dist/v3/terminal/`; ordinary ISO/package exports are untouched.

Dependencies verified against official Debian13 APT metadata and the installed development headers:

- `libqtermwidget-dev` / `libqtermwidget6-2` **2.1.0-1** (the development package has no “6” in its name).
- `qt6-base-dev` **6.8.2+dfsg-9+deb13u2**, CMake **3.31.6-2**, GCC14.
- `libutf8proc-dev` is needed because the exported QTermWidget CMake target references its development link; it is a build dependency.
- Runtime dependencies are derived from the built executable by `dpkg-shlibdeps`. Wayland uses the guest's `qt6-wayland` platform plugin. There is no new display server or GPU dependency.

The package includes this frontend's full source/build instructions and license texts. Frontend source is MIT; the linked executable is distributed under GPL-2-or-later, reflecting QTermWidget's mixed GPL-2+ / LGPL-2+ files in Debian's copyright record. The engine is an unmodified Debian dependency, not vendored code. Primary evidence: Debian's installed `/usr/include/qtermwidget6/qtermwidget.h`, `/usr/share/doc/libqtermwidget6-2/copyright` and official APT package metadata; upstream source is <https://github.com/lxqt/qtermwidget>.

## Verification and limits

The QtTest executable compiles the same production window/session class. Its six substantive tests launch actual Bash PTYs and verify TTY stdin/stdout, Unicode output, changing terminal geometry with the same PID, real terminal-background repaint after a worldline update, linked rail/tab ordering, compact rail, default-Cancel close safety and normal session exit. Timer-driven regressions verify that a shell exiting while its close confirmation is open cannot cause the next shell to be closed, and that a window-close confirmation cannot approve a newly created shell. Missing/invalid optional ANSI palettes fall back rather than retaining the previous world; hidden session rails become actually invisible so their controls leave keyboard focus traversal. Test init/cleanup produce two additional QtTest pass lines. Offscreen tests do not establish real Wayland focus, IME, fractional scaling, complete SSH/editor compatibility or screen-reader behaviour. The parent V3 VM ledger records real display/clipboard/TUI checks separately.

Known current limits: no split panes, session persistence/recovery after crash, remote profile manager, full accessibility qualification or full font-settings UI. Existing Konsole remains the maintained fallback for unsupported workflows. Native terminal applications can intentionally change their own colours; this frontend does not reset their process/application state to force a worldline palette.

## Prototype 2 corrections

Close confirmations bind to guarded terminal identities, never a tab index retained across a nested event loop. After confirmation, the target is re-resolved and ignored if already removed. Session completion does not recursively close the window while a confirmation is active. Whole-window confirmation checks for any newly added running shell and asks for a fresh close rather than terminating a session the earlier prompt did not cover. These protections were exercised with real shell exits during modal dispatch.

## Prototype 3 chrome qualification

The real Wayland capture exposed an unstyled bright engine scrollbar and a desktop-style-dependent red tab close box. Prototype3 explicitly styles the existing vertical QScrollBar with a dark 16-pixel track, a 32-pixel minimum handle and hover/focus accents. Scrolling remains upstream wheel/drag/page-key behaviour. Neutral 24-pixel close toolbuttons have accessible names/tooltips and resolve their guarded session identity at click time, then use the same modal close protections. Native window controls and the PTY engine are unchanged. The timer-driven close-race regression now activates this actual toolbutton path.
