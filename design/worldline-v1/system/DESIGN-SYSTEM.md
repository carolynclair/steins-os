# Worldline visual system — proposal 01

**Status:** a coherent design proposal for owner review. These tokens/icons are not installed theme values, and this document does not establish runtime support for a custom shell or compositor effect. It accompanies the original artwork, desktop compositions and engineering proposal elsewhere in this design folder.

## The visual idea

Quiet instrument housings, precise illuminated readouts and illustrated summer light. The identity comes from a continuous graphite shell, the compact tube readout, a recognisable route motif, calm proportions and the same typography/control rules across ordinary applications. The artwork supplies atmosphere; it does not supply the interface.

Use one interaction system in all six worlds. Change the accent, illustrated environment and a few approved light/material details. Preserve control positions, semantic danger/success colours, keyboard behaviour and text legibility. The Hinamizawa default is peaceful moss green; any future unsettling treatment is a separately enabled experience, not the default interface palette.

## Palette and semantic roles

`tokens.json` is the editable source. Every screen uses named roles rather than copying whichever colour currently looks close. App content that has its own established colour semantics can retain them.

| Role | Value | Use |
|---|---|---|
| Canvas | `#101820` | Desktop neutral background; identity check without wallpaper |
| Panel | `#151f28` | Persistent shell and window frame |
| Raised | `#1d2a35` | Launcher, cards, menus and secondary surfaces |
| Hover | `#293946` | Pointer feedback, kept separate from selection |
| Input | `#0c1319` | Input fields, terminal body, tube housing |
| Border | `#435767` | Boundaries; never the only keyboard-focus indication |
| Text | `#eee9df` | Warm ivory primary text |
| Muted | `#a9b6bf` | Explanatory labels, inactive window title |
| Subtle | `#90a3af` | Lower-emphasis readable supporting text |
| Selection | `#334657` | Dark selected rows with ivory text |
| Default accent | `#efad60` | Steins Gate active state, compact tubes, focus |
| On-accent | `#101820` | Text/icons on a solid accent primary button |
| Success / warning / error / information | `#a9cd9a` / `#efc476` / `#f3978b` / `#8ecada` | Consistent semantic states in every world |

Do not put ivory text on a bright solid worldline accent. Use dark `onAccent` text there. Do not use a pale selection fill with low-contrast text, a tinted placeholder as an error message, or worldline accent alone to communicate an unsafe operation.

### Worldline accents

| Worldline | Accent | Atmosphere |
|---|---|---|
| Alpha | `#ec887d` | Copper dusk; experimental origin, distinct from default amber |
| Steins Gate | `#efad60` | Warm laboratory light and nostalgic urban summer |
| Hinamizawa | `#b8ca81` | Moss, rice fields and rural afternoon stillness |
| Hitogashima | `#72c9dc` | Sea glass, open ocean and luminous summer skies |
| Lugunica | `#b6a0ec` | Atmospheric stone, fantasy silhouettes and violet light |
| Mitakihara | `#e6a7d4` | Elegant geometric city forms and restrained rose light |

These are proposed UI accents, not replacements already applied to the current pack registry. A wallpaper can contain a richer art palette; controls still use the semantic values above.

### Measured contrast

`build_system.py` computes linearised sRGB relative luminance and contrast ratios from the literal hex values, and saves `contrast-report.json`. These measurements assume opaque flat surfaces. They do not validate translucent compositing over arbitrary wallpaper or third-party application content.

| Pair | Ratio |
|---|---:|
| Primary text / canvas | 14.79:1 |
| Primary text / raised surface | 12.10:1 |
| Muted text / raised surface | 7.06:1 |
| Subtle text / raised surface | 5.61:1 |
| Selected text / selection background | 8.06:1 |
| Error text / raised surface | 6.70:1 |
| Six accents / raised surface | 5.84–8.23:1 |
| Dark primary-button text / six accent fills | 7.14–10.06:1 |

The intended normal-text minimum is 4.5:1; the focus-indicator minimum is 3:1 against adjacent surfaces. All explicitly measured pairs exceed those targets. A 1-pixel decorative border is not sufficient evidence of an accessible focus state. Any future translucency must preserve an opaque content backing or be remeasured on representative composites.

## Typography

Use the existing licensed Noto Sans family for interface text and DejaVu Sans Mono for the everyday terminal/prompt. Retain the existing tube renderer for the expanded divergence display; no new imitation Nixie font or copyrighted decorative face is required. Font files are not bundled by this token package; upstream font licenses continue to apply.

