# Worldline applications — proposed interaction and implementation contract

Status: **creative proposal, not an implemented desktop or tested terminal frontend**. This document complements the shared tokens and the root design boards. Dimensions below are logical pixels at 100% scale, not physical display pixels. The existing Plasma/GTK/Thunderbird runtime remains the functional reference. All new layouts, shortcuts and effects require the qualification gates below.

## One application language

Use the same precise, quiet chrome for ordinary applications: a **42px shared titlebar** (40px content plus 2px border allowance), a narrow accent marker identifying the active window, inset line icons, graphite surfaces and warm high-contrast text. Keep the window title aligned to the left; keep minimise/maximise/close in the familiar upper-right order. The brand should be carried by geometry, typography, the instrument-like worldline chip and consistent controls rather than repeated product names. No fake rivets, scanlines over text, tiled circuitry, large logos or additional decorative status rows.

Window decorations may share the design while native application toolbars remain application-specific. A board is not evidence that every third-party app exposes these exact header surfaces. When a supported integration cannot reproduce a control, retain the application's usable native control and use the nearest shared palette/spacing treatment.

## Flagship everyday terminal

Working product label: **Terminal**. Do not put an engineering component name into the normal UI. The proposed frontend owns tabs, panels, commands, search and worldline header presentation; a maintained terminal component owns PTY interaction, terminal parsing/rendering and ordinary application compatibility.

### Main composition at 850×540

| Region | Rectangle | Contents and behaviour |
|---|---|---|
| Shared titlebar | x0 y0 w850 h42 | Terminal icon/title at x16; compact divergence readout near the right; reserve the final 132px for window-control hit areas |
| Worldline readout/chip | x544 y8 w166 h26 | Current value `1.048596`, right aligned before the control region; current worldline tooltip; opens the same navigator as the panel meter. The board uses a quiet numeric readout, with full tube rendering reserved for panel/expanded states |
| Session strip | x1 y43 w848 h38 | Two named tabs, e.g. `~/Projects` and `SSH · lab`; 2px selected underline, small close target inside selected tab, plus action at the end; tab widths 120–220px |
| Terminal plane | x1 y81 w848 h434 | Flat opaque terminal background; first text baseline x22 y114. No blur/glitch layer over terminal glyphs; unobtrusive edge scrollbar when needed |
| Context footer | x0 y515 w850 h25 | Optional working-directory/process context or search-result count. The board shows `bash / UTF-8` and `Local session`; do not display invented process state or success indicators |

The header chip is part of the application chrome, not text inserted into the PTY. It consumes the authoritative service snapshot. Its digits do not scroll the terminal, alter shell variables, change a remote host or inject escape sequences into running applications. Clicking it previews destinations; it does not immediately shift to an arbitrary value.

Typography: use the shared UI family for chrome and a real fixed-width licensed family for the terminal plane (DejaVu Sans Mono is the available baseline). Start with a 13–14px equivalent at ordinary text size, preserving a comfortable cell grid and a minimum 1.35 line-height target where the selected engine supports it. User zoom/font preferences take precedence. Measure actual cell size and screen dimensions with the component instead of assuming a character count from a drawing. No proportional terminal font or fake monospace rendering.

The default prompt should remain short and useful: username only when useful, working directory, optional Git branch when available and a conventional `$`/`#` prompt. A restrained accent separator can provide identity. Do not show a huge greeting, permanent divergence duplicates in every prompt, fabricated health statuses or a Git label when no repository exists. Existing shell startup files and chosen shells remain user-owned; prompt integration is optional and backed up/migrated deliberately.

### Terminal states and controls

