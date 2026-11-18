# Worldline Instrument — real Plasma 6 applet

This is a working-source Plasma applet, not an image board. Its original compact instrument displays the **saved service state**, with separate pending/partial/disconnected wording. It never invents successful appearance completion or previews an unconfirmed selection. The panel stays static for every motion mode; the menu controls the existing expanded meter's motion preference through the shared service.

The applet imports the existing `org.kde.plasma.workspace.dbus` module supplied by Plasma Workspace. Installed upstream `dbusplugin.qmltypes` on Plasma 6.3 exposes `SessionBus.asyncCall()`, typed string constructors, `DBusPendingReply` and `DBusServiceWatcher`; upstream taskmanager uses that watcher. No shell command engine, subprocess polling, custom native plugin, host installation or new terminal/state service is needed. The module is a Plasma integration API: requalify against each shipped Plasma major/version.

GetState is queried asynchronously every two seconds, with at most one state/mutation request in flight. Worldline names are fetched at startup/menu opening. The bounded timer does not overlap calls or spin on failures. The service watcher immediately clears digits when the name disappears and reconnects on return; generation checks ignore stale completions. A refresh delayed beyond eight seconds is visibly marked stale. Existing service D-Bus timeout semantics bound a hung call. There is no second saved divergence or direct write to user state. Mutations call SetDivergence, SetPreference or ApplyCurrent only.

## Build and deploy only to the disposable fork

```sh
python3 prototype/panel/build.py
```

Output: `dist/v3/panel/steins-worldline-panel_0.1.0~prototype2_all.deb`. It contains only the applet and documentation. It has no maintainer scripts and never changes a panel automatically. Install through the normal guest package mechanism, then add **Worldline Instrument** from Plasma's widget browser. The existing Konsole/prototype continue to work independently.

For the explicitly opted-in disposable lab profile only, `attach.js` places the instrument after an existing launcher on a bottom panel. It never removes a widget or replaces the panel. A new instrument uses supported insertion coordinates. For an already-added instrument, it preserves the other widgets' saved relative order and changes only the instrument's position in `General/AppletOrder`. It refuses missing/unready launcher geometry, duplicate instruments or missing saved order rather than guessing. After transferring that script into the guest:

```sh
qdbus6 org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "$(cat /tmp/v3-integration/attach.js)"
```

The script returns JSON describing whether it inserted a new instrument or saved a reordered list. If `restart_required` is true, **normally restart plasmashell inside the disposable guest** and verify the live panel; running the script alone does not move an existing applet on Plasma 6.3. Application windows remain owned by KWin, but the panel temporarily disappears during that shell restart. Use the prepared guest-only controls, never a host `systemctl --user` command. Rerunning after the saved order is correct leaves the configuration unchanged.

Do not run the command against Gary's host session. This source's author performs no VM or host deployment; runtime evidence belongs to the lead engineer's isolated fork ledger. Removal uses Plasma's normal widget removal; package removal leaves existing panels intact.

The original `instrument.index = 1` attempt was ineffective: exact [Plasma/6.3 source](https://raw.githubusercontent.com/KDE/plasma-workspace/Plasma/6.3/shell/scripting/widget.cpp) leaves the index getter/setter unimplemented. [KDE bug 523675](https://bugs.kde.org/show_bug.cgi?id=523675) documents that limitation and the insertion-coordinate workaround. Installed Plasma 6.3 `org.kde.panel/contents/ui/LayoutManager.js` restores `General/AppletOrder` only when its component loads; the newer live reorder API is not assumed available.

## Interaction and limits

- Click/Space/Enter opens a popup with the six shared worlds, the expanded meter preference, Full/Reduced/Off and explicit retry on a partial apply.
- Current digits and label use the active world's accent; the low-contrast glass housing stays legible. Focus border, accessible names/descriptions and full-value tooltips are present. Buttons remain standard keyboard-operable Qt Controls.
- Service loss displays unavailable digits, disables world selection/preferences and keeps Refresh available. A partial appearance operation shows the saved value plus **Appearance incomplete**, not false success.
- Pending poll is intentionally silent in normal UI; mutations show Applying. The existing service still performs sequential appearance steps. This applet does not create a compositor transition or make legacy writers transactional.
- The popup's Open Worldlines action calls the session service's fixed `OpenNavigator` method, which uses GIO's DesktopAppInfo launcher. Real testing exposed that an `applications:` URL opened a KIO folder error instead of the application; prototype2 corrects that path. Horizontal/vertical sizing, focus and scaling remain separately qualified.

## Verification

`evidence/loader.log` records an initial isolated private-bus/offscreen Plasma loader check using temporary HOME/XDG locations. It does not touch the host Plasma layout or session bus. This is loader/API evidence, not a real VM or usability pass. The parent supplies real guest screenshots and interaction tests after deployment.

`/usr/bin/python3 prototype/panel/test_loader.py` also loads a throwaway copy of the **actual production applet** against a private synthetic D-Bus service, with temporary test timers driving its real methods. The checks cover typed meter/motion writes, world selection, explicit partial appearance state, ApplyCurrent recovery, immediate unavailable digits on service loss and automatic reconnection. `evidence/private-bus-result.json` records source hash, observations and backend receipts. Normal offscreen/no-window-manager warnings in the log are not passed off as a production display test. No personal service or VM is contacted.