- Body/control target: 14 device-independent pixels, weight 400/500. Supporting caption: 12 DIP, only for secondary information. Do not put essential authentication, recipient addresses or errors solely in the smallest style.
- Section/title/display hierarchy: 18 / 24 / 32 DIP. Use weight 600 for selected headings; reserve letter spacing for short instrument labels.
- Body line height: about 1.45. Terminal target starts at 14 DIP and remains user-adjustable with explicit line-height/character fallback tests.
- Readout digits: tabular alignment, 18 DIP compact target. The full-size tube display retains its current visual identity.
- DIP sizes describe the composition at 100% scale. Implementations derive actual font sizes from the user's font and scale settings; do not hard-code physical pixel sizes or shrink text automatically to make a layout fit.

Ordinary prose uses sentence case. Keep short, recognisable action verbs. A pathname, recipient address, secret code, password or terminal output is data: preserve it and keep it selectable where appropriate.

## Geometry and material

Use a 4 / 8 / 12 / 16 / 24 / 32 / 48 DIP spacing ladder. Controls use an 8 DIP radius; main windows 12; panel 16; tube cells 6. Avoid applying a giant radius to every row or wrapping every object in its own card.

Use a 1 DIP boundary, 2 DIP focus ring and 2 DIP active marker. Content margins are normally 16 or 24 DIP. The shared window header is 42 DIP, including its boundary; caption actions have a 36×36 DIP pointer target. Main controls prefer 40 DIP targets; compact controls may use 36 DIP, and touch layouts expand to at least 44 DIP. Visible icon size is independent of its hit area.

The panel target is 56 DIP high, inset 28 DIP from each side and 20 DIP from the bottom edge at the reference desktop sizes. Keep launcher, app switching, compact divergence and practical status controls in one coherent housing. Avoid a second permanent monitoring bar. These composition insets are explicit tokens; they are not the spacing-ladder defaults for ordinary app content.

Windows are predominantly opaque. Small shadows explain stacking, not a second neon lighting system. An active window gets a restrained accent segment/node and clear title contrast. Inactive windows keep readable titles and preserve content; they do not become grey silhouettes.

## Interaction states

| State | Shape / material | Text and behaviour |
|---|---|---|
| Rest | Panel/raised surface with a quiet boundary | Ivory primary, muted supporting text |
| Hover | Raised-hover surface | No sound by default; no layout shift |
| Pressed | Brief darker inset or compressed highlight | Action fires on normal release semantics; no decorative wait |
| Selected | Dark selection + persistent 2 DIP accent marker | Label/check/state indicator persists; colour is not the only cue |
| Keyboard focus | 2 DIP accent ring with 2 DIP gap | Independent of selected state; never clipped by the container |
| Disabled | Noninteractive surface, clearly disabled control | Keep reason/help readable; disable the action rather than accept-and-fail silently |
| Busy | Small progress indicator/label | Preserve cancellation/input where relevant; prevent duplicate destructive actions |
| Error | Semantic error icon + short text + relevant retry | Keep the committed worldline/status truthful; never substitute a success animation |

The normal, focused and selected states must remain distinguishable when motion is off. Use an icon/label/geometry alongside colour for network state, unread mail, volume mute, shift failure and current-world selection.

## Compact divergence control

The compact panel readout is **visible by default** during ordinary desktop use. Its reference housing is 184×46 DIP, with a 160 DIP minimum width composition target; allow growth with text scale. Render the eight-character divergence (`d.dddddd`) in small tube housings, with a narrower period housing. Preserve a subtle glass rim and a warm/cool emission consistent with the active worldline. Do not add ambient digit flicker, random numbers or a looping animation while the value is stable.

The entire readout is one keyboard/pointer target. Primary activation opens the worldline navigator anchored to the panel location; it does not immediately change worldline. The navigator supplies an explicit path to the existing expanded meter. The everyday terminal may display the same authoritative value as a compact header action.

Accessible name: “Worldline, Steins Gate, divergence 1.048596” (substitute actual state). Announce the stable destination once after a successful shift, not every digit of a transition. Clicking/closing the full-size display must not invent another state file or change the numeric value.

If space is tight, collapse nonessential pinned-app labels and move extra tray items into a reachable overflow. Keep the compact readout, launcher, essential app switching and clock accessible. Do not sacrifice legibility by making the digits microscopic.

The reference launcher is 430 DIP wide. The navigator is 530 DIP wide and uses a single column of 486 DIP preview rows, with 22 DIP horizontal margins. These dimensions match the supplied application boards; they do not prescribe a three-column card grid. At increased text size the surface can grow/reflow or scroll, preserving the same controls and focus order.

## Terminal and ordinary applications

The proposed everyday terminal earns its identity through its caption/header rhythm, original tab geometry, readout placement, typography, prompt and matching controls. It remains a real terminal frontend around a maintained engine. The concept does not claim an engine implementation.

