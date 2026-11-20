# Everyday terminal

This note covers the terminal shipped in the installable XFCE image: `xfce4-terminal` with the user's Bash login shell. The `ibm5100` program and the V4 QTermWidget prototype (`prototype/surfaces-v4/terminal/`) are separate and unchanged. Because the prompt and `steins-info` are ordinary shell files, they also apply in any other terminal that starts a Bash login shell.

## Design

| Layer | Source | Follows the worldline |
| --- | --- | --- |
| Default profile: JetBrains Mono 11 at 1.1 line height, block cursor, 10,000 lines of scrollback, shell-set window title, no menubar or toolbar, login shell | `TERMINAL_PROFILE` in `steinslib.py` (fills absent xfconf properties) and the matching `/etc/skel/.config/xfce4/terminal/terminalrc` | Colours only |
| Frame: graphite tab strip, accent underline on the selected tab, slim dark scrollbar | `packaging/theme-overrides.css` (Steins-Lab theme) | Accent and surface via the user block below |
| Text margin, selected-tab accent, scrollbar surface | `gtk_css()` in `steinslib.py`, written to `~/.config/gtk-3.0/gtk.css` | Yes |
| Foreground, background, cursor and cursor text, selection, tab activity, 16 ANSI colours | `_write_terminal()` in `steinslib.py` (terminalrc and xfconf) | Yes |
| Prompt and greeting | `usr/share/steins/shell/prompt.bash`, loaded by `etc/profile.d/steins.sh` | Yes, through ANSI indices 3, 6 and 8 |
| `steins-info` | `usr/local/bin/steins-info` (packaged as `/usr/bin/steins-info`) | Yes, through ANSI indices |

The text margin must live in the user stylesheet: `xfce4-terminal` installs its own stylesheet for the terminal widget at a priority above themes, so a theme-level `vte-terminal` rule is ignored. Tab and scrollbar rules work from the theme and are scoped to `#xfce4-terminal-notebook`, so no other application changes.

## Prompt behaviour

- Shape: `user@host  path  on branch  took 12s  exit 2  ❯`. Root uses a red user name and `#`. Linux consoles and non-UTF-8 locales use `>`.
- On the first prompt it replaces only Debian's stock prompts (from `/etc/skel/.bashrc` or `/etc/bash.bashrc`). Any other `PS1` is kept. `STEINS_PROMPT=off` keeps Debian's prompt; `STEINS_PROMPT=on` overrides a custom one.
- It never edits `~/.bashrc` or `/etc/bash.bashrc`. Removing `steins-desktop` removes it.
- The Git branch is read from `.git/HEAD` without running `git` or forking. Linked worktrees are followed. Repository status (dirty or clean) is not shown, to keep large repositories fast.
- The prompt hook is the first element of an array `PROMPT_COMMAND` (Bash 5.1 and later). Debian's VTE integration (`/etc/profile.d/vte-2.91.sh`) appends to an array but would overwrite a string. The `PS0` timer is prepended because VTE's `PS0` ends in an `ESC \` terminator.
- Greeting: one line per interactive login shell, showing the saved divergence. `STEINS_GREETING=off` or `~/.hushlogin` silences it.

## Upgrades and existing users

The package version is 0.1.0-9. `/etc/profile.d/steins.sh`, `/etc/skel/...terminalrc` and `/etc/steins/theme-overrides.css` are conffiles. Unedited copies are replaced on upgrade; locally edited copies follow normal dpkg conffile handling. The theme regenerates through the existing `steins-branding` trigger.

`steins-worldline apply` runs at every login. It always writes the worldline colours. It also writes the profile defaults (font, login shell, no menubar, cursor, scrollback, title) for any property absent from the user's `xfce4-terminal` xfconf channel. xfce4-terminal stores only settings changed in Preferences, so anything a user chose stays theirs. If the channel cannot be read, no defaults are written.

This is required, not cosmetic. The first session's apply creates the xfconf channel before the terminal first runs, so xfce4-terminal never migrates `/etc/skel`'s `terminalrc`. A real live-ISO session showed this on `main`: menubar visible, no login shell and therefore no profile.d greeting. The skeleton file remains as a fallback for sessions without the apply step. As a result, existing users also receive the profile at their next login, minus anything they had customised.

The `steins-info` side-by-side layout needs 88 columns. Narrower terminals get the coloured list without the emblem, and auto-wrap is paused while the emblem prints.

## Verification

- `tests/check_terminal.py` (run by `tests/check_source.py`) drives a real interactive Bash on a PTY. It covers prompt adoption and opt-outs, greeting rules, exit status, duration, Git branch, detached HEAD and worktrees, coexistence with VTE, an existing `PROMPT_COMMAND` and silence in non-interactive shells. It also checks the default profile against the default worldline, the scoping of the theme rules, the per-world CSS and the `steins-info` output modes.
- `tests/check_worldlines.py` checks that the new terminal keys are written with the correct xfconf types.
- The package, install and upgrade checks and the ISO results for this change are recorded in the pull request.
