# Worldline — creative proposal 01

**Status: design proposal and a read-only review tool. No new desktop, theme or effect has been installed.** This responds to Gary/Burrito's complete creative review of 2026-11-01. The working distribution and Plasma experiment remain the functional reference while the new direction is assessed.

The proposed experience is a quiet laboratory instrument surrounding illustrated summer worlds: graphite housings, warm readable type, one route-shaped icon family and an always-visible tube divergence control. Worldline changes affect light, accent and environment while controls retain their place. The interface identity is carried by the shell and applications, including when the wallpaper is hidden.

![Cohesive desktop concept](boards/multi-app-steins-gate-1920x1080.png)

## 1. The desktop and shell

Use one original 56-DIP panel, with a consistent hierarchy: application launcher; compact divergence instrument; running applications; practical status/audio/network/clock/power controls. Its side/bottom insets are intentional breathing room, not a second dock. There is no permanent monitoring overlay. App indicators pair a readable icon with an underline/background; state is not communicated by accent colour alone.

The compact divergence control is **184×46 DIP**, present by default. It preserves the existing glowing tube identity at a quiet scale. Clicking or keyboard-activating it opens the anchored navigator; expanded tubes remain an optional larger instrument. The same authoritative value appears in the terminal header. These displays never calculate or save their own competing numbers.

The original launcher uses the same housing, icon geometry, search field, focus states and recent/pinned-app grammar as the navigator. The first panel surface is intentionally restrained: a memorable instrument, not multiple decorative status strips.

- [Minimal desktop](boards/desktop-steins-gate-1920x1080.png)
- [Launcher](boards/launcher-steins-gate-1920x1080.png)
- [Wallpaper hidden: identity check](boards/plain-steins-gate-1920x1080.png)
- [Compact and expanded divergence](boards/navigator-steins-gate-1920x1080.png)

This is a new shell design, not a promise that an ordinary Plasma layout script can realise it all. The engineering recommendation is to first test owned QML shell components over maintained Plasma/KWin services, with an independent LayerShellQt frontend as a comparison if needed. The final visual design is not constrained to today's stock panel. A new compositor is not justified by the evidence. See the architecture comparison in [ENGINEERING-HANDOFF.md](engineering/ENGINEERING-HANDOFF.md).

## 2. One desktop with ordinary applications open

The multi-app board contains terminal, files, navigator and simple real mail together. The shared 42-DIP header, route-family icons, 36-DIP caption targets, dark selection surface, restrained active marker and predictable spacing provide continuity. Inactive windows keep readable titles. The appearance does not depend on every application using identical content layouts.

The terminal and navigator are surfaces the project can own deeply. File manager, settings and mail retain maintained application engines and supported functionality. Their boards are **visual targets**, not captures of customised Dolphin/Thunderbird or evidence that all controls can already be styled. The D-Mail composition simplifies real client content to assess cohesion; it does not propose rebuilding Thunderbird's inbox layout.

At small resolutions, preserve ordinary text sizes and allow realistic window overlap. Do not shrink four whole applications into tiny unusable tiles just to fit a presentation. [1280×800 composition](boards/multi-app-steins-gate-1280x800.png) and [1366×768 composition](boards/multi-app-steins-gate-1366x768.png) are authored target arrangements; live accessibility and implementation tests remain later work.

## 3. Illustrated worlds

Three representative original scene proposals establish the intended anime-background direction:

- **Steins Gate:** illustrated electronics rooftops, an amber laboratory window, ink-blue architecture and expressive summer-evening sky.
- **Hinamizawa:** rice fields, a shrine at the cedar edge, warm sunlight and peaceful green stillness. The default accent is moss, not a mandatory horror treatment.
- **Hitogashima:** bright island harbour, luminous clouds, cyan sea and quiet coastal architecture.

The same shell is shown in [rural](boards/desktop-hinamizawa-1920x1080.png) and [coastal](boards/desktop-hitogashima-1920x1080.png) atmospheres. Alpha, Lugunica and Mitakihara have distinct art briefs and palettes; their final drawings are not produced in this pass. See [ART-DIRECTION.md](art/ART-DIRECTION.md), the full [prompt set](art/PROMPTS.json) and [asset provenance](art/PROVENANCE.json).

Native generated scene size is 1672×941. The 1080p boards show a scaled composition target; they are not native 4K masters. Final scene production, multiple aspect ratios and crop quality need approval before release.

## 4. A flagship everyday terminal

The everyday terminal owns its frame, tab strip, divergence header, search/split/session affordances and typography. It has no stock Konsole menu/toolbar silhouette in this concept. It remains an ordinary selectable-text terminal for shells, editors, SSH and development workflows.

Use a maintained terminal component. The first engineering spike is an original Qt frontend around QTermWidget 6, compared with KonsolePart if KDE integration helps. This is not implemented and is not assumed to be a drop-in QML/Python widget. PTY, IME, Unicode, true colour, scrollback, copy/paste, accessibility, split sessions and keyboard behaviour must be qualified on the exact Debian build.

The separate **IBN 5100** keeps its deliberate retro interaction, command compatibility, secret commands and local fictional D-Mail. It remains a special instrument reached from the meter/launcher, not the everyday terminal's visual mode. See [terminal closeup](boards/terminal-steins-gate-1920x1080.png) and [APPLICATION-SPECS.md](apps/APPLICATION-SPECS.md).

## 5. The navigator and shared instrument