- Preserve ordinary terminal input, escape sequences, copy/search/selection, scrollback and accessibility. `Ctrl+C` keeps its shell meaning; proposed application copy/paste defaults use `Ctrl+Shift+C/V`.
- `F6` can move between header/tabs/body focus regions; `Tab` inside the terminal remains shell/application input. Tab shortcuts must remain configurable and avoid stealing terminal program keys without a documented mode.
- Worldline changes preserve the running process, input buffer, selections, scrollback and current working directory. A header readout is informational/interactive chrome, not a new shell interpreter.
- A custom prompt is opt-in and shell-aware. Never replace a user's shell configuration wholesale to obtain a screenshot.

The file manager, settings and notifications follow the same colour/type/icon/frame rules. A mockup may illustrate desired spacing, but existing applications retain their supported integration surfaces until an implementation has been tested. Do not imply that Thunderbird's basic theme API can redesign every compose/message element, or that a window decoration controls every client-drawn header. D-Mail remains a simple supporting application with real addresses, errors and authentication controls intact.

Menus and dialogs use the same focus ring, spacing ladder and semantic action ordering. Notifications should be concise and contextual. Do not produce a giant success toast for every worldline change; the readout/navigator already show that state. Failures remain visible until addressed or dismissed.

Boot/login/lock/logout surfaces share the instrument housing and restrained light language. Authentication remains readable and functional. Avoid decorative distortion over credentials, fake authentication feedback or a login flow that depends on a working worldline effect.

## Keyboard, scaling and reduced motion

Proposed shell defaults: `Super` opens the application launcher; `Super+W` opens the worldline navigator, subject to collision review. Escape closes a transient launcher/navigator and restores focus to its invoker. Arrow keys move within card/list groups; Enter/Space activate the focused control. Tab traverses logical groups, and activation must not strand focus behind an overlay. Touch, keyboard and pointer paths reach the same actions.

Target layouts are 1280×800, 1366×768 and 1920×1080. These are **target specifications**, not all verified runtime layouts. Test at 100%, 125%, 150%, 200% display scale and increased system text size. Cards reflow instead of squeezing titles; windows scroll vertically where necessary; critical controls remain visible/reachable. At 1280×800, retain a usable content region above the 56 DIP panel and its margins. At large text sizes, grow the panel/readout and reduce optional ornament before truncating meaningful content.

Off: immediate, truthful state/theme update; static readout; no sound implied. Reduced: a proposed maximum 180 ms opacity/material change and one stable digit update, with no spatial distortion. Full: a single short coordinated transition may use the separately specified compositor behaviour, with an 800 ms target and proposed maximum of 900 ms. These are visual targets after preparation, not promises that every third-party application can apply its theme in that time. System/user motion settings win. No rapid flashing, forced cursor capture, application restart or decorative input lock. A failed effect must not prevent state recovery or login.

Sounds are optional and off by default. System mute/user volume win. No hover noise, background ambience or repeated success chirps in normal navigation. Never use an audio cue as the only confirmation or error channel.

## Icon family and scope

The `icons/` folder contains 16 original 24×24 SVG sources using a shared 1.75-unit round stroke and `currentColor`: launcher, terminal, navigator, files, D-Mail, settings, network, volume, power, search, close, minimise, maximise, plus, arrow and lock. `icons.svg` provides symbols for code-native compositions; `icon-sheet.svg`/`.png` show actual 16/24/32 pixel examples.

The route-and-node motif belongs to the Worldline launcher/navigation family. Terminal, files and mail keep familiar silhouettes so daily recognition stays fast. Project application launchers may use a common neutral tile; action icons stay unboxed. Active state comes from accent/marker and accessible label, not six unrelated rainbow icon packs.

This is a **starter family, not complete desktop icon coverage**. Preserve third-party application identity/trademarks. If a vendor icon does not match, use consistent containment and spacing; do not redraw another product's identity without review. Full MIME type, device, battery, accessibility and status coverage remains work.

## Validation and files

- Generator: `python3 design/worldline-v1/system/build_system.py`. It asserts all listed normal-text contrast ratios ≥4.5, parses each icon/sheet as SVG XML, and writes sources locally.
- Render: existing `steins-os-builder:trixie` container `rsvg-convert` produced `icon-sheet.png` at 1280×800. The rendered sheet was visually inspected for alignment, clipping and small-size recognisability.
- Measured: flat-colour contrast, generated SVG/XML validity, 16/24/32 sheet rendering.
- Not measured here: screen-reader behaviour, touch usability, high-DPI native app rendering, final animation performance, arbitrary third-party app contrast or full icon-theme coverage.

New token/icon/generator sources and this document use the repository's MIT license; see `LICENSE`. Upstream font/application assets retain their own licenses. No screenshots, official anime logos, character art, music or voice clips were used to create these icons.