- **Normal:** text, selected tab and worldline chip use the shared hierarchy. The terminal plane remains legible with a plain desktop background.
- **Inactive:** decrease border/header prominence; preserve content contrast and leave critical output readable. Never dim the PTY to imply it is paused.
- **Find:** an in-window search row appears immediately below tabs and returns focus to the terminal on Escape. Include query field, match count, previous/next and explicit no-match text. Find never executes text.
- **Split:** a menu action plus configurable shortcut creates another maintained terminal widget within the same window. Keep a 1px divider, 2px focused-pane marker and a plain session title. A split is not another desktop window.
- **Busy process close:** when supported process information indicates a running child, name the actual session/process and ask before closing that session. Do not infer completion from an animated dot. A worldline shift never closes or restarts shells.
- **Worldline pending:** the chip names the requested destination while its current-value accessible label remains truthful. Terminal content/input continues. On commit update chrome; preserve the user's terminal content and ANSI contrast. Keep content palettes stable initially rather than recolouring a full-screen editor unexpectedly.
- **Service unavailable:** retain the last confirmed chip as muted `Unavailable` context, with no fake current/healthy state. Normal terminal work must remain available; retry/reconnect should not spawn a second shell.

Proposed keyboard defaults, subject to collision and accessibility testing: Ctrl+Shift+T new tab; Ctrl+Shift+W close current session; Ctrl+Shift+F find; Ctrl+Shift+C/V copy/paste; Ctrl+PageUp/Down change tabs; Ctrl++/−/0 font zoom; a menu action for splitting. Forward ordinary terminal Ctrl+C, Ctrl+D, Ctrl+Z and Ctrl+L to the PTY. Do not introduce a global shortcut that overrides these shell controls. All GUI shortcuts must be discoverable and configurable.

### Maintained engine feasibility — researched, not compiled here

| Candidate | Primary-source evidence | Assessment for this proposal |
|---|---|---|
| **QTermWidget + original Qt Widgets frontend** | Upstream describes an embeddable Qt 6 terminal widget and documents shell/font/scheme/search APIs. Debian trixie supplies runtime `libqtermwidget6-2` and development `libqtermwidget-dev`, both 2.1.0-1 | Recommended first spike for owning the visible terminal chrome while retaining an upstream engine. It is a QWidget, not automatically a drop-in QML item. Build the frontend with native Qt Widgets or explicitly evaluate a supported bridge; do not assume PySide bindings/QML embedding are packaged |
| **KonsolePart + original KDE frontend** | Debian trixie lists `konsole-kpart` 4:25.04.2-1 and KDE Frameworks 6 dependencies | Viable comparison if Konsole behaviour/integration is materially stronger. Plugin/API and profile access must be inspected against that exact packaged build. Legacy KDE3/KDE4 TerminalInterface examples are not proof of a current KF6 integration |
| **VTE + GTK frontend** | Debian trixie `libvte-2.91-0` 0.80.1-1 supplies a GTK3 terminal widget; upstream VTE Terminal docs expose terminal/process APIs | Maintained alternative if GTK frontend quality/accessibility wins the comparison. It introduces a different application toolkit from the proposed Qt shell. Do not embed a GTK widget in QML or promise cross-toolkit parity without a separate technical spike |
| **Current Konsole profile** | Existing `prototype/worldline/bin/steins-terminal` launches Konsole with the generated per-world profile | Keep as a functional fallback during the spike. A recoloured profile alone does not satisfy the owner's final terminal design |

