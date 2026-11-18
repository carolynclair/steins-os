# Worldline Shell — engineering proposal

2026-11-01. **Design/architecture specification, not a new installed shell.** This pass reads the current prototype and official upstream documentation. It does not modify Parrot, a VM, the ISO, the worldline service or its packages. The working prototype is the recovery/reference system while the owner reviews the proposal.

## Recommendation: own the experience, retain the infrastructure

Build an original Worldline component set—panel, compact divergence meter, launcher, navigator, controls and notification presentation—on a maintained desktop stack. Evaluate the complete design in a disposable session rather than accepting the current stock panel's geometry or interaction model. The lowest-risk first implementation spike is **owned Qt/QML shell components hosted by Plasma and KWin**. This is a technical recommendation to test, not a declaration that Plasma's existing appearance is the final product.

Current guest evidence is Plasma/KWin **6.3.6** with Qt **6.8** bindings on Debian 13. Upstream documentation is current and may describe newer features. Exact imports, protocols and effect interfaces must be tested against the shipped Debian versions; documentation establishes extension mechanisms, not compatibility or completed implementation.

| Architecture to evaluate | What the project owns | Reused infrastructure | Qualification cost and unresolved questions |
|---|---|---|---|
| **A. Original Plasma/QML component set, with a project shell/containment package if required** | Original panel composition, launcher/navigation, meter, controls, design tokens and interaction states; selected decorations | KWin, session/login integration, existing task/tray and desktop services where exposed | Recommended first spike. Do not mistake layout scripting for unlimited rendering control. Check custom containment/panel package behaviour, task models, tray popups, focus, accessibility, mixed DPI and crash recovery on 6.3.6. Original geometry must remain the design target |
| **B. Independent Qt frontend using LayerShellQt over maintained KWin** | Dedicated panel/launcher/navigator surfaces and their process lifecycle | KWin/compositor, Qt, system services | A serious alternative if A cannot realise the design cleanly. LayerShellQt exposes layer-shell surfaces; it does not by itself supply a complete shell. Task/window actions, tray protocols, notifications, shortcuts, portals, keyboard focus, output placement and recovery become explicit integration work |
| **C. New compositor / broad desktop fork** | Compositor or a fork of a full DE, plus all dependent UX | Selected lower-level libraries only | Not justified by this review. Greater update/security/accessibility/session burden without evidence it is needed. Qt compositor examples demonstrate mechanisms, not a daily-use replacement compatible with arbitrary applications |