The navigator is an anchored shell surface, not an unrelated six-button utility. It shows confirmed current state separately from a selected destination. Illustrated preview rows identify the destination; the primary **Shift** action is deliberate. Hovering a card does not change reality. Tab/arrows/Enter/Space/Escape have explicit roles; focus is visible and does not rely on colour.

Compact panel readout, expanded meter, navigator and terminal header subscribe to the same model. A preparation failure leaves the current worldline intact and offers **Retry shift**. A post-commit partial appearance failure must identify the confirmed destination and failed surface, with **Reapply appearance**; these are different conditions and must not share a misleading success animation. The [failure board](boards/error-steins-gate-1920x1080.png) illustrates the pre-commit case.

## 6. The signature worldline shift

![Worldline shift storyboard](boards/shift-storyboard.png)

The proposed Full sequence targets **800 ms after preparation**, not a measured performance result:

| Time | Moment | User-visible purpose |
|---|---|---|
| 0–90 ms | Activation | Immediate local feedback on the trigger |
| 90–220 ms | Instability | Tubes move once toward a destination; no rapid flashing |
| 220–400 ms | Distortion | One restrained native spatial ripple, if qualified |
| 400 ms | Commit | Coordinated state/environment change |
| 400–620 ms | Transformation | Supported appearance surfaces reveal the new world |
| 620–800 ms | Stabilisation | Confirm the value; optional quiet completion cue |

**Reduced** uses a proposed 180-ms crossfade/accent change, static confirmed digits and no spatial distortion. **Off** applies immediately with a quiet status result. Apps, input, authentication and user data remain intact. The native effect is optional; if unavailable, fall back to Reduced/Off. Never fake native integration with a desktop-sized focus-stealing application.

The review viewer can play a **contained timing study**. Its crossfade/ripple marks are diagrammatic review graphics, not a KWin shader or a change to the actual desktop. Full mode is user-selected; Reduced is its default. The storyboard/spec governs the intended future implementation.

Original quiet [sound previews](engineering/audio/manifest.json) include activation, meter movement, stabilisation and a combined cue. They are synthetic WAV assets, not installed system sounds. Audio is off by default, never unmutes the system and is independent of motion settings. No audio was automatically played during this work. Longer ambience is specified by world but not generated. See [TRANSITION-SPEC.md](engineering/TRANSITION-SPEC.md).

All fictional triggers—navigator, compact/expanded instrument, IBN and local D-Mail—must eventually converge on one staged transaction path. Normal real email sending never changes divergence. The current service does not yet provide the full staged protocol; [storyboard.json](engineering/storyboard.json) and the engineering handoff describe the new events and failure semantics as proposals.

## 7. A system, not a wallpaper collection

The visual language extends to boot/login/lock, menu/dialog/settings, notifications and logout/shutdown:

- [Boot direction](boards/boot-steins-gate-1920x1080.png): retain the original emblem; quiet progress, no ornamental readouts.
- [Login direction](boards/login-steins-gate-1920x1080.png): readable authentication, familiar focus and clear sign-in. No private worldline-service access from the unauthenticated greeter.
- [Lock direction](boards/lock-steins-gate-1920x1080.png): time, date and a clear unlock action; no cinematic effects over authentication.
- [Settings, notification and shutdown](boards/system-steins-gate-1920x1080.png): common opaque surfaces, type, icons, selection and plain actions. Future shutdown status must say shutting down rather than reuse a startup message.

The [editable tokens](system/tokens.json), [design specification](system/DESIGN-SYSTEM.md), [icon sheet](system/icon-sheet.png) and sixteen original SVG icons define shared semantic colours, six accents, spacing, radii, typography, focus/selection, control targets and motion. All nineteen explicitly measured flat colour pairs exceed 4.5:1; the minimum is 5.61:1. That does not establish accessibility of a future transparent composite, third-party app or live screen reader.

## 8. Implementation and review gates

This pass supplies the eight requested creative deliverables. It does not install them or declare the final architecture approved. The next concrete step after owner review is an isolated **original panel + compact meter + anchored navigator** spike, followed by the maintained-engine terminal spike. Qualify the signature identity with wallpaper hidden before expanding the migration.

Then converge trigger/state events, qualify native effects/audio, finish six illustrated environments, integrate real applications and session surfaces, split/migrate packages and rebuild a separately versioned ISO. The exact new artifact must repeat BIOS/UEFI installation, update, profile preservation and reboot testing. The previous ISO's test results cannot be transferred to an unbuilt redesign.

The owner's three acceptance questions remain the review rubric:

1. With wallpaper hidden, do the panel, meter, icons, terminal and common chrome carry one recognisable identity?
2. Does changing worlds have a deliberate activation/transition/stabilisation grammar while staying comfortable and accessible?
3. Do ordinary applications together feel like one product, with honest supported-integration limits?

## View and verify

Run the local read-only viewer using the existing host PySide6 installation:

```sh
/usr/bin/python3 '/home/developer/Documents/ChatGPT/Steins;OS/design/worldline-v1/preview/review.py'
```

Choose a scene, board and authored resolution; use the plain-background board or preview shift timing. The viewer has no connection to the real worldline service, mail or desktop configuration. `BOARDS.json` records exported compositions. `build_boards.py` rebuilds editable SVGs and PNGs using the existing builder container. It does not build an ISO.

[Validation and limitations](evidence/VALIDATION.md) distinguish exported designs, viewer smoke checks, token/audio measurements and the still-unimplemented operating-system work. New code/icons are MIT; original scene/audio assets follow their recorded CC-BY-4.0 provenance. Existing upstream applications, fonts and the project emblem retain their licenses.
