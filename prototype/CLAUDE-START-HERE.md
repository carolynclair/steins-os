# Claude: resume from the running prototype

**Superseded for creative direction:** Gary's subsequent complete VM review and the new lead brief are in `docs/reviews/2026-11-01-complete-creative-direction.txt` and `docs/CLAUDE-CREATIVE-DIRECTION-2026-11-01.md`. Read those first. The following is historical prototype context, not the final visual specification.

Gary authorised Codex to start the design prototype on 2026-11-01 while your tokens were unavailable. Read `prototype/README.md` and `evidence/plasma-prototype/VALIDATION.md` first. The earlier architecture assessment is historical planning; this pass implements the first prototype, not the final desktop migration.

**Protect:** normal ISO `dist/steins-os-0.1-amd64.iso`, existing libvirt `SteinsOS-Test`, host Parrot KDE, and the backing QA disk. Keep experiments under `prototype/` / `dist/prototype/`. Do not blindly unzip over dirty source.

**Look at actual captures:** `navigator-coastal.png`, `meter-wayland.png`, `dmail-received.png`, `dmail-compose.png`, and the final desktop capture in `evidence/plasma-prototype/`. These are QEMU captures of real Plasma/GTK/Thunderbird programs, not mockups. Original wallpaper PNGs are source assets, not desktop screenshots.

**Working interface:** session bus `org.steinsos.Worldline1`, path `/org/steinsos/Worldline`, same interface. Methods `GetState() -> JSON`, `ListWorldlines() -> JSON`, `SetDivergence(string) -> JSON`, `SetPreference(key, JSON-value) -> JSON`, `ApplyCurrent() -> JSON`. Signals `StateChanged(JSON)`, `ApplyFinished(JSON)`. State includes interface version, divergence, pack ID/name/palette/preferences/revision; apply responses add `applied` and `errors`. Completion can explicitly report partial failure. See `prototype/worldline/lib/worldline_service.py` and tests.

**Keep:** original tube design, IBN 5100, numeric state compatibility, readable addresses/security controls in real mail. No mandatory monitoring and no text/control strips baked into scenic art. Mail is separate from the local `dmail` simulation. No franchise screenshots/logos/characters or artificial mail/OS success states.

**Your useful next pass:** review spacing/typography/focus at actual screen sizes; propose a cohesive original launcher/panel/navigation design; improve D-Mail theme colours within supported API limits; review original scene compositions and design the other three environments. Prefer edits to the QML/theme/assets contract above. Discuss core state/package changes before editing the same engine files concurrently with Codex.

**Known unfinished surfaces:** stock Plasma launcher/decorations/settings; lab-only SDDM setup and stock lock screen; some default Thunderbird colours and its unchanged layout; static (not worldline-driven) mail theme; three older labelled wallpapers; no KWin transition; no large-text/multi-resolution qualification. Do not describe these as finished.

Record the exact files changed, screenshot origin, test commands and unverified items in a new change note. Send a small source/assets patch ZIP rather than VM disks or build caches.