The comparison is our engineering inference from upstream extension surfaces. No A/B prototype or performance comparison has been executed in this design pass. KDE documents QML widgets, panel/widget scripting and original window-decoration surfaces; the layer-shell library documents access to layer-shell settings on a `QWindow`. [Plasma widgets](https://develop.kde.org/docs/plasma/widget/), [KF6 porting notes](https://develop.kde.org/docs/plasma/widget/porting_kf6/), [desktop scripting](https://develop.kde.org/docs/plasma/scripting/), [LayerShellQt README](https://github.com/KDE/layer-shell-qt/blob/master/README.md), [Aurorae decorations](https://develop.kde.org/docs/plasma/aurorae/).

Qt's custom-shell example requires server and client extension implementations. Its QtShell compositor example constrains client support; these are reasons not to infer ordinary-app compatibility from a demo compositor. [Qt custom-shell example](https://doc.qt.io/qt-6/qtwaylandcompositor-custom-shell-example.html), [QtShell example](https://doc.qt.io/qt-6/qtwaylandcompositor-qtshell-example.html).

### Flagship terminal

The design should own the terminal's window/header, tabs, command affordances and divergence display. A Konsole profile cannot deliver that entire frontend. First compare a custom Qt Widgets frontend around **QTermWidget 6** with a KDE component option, preserving normal PTY/application behaviour. The LXQt project describes QTermWidget as an embeddable Qt 6 terminal widget; Debian trixie provides `libqtermwidget6-2` **2.1.0-1**. That makes it a concrete candidate, not a qualified replacement. [QTermWidget upstream](https://github.com/lxqt/qtermwidget), [Debian package](https://packages.debian.org/trixie/libqtermwidget6-2).

Test selection, keyboard shortcuts, IME, bidi/Unicode, accessibility, hyperlinks, bracketed paste, alternate screen, shell integration and long-lived terminal jobs before choosing it. Do not claim a native QML terminal component: QTermWidget is a Qt widget, and integrating a QML header needs its own rendering/focus evaluation. Preserve Konsole as an ordinary fallback until the frontend is proven. Review upstream/component licenses when packaging rather than assuming all new linked code can remain MIT.

IBN 5100 stays a separate deliberately retro experience. Preserve the current command parser and its output/secret behaviours. A maintained terminal component may host it, but its UI must not be flattened into the everyday terminal's modern command area.

## Current state and precise API gaps

The prototype already has one persisted number in `~/.local/state/steins/divergence`, a validated pack registry and an atomic replacement helper. `org.steinsos.Worldline1` exposes JSON snapshots and apply results. It prepares assets before bus-requested state changes, then runs Qt palette, wallpaper and GTK appearance steps. This is useful existing work.

The following are source findings, not speculative deficiencies:

- `SetDivergence` is synchronous and supplies no job ID, preparing/ready phase, cancellation or pre-commit signal. Its `StateChanged` and `ApplyFinished` are emitted after appearance operations.
- `revision` is a content hash of state/preferences. A→B→A can return the same hash; it is not an ordered transition sequence.
- `apply_prepared` applies different presentation surfaces sequentially. It is not a compositor-wide visual transaction. Existing applications can cache palettes or theme files.
- The service observes legacy writes. IBN `change()` and terminal `dmail` still calculate/write state outside the session service and may also invoke the adapter. Relative D-Mail changes are not yet serialised with other writers.
- There is no compositor-effect client, animation schedule, capability negotiation, sound client or per-surface completion report. The existing `motion` preference reserves a future interface; it is not evidence of implemented effects.
- The optional meter is a separate child app. A compact shell display and terminal header must be new subscribers to the same snapshot, not new owners of the number.
- The retained numerical file uses atomic replacement, but there is no claim of crash-durable multi-file commit or a persistent transition journal.

The old source entry points remain `prototype/worldline/lib/worldline_service.py`, `steinsplasma.py`, `config/includes.chroot/usr/local/lib/steins/steinslib.py` and `usr/local/bin/{ibm5100,dmail,steins-worldline,steins-meter}`.

## Proposed version-2 transition contract

Specify and test a separate versioned interface before changing callers. Preserve the v1 interface through an adapter while migrating. The following names and payloads are **proposed**, not endpoints available today.

| Operation/event | Proposed behaviour |
|---|---|
| `GetSnapshot()` | Return canonical divergence, pack/palette, preferences, service-instance UUID, sequence, current job/phase, effective motion/audio policy and actual capability summary |
| `RequestShift(target, origin, request_id, expected_revision)` | Validate and return an in-memory job ID promptly. An absolute target may be a pack ID or normalised number. Optional expected revision rejects stale intent instead of silently overwriting it |
| `RequestDmailShift(text, origin, request_id)` | Resolve the existing deterministic relative delta **inside** the serialised model when its job becomes active. Do not log/store text; do not send network mail |
| `CancelShift(job_id)` | Cancel a queued/preparing or staged job before the commit boundary. After commit, return a truthful `AlreadyCommitted` result; do not imply rollback of applications or user data |
| `GetJob(job_id)` | Query accepted/preparing/ready/animating/applied/partial/failed/cancelled status, stage timing and per-surface outcomes |
| `ShiftAccepted`, `PreparationProgress`, `ShiftReady` | Let the shell acknowledge immediate input and present preparation without pretending that divergence has changed |
| `ShiftStarted(job_id, start_monotonic, commit_offset_ms, policy)` | Coordinate the agreed finite presentation timeline, after preparation. Clients must understand service restart/epoch and not replay old schedules |
| `StateCommitted(job_id, snapshot)` | Canonical number has been atomically replaced. Displays distinguish the confirmed value from an ephemeral destination preview |
| `SurfaceApplied(job_id, surface, revision, outcome)` | Record which supported surfaces acknowledged the new revision. Do not call an unsupported native surface successful |
| `ShiftFinished(job_id, final_snapshot, outcomes)` | Report complete or partial apply. Ordinary shell use remains available in either case |

Use opaque `(service_instance_uuid, sequence)` ordering per service lifetime. On restart, clients receive a new instance ID, discard scheduled effects/jobs and read the canonical numeric file. There is still only one persisted divergence. Do not persist another authoritative number inside panel/navigator/terminal preferences. Accepted job IDs/idempotency keys need an explicit bounded lifetime; a restarted service must report `UnknownJob` rather than invent a historical result.

One service owns a serial commit queue and the state-file lock. The future async API can accept a bounded FIFO (proposed maximum four); queued relative shifts calculate from the latest committed number when activated. The navigator disables duplicate clicks on an accepted request. At capacity, return `Busy` with no invisible state mutation. The v1 synchronous adapter should reject `Busy` rather than queue work beyond old callers' deadlines. A client timeout is not proof a request failed: query the job/snapshot before retrying with the same idempotency key.

### State/apply boundary

1. Validate request and available pack; acknowledge immediately without changing divergence.
2. Prepare destination assets/palette/profiles privately and check compatible appearance adapters. Do not run rendering on a shell UI thread. Give slow preparation a visible, cancellable state; a proposed 10-second preparation deadline must be qualified on the N4500.
3. Once ready, choose effective Off/Reduced/Full policy from user preference and actual compositor/session capabilities. Announce the finite schedule. The visual 800 ms target starts **here**, not at a potentially slow renderer invocation.
4. At the commit boundary, atomically persist the one canonical number and then notify confirmed state. Strengthen durability with file/directory sync only after failure/recovery tests; do not claim existing rename alone provides it.
5. Apply only supported appearance surfaces and collect actual results. Compositor presentation may soften sequential palette changes; it cannot make arbitrary third-party apps transactional.
6. Finish without closing/restarting user applications. Report any stale native surfaces and provide a deliberate Reapply action. Reapplication never replays a cinematic effect or sound.

Before commit, an asset/disk error preserves the old state and restores any destination preview. After commit, retain the new canonical state, stop effects cleanly and report `partial` with retry; do not silently oscillate back to the old world or fabricate successful acknowledgements. A later explicit user shift can request the previous world. Desktop appearance files are user configuration, but no unrelated user documents, terminal jobs, mail, or application data are modified by a shift.

### Trigger convergence

| Trigger | Route |
|---|---|
| Navigator card / keyboard action | Version-2 absolute request; same destination and error states regardless of pointer/keyboard |
| Compact panel meter | Open navigator; do not unexpectedly shift on a single click. Expanded meter remains separately reachable |
| Expanded meter / terminal header | Open navigator or its explicit expanded action; both subscribe to one confirmed snapshot |
| IBN `SET`, secret code | Reuse validation/code lookup, then request the same service job; retain retro output and show accepted/committed/partial accurately |
| IBN `DMAIL` / local `dmail` CLI | Existing deterministic fictional delta, resolved serially by the service; local only |
| `steins-worldline set` | Service when session available; a compatible file-lock + atomic-write headless path when absent; no effect/audio in headless mode |
| Real graphical D-Mail | **No shift route.** Upstream mail transport/storage/authentication remain independent; an optional future appearance bridge receives only tokens |

Centralising commit resolves concurrency; merely adding a before/after animation around today's separate file writers does not. Test simultaneous requests, caller disappearance, stale expected revisions and service/compositor restarts. Do not automatically re-run a fictional D-Mail text after a lost reply.

## Compositor, accessibility and fallback policy

Prototype the approved ripple in a native KWin effect. KDE documents declarative effect packages, but this does not prove that an arbitrary scene-warp/chromatic shader is exposed by the exact Debian 6.3.6 API. Inspect that version's QML/C++ effect interfaces first. If the approved warp needs a small compiled effect, assess ABI maintenance and update fallback; if it is disproportionate, use the approved Reduced treatment until a proper implementation exists. [KWin effects tutorial](https://develop.kde.org/docs/plasma/kwineffect/).

Never substitute a fullscreen ordinary application that captures focus and call it compositor integration. No input grab, window restart/reparent, fake errors, stored screenshot or mail/document inspection is required. Any transient compositor scene texture stays local and ephemeral; protected or unsupported surfaces use the no-warp fallback. Locked sessions and authentication surfaces get no effect/audio; they apply the latest state without a delayed cinematic replay after unlock. Do not expose a user's home-state service to the unauthenticated greeter.

- **Full:** opt-in only after graphics qualification. One restrained ripple, no repeated flashes; at most 800 ms visual target after preparation. Do not distort readable controls while a drag, accessibility action or sensitive modal interaction is in progress; select Reduced instead.
- **Reduced:** default for the prototype. 180 ms local crossfade/accent change, no spatial motion, chromatic split, flicker or rolling digits. The confirmed meter value changes once at commit. If only immediate presentation is reliable, degrade to Off.
- **Off:** immediate supported state/apply; ordinary focus/selection and a quiet status indicator remain. No cinematic sound is coupled to Off unless a separate sound preference explicitly permits it.
- **Audio:** off by default in this proposal, separate from motion. Honour global mute/volume and notification sound policy; a worldline never unmutes the system. No overlapping shift cues or idle tick loop. See `TRANSITION-SPEC.md` and isolated sample assets.
- **Failure:** compositor/effect absence is nonfatal. Core persistence, shell navigation and application use must remain functional. Drop stale animation schedules on suspend/resume, output changes, locking or client restart.

Initial performance goals are acceptance targets, not measurements: no polling repaint in an idle panel; one event subscription per component; bounded asset cache; no synchronous renderer in UI thread; GPU effect disabled under unqualified software rendering; one queued shift visible at a time. Measure frame times, input latency, memory and idle wakeups with the final assets on the N4500 and a hardware-accelerated test machine. The current 2-vCPU software-rendered VM cannot qualify native effect performance.

## Non-disruptive migration gates

| Gate | Deliverable | Evidence required before replacing a working component |
|---|---|---|
| 0 — owner review | One coherent concept, plain-background identity board, multi-app board, storyboard/tokens | Owner agrees the product direction; no desktop migration performed by this design pass |
| 1 — shell feasibility | Disposable original panel/meter/launcher using candidate A; focused candidate B comparison only if necessary | Tray/task/focus/accessibility, shortcuts, crash recovery, output placement; real runtime captures with wallpaper hidden |
| 2 — model/events | Versioned service/compatibility adapter and all fictional triggers converged | Concurrency, cancellation, write failure, process death, restart and headless compatibility tests; one persisted number |
| 3 — terminal and app cohesion | Maintained terminal-engine spike; decorations/icon/style integration; unchanged real mail client engine | Interactive PTY/IME/accessibility tests; readable real apps/dialogs at target sizes; upstream attribution/security controls preserved |
| 4 — optional effects/audio | Native effect on exact shipped KWin, Reduced/Off controls and optional cue integration | Hardware/VM performance, input continuity, protected surfaces, lock/suspend/multi-monitor and failure modes |
| 5 — packaging/installer | Split native packages, reversible user defaults and versioned experimental ISO | Fresh BIOS/UEFI install, profile migration, package updates/removal, installed reboot, recovery/reference preservation |

Keep the current ISO and `SteinsOS-Test` untouched during proposal work. Store new experiments under `design/` or separately versioned prototype outputs. No automatic edits to the host KDE session, existing user panels, accounts or terminal/mail profiles. Public release still requires the distribution's broader hardware, security/update and installation qualification.