Sources checked 2026-11-01: [QTermWidget upstream](https://github.com/lxqt/qtermwidget), [Debian runtime](https://packages.debian.org/trixie/libqtermwidget6-2), [Debian development files](https://packages.debian.org/trixie/libqtermwidget-dev), [Debian KonsolePart](https://packages.debian.org/trixie/konsole-kpart), [Debian VTE](https://packages.debian.org/trixie/libvte-2.91-0), [VTE Terminal documentation](https://gnome.pages.gitlab.gnome.org/vte/gtk3/class.Terminal.html). Upstream main-branch documentation can differ from Debian's package; compile and feature tests must use the shipped version. Inventory the selected upstream license/source obligations before packaging a linked frontend; the current MIT design/source assets do not relicense an upstream engine.

No new terminal engine, custom PTY protocol or shell parser is proposed. Acceptance requires real Bash/Zsh, Unicode/wide glyphs/combining characters, copy/paste and bracketed paste, resize/reflow, search, scrollback, hyperlinks, keyboard selection, SSH, tmux, Vim/Neovim and other full-screen TUIs. Include AT-SPI/screen-reader testing, child-process close handling, crash recovery and fractional scaling. Test true colour, ANSI 16-colour fallback and application-controlled colours separately. Installation, these compatibility tests and engine performance have not been performed in this design pass.

## IBN 5100 remains a separate artefact

Keep the retro amber presentation, existing `HELP`, `LIST`, `DIVERGENCE`, `SET`, `DMAIL`, status and secret commands. Launch it explicitly from the launcher or expanded meter action into a dedicated terminal session. Keep its connection to the same service/state; do not maintain an IBN-specific divergence. Respect reduced motion/fast text preferences for its typewriter treatment. Moving required attribution into an appropriate About/Credits surface is a separate reviewed content change, not a reason to remove licensing information silently.

The everyday terminal remains useful with no retro simulation. IBN can feel special precisely because its slower, deliberate presentation is not forced onto every shell session.

## Integrated navigator

### Entry and placement

The compact panel meter is visible during ordinary use, in a **184×46px** instrument region inside a **56px-high** panel. The panel sits 28px from either side and 20px above the bottom edge. Its tube presentation is quieter than the expanded app, but the full value is still readable. Click or keyboard-activate it to open a **530×650px** navigator anchored above the meter, aligned to the same horizontal centre when space permits. Clamp the surface inside the current work area. At narrow widths or increased text size, use a centred resizable dialog/scrollable layout rather than allowing the anchored surface to extend off-screen.

This is one shared navigator, not separate terminal/panel versions. Application-header chips invoke it using the same action. A configurable global shortcut is useful, but its binding needs a desktop collision audit; none is claimed as registered in the current prototype.

### 530×650 proposal

| Region | Rectangle | Interaction |
|---|---|---|
| Shared titlebar | x0 y0 w530 h42 | `Worldlines`, familiar window controls and discreet accent marker |
| Heading/current state | x22 y62 w486 h50 | `Choose a worldline` and `Stable · Steins Gate` from the confirmed snapshot. The current preview row and panel carry the full divergence |
| Search | x22 y125 w486 h40 | Search world names/known destinations; explicit clear action; not a command field |
| Scenic destinations | x22 y184 w486 h306 | Three 94px-high preview rows separated by 12px. Preview at x30; title, atmospheric cue and canonical divergence alongside; selection has edge/arrow plus text |
| Other-world caption/choices | x22 y516 w486 h62 | `All worlds` caption, then three 158×36px named chips at y542 for Alpha, Lugunica and Mitakihara; expand/scroll to full rows where needed |
| Status/error line | x22 y586 w486 h14 | Short contextual or error message; a production layout wraps/grows this region for longer errors |
| Action row | x22 y602 w486 h36 | 110px secondary `Cancel`; 362px primary `Shift to Hinamizawa` or `Retry appearance`. Destination is explicit in the primary label; do not hide failure feedback beneath the fold |

These reference coordinates follow the rendered design board. Production must use layouts, not absolute positioning. Larger fonts increase row height and permit scrolling. Long/localised world names wrap or elide with a full accessible name/tooltip; values do not truncate. At 1280×800 and 1366×768 keep native 100% text rather than shrinking every window to fit a composition. Ordinary overlapping windows are preferable to illegible miniatures. Increased-text layouts must reflow/scroll, not scale glyphs down to preserve a screenshot arrangement.

### Selection and shift semantics

1. Opening reads the latest authoritative snapshot and pack list. Focus starts in Search, with the current row labelled **Current**.
2. Clicking a destination or moving keyboard focus previews it. It does **not** commit a worldline shift. Show **Selected destination**, distinguish it from **Current**, and enable the single `Shift worldline` button.
3. Keyboard Tab follows search → scenic destinations → other-world choices → Cancel → primary action. Arrow keys navigate choices without causing a shift. Enter/Space activates the focused action. Escape dismisses the navigator and restores focus to the invoking meter/chip. Expanded meter remains a separate discoverable action in the meter's context menu, not an extra required confirmation step.
4. The primary action submits the destination through the shared service. Show the pending destination, retain the current value until commit and avoid repeated submissions during that transaction. Keep ordinary applications/input available.
5. On success, the destination becomes **Current**. On failure, explain the actual failed operation and expose Retry/Keep current/Close as appropriate. Preparation failure must not imply the selected destination became current. Partial appearance failure must distinguish persisted worldline from surfaces still awaiting retry.

The current prototype's cards switch immediately and must change for this staged selection design. Its D-Bus service already supplies snapshots and completion/error information, but the proposed transition stages are not implemented. Never synthesize a successful shift merely because a preview animation ended.

### Compact and expanded meter

The panel and terminal header display the same confirmed divergence, sourced from the existing per-user service. A UI-selected destination may be held transiently for preview, but it is never an independent authoritative value. Do not derive ranges or secrets independently in QML; use the existing registry/service.

Keep the original expanded GTK tube design available via `Expand meter` in the navigator or a meter context menu. Optional pinning belongs to a user preference. A single click on the panel meter always opens the navigator; avoid a required double-click or a hover-only action. Accessible labels announce the world name and full decimal value. Announce a committed change once, not for each animated digit.

The root storyboard proposes 800ms full motion: activation 0–90ms, digits 90–220ms, one distortion 220–400ms, commit at 400ms, reveal 400–620ms, stabilise 620–800ms. That is a design timing target, not measured compositor behaviour. Reduced/off and failure handling are specified in the engineering handoff. Keep the decimal point fixed, never flash through high-contrast frames and suppress digit movement in reduced motion.

## Ordinary application cohesion

**File manager:** preserve Dolphin's familiar Places, breadcrumbs, navigation, search, list/grid views, drag/drop and file-operation controls. Use the shared header/decorations, quiet sidebar, selected location treatment, icon family and spacing. Do not rename real folders for flavour or paint decorative system statistics into the sidebar. Any exact toolbar restructuring in a mockup is proposed; supported theme APIs alone may not reproduce it.

**D-Mail:** preserve upstream Thunderbird's real account/folder/message/compose layout and sender/recipient/security controls. Use the original D-Mail launcher icon, shared window decoration and a supported theme. It should be a supporting application, not a bespoke theatrical email frontend. The current local synthetic send/receive result does not qualify provider OAuth or updates. Supported static/dynamic themes have documented scope; they do not grant arbitrary layout replacement, and message/compose surfaces require separate evaluation. [Thunderbird's official guide](https://developer.thunderbird.net/add-ons/web-extension-themes) is the integration reference. Do not remove warnings, change message content or conflate real sending with fictional terminal `DMAIL`.

The multi-application board uses a simplified D-Mail content panel to communicate the **conceptual supported-theme target** within the composition. It is not a Thunderbird render, proof of a replacement layout, or a promise that static theme APIs can move every illustrated control. The earlier real guest captures remain the runtime evidence.

**Settings:** use familiar names such as Appearance, Worldlines, Sound and Accessibility. A Worldlines page owns meter visibility, default scene and motion/audio choices. Use the same controls and semantic states; do not create a second shadow settings store for existing system volume/network controls.

**Notifications:** quiet opaque lifted surface, same icon family, app/source name and readable body; one accent marker, no animated decorative telemetry. Distinguish a worldline change from ordinary task notifications. Coalesce repeated shift requests and avoid announcing every digit. Use real application success/error events only.

**Context menus/dialogs:** same typography, 8px spacing rhythm and strong keyboard focus; retain familiar verbs and destructive-state semantics. No essential action only appears on hover. Authentication/certificate dialogs keep the upstream trust signals and identity. Ordinary data/application dialogs never claim that the fictional worldline caused real corruption.

## Evidence and remaining decisions

Inspected existing source: `prototype/worldline/lib/worldline_service.py`, `steinsplasma.py`, `prototype/worldline/share/Navigator.qml`, `prototype/worldline/bin/steins-terminal` and legacy IBN code. Those demonstrate the current state/launcher contract, not these proposed layouts. No host/guest configuration, runtime package, terminal engine or personal profile was changed by this document.

Before implementation: choose the frontend component after a contained compile/accessibility/compatibility spike; approve the staged navigator action; decide shared client/server decoration responsibilities; qualify layout at 1280×800, 1366×768 and 1920×1080 plus large text; verify all shell shortcuts and AT-SPI behaviour; reconcile the transition coordinator with legacy CLI triggers. The prototype remains the rollback reference until exact built artifacts pass the new gates.
