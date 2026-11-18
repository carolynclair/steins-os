# Steins Lab V4 panel milestone

This opt-in native Plasma 6.3+ package coexists with the V3 applet. Installation does not modify a user's desktop. It supplies:

- A 46px anchored graphite panel with 94% static opacity, a solid fallback, and no blur dependency. Calendar, tray and menu popup backgrounds use original fully opaque raised surfaces in every transparency variant, preventing underlying text or wallpaper from competing with popup content.
- Original nine-slice native task and list frames; Breeze supplies the remaining mature widgets. Native launcher, tasks, tray, clock, context menus and keyboard interactions are retained.
- A quiet 176×34 divergence instrument with one clickable enclosure, restrained per-world digits, focus outline, readable status, native controls and an accessible name. Six atmospheres share one layout. Shared-service calls include OpenNavigator; partial, delayed and disconnected state remain explicit.
- Generated QML/theme assets from ../identity-v4/TOKENS.json. Icons come from the separate steins-identity-v4 package. The existing emblem is preserved.

Build without installation: `python3 prototype/panel-v4/build.py`.

Only inside the disposable V4 test guest, as its desktop user:

```
python3 /usr/share/steins-v4/panel/apply.py --replace-v3
```

The helper refuses outside a QEMU/KVM VM. This explicitly backs up applet layout, theme and icon configuration to the user's state directory, selects SteinsLab, sets the existing bottom panel to 46px/non-floating, uses the familiar Steins launcher, keeps native tasks in one row with standard iconSpacing=1, and inserts V4 immediately after the launcher. `--replace-v3` removes only the known V3 meter after adding V4 and migrates the project’s own pinned Navigator/Terminal aliases. `steins-navigator`, `steins-worldlines` and `steins-worldline` desktop IDs resolve to `steins-navigator-v4.desktop`; `steins-terminal.desktop` resolves to `steins-terminal-v3.desktop`. Duplicates of those resulting project IDs collapse at their first position. Native Qt KConfig `V4Sequence` QString lists are copied by bounded, validated indexed reads; malformed sequences are refused before any panel mutation. Unrelated pins, their order and deliberate duplicates remain intact. Without `--replace-v3`, every pinned launcher and the V3 meter are preserved. It never removes other applets. It does not install software, stop a shell, alter disks, or change login configuration.

Plasma 6.3 Widget.index is a nonfunctional stub. The helper uses supported insertion coordinates and saves General/AppletOrder; verify order after a normal guest sign-out/in or a deliberate guest-only shell restart. Run it again after the shell settles if a newly created widget has not yet been persisted. `--panel-id ID` selects a particular existing bottom panel; `--print-script` is read-only.

Rollback: end that user's Plasma session first, then run `python3 /usr/share/steins-v4/panel/restore.py BACKUP_DIRECTORY`; log in again. The restore helper refuses while plasmashell runs. The original V3 package and frozen VM remain available.

Validation: `python3 prototype/panel-v4/test_loader.py` loads the actual applet on an offscreen, software-rendered Plasma window with a private fixture D-Bus and temporary HOME/XDG directories. It verifies typed calls, partial/reapply status, navigator launch, service loss/reconnect and explicit delayed-state feedback. The same real Qt engine exercises migration ordering, idempotence, safe refusal, and preservation of third-party applets/task launchers. The private bus omits host service activation directories to keep optional KDE/portal daemons isolated. `test_theme.py` validates native frame contracts, opacity fallbacks, token consistency and text/focus contrast. `test_raster.py` renders actual KSvg frames at non-tile-multiple sizes, checks edge alpha for gaps, and saves composites over bold white underlay text. Borders use filled bands inside exact slice bounds and stretch-border hints; no stroke extends a slice or creates repeated seams. These tests do not prove the final guest panel, system tray, keyboard navigation, or no-compositor appearance; capture and inspect those in the isolated V4 guest before calling this a daily-use release.

All new code and SVG geometry are original MIT assets. No upstream SVG geometry or licensed screenshots are embedded. Breeze is inherited from the installed system; its assets are not copied into this package.
