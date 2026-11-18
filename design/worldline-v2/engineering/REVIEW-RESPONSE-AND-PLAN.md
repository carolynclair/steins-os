# V2 response and prioritised polish plan

The review's priorities are sound: preserve the illustrated worlds and functional work, give the terminal and panel a stronger identity, and distinguish real implementation from previews. This pass refines those surfaces, exposes the actual engineering boundary and fixes small verified defects without migrating the original working environment.

## Response to the recommendations

| Recommendation | Response and refinement |
|---|---|
| Make the terminal a flagship | **Agree.** V2 develops a shared instrument header, a stronger session/tab layout and deliberate floating/maximised/tiled states. These are previews. The actual engine tested today is Konsole; a new maintained-component frontend still needs an approved implementation spike and compatibility matrix |
| Make startup more dynamic | **Agree with a constrained scope.** Preview signal emergence/assembly/brief stabilisation, with reduced/static/silent alternatives. Do not force a fixed animation delay on fast boot or move audio/authentication dependencies into initramfs. The existing Plymouth theme already has a small activity pulse; its logo and handoff are not cinematic |
| Explore logos without replacement | **Agree.** Present the current emblem with three original candidates, monochrome and small-size examples. The reference images inform qualities, not traced geometry. Current branding remains the default pending Chairman selection |
| Coordinate worldline shifts | **Agree.** The shared persisted number is a useful base, but legacy direct writes and sequential appearance steps do not yet constitute one staged transaction. The current source fix consumes Reduced/Off in the expanded meter only; it is not a native transition implementation |
| Audit audio rather than assume | **Agree.** Original WAVs exist; custom cue wiring does not. The V2 VM has no sound cards and only a null sink. Keep audio optional/off, respect mute and do not label a silent transport as a failed product cue before the transport exists |
| Establish one visual grammar | **Agree.** Use the wallpaper-hidden board, common controls/icon geometry and practical panel hierarchy as the comparison. Preserve daily usability and semantic/error colours across worlds. Third-party app layouts keep honest supported-integration limits |
| Continue original anime art | **Preserve first.** Akihabara/Hinamizawa/coastal scene files stay byte-preserved. Finish the remaining original worlds after the shell/terminal direction settles; no photorealistic replacement or extra decorative feature work was needed to address this review |
| Repeatable safe VM testing | **Implemented a separate validation path.** Cold checkpoint copies the installed prototype overlay/NVRAM, pins the immutable QA backing, and creates retained reset forks. The original prototype and libvirt guest are separate. New evidence is labelled as tests of the actual inherited desktop |
| Engineer-led low-risk fixes | **Done within scope.** Meter preferences stop scramble motion for Reduced/Off and invalidate stale callbacks; verified headlessly/in real GTK. Cold reset revealed an early-plasmashell startup race, now corrected in source with bounded, stale-safe retries and 17 private-bus tests. Mode-aware Plymouth wording is corrected in source. Fresh patched boot and controlled real-shell recovery passed in the fork; Plymouth deployment remains unqualified. No host packages, new terminal libraries or GPU/audio devices were installed |

## Priorities, dependencies and expected outcomes

| Priority | Task | Dependency / approval gate | Expected evidence |
|---|---|---|---|
| P0 — preserve truth and fallback | Keep inventory, design labels, cold baseline and retained runs; finish shutdown/reset ledger | Existing tools only; no redesign migration | Exact artifact hashes, real captures, zero accidental edits to original guest/ISO |
| P0 — small correctness | Retain meter Reduced/Off/stale-frame fix; qualify bounded startup recovery; qualify Plymouth mode text in a future package/initramfs | Meter source/fork checks and 17 service contracts pass; retry passed fresh boot and a controlled real-shell outage/recovery; Plymouth needs separately built guest package and real boot/prompt/shutdown check | No stale digits or indefinitely cached early-shell failure; correct startup/shutdown/reboot text; normal prompt fallbacks |
| P1 — terminal identity decision | Review floating/maximised/tiled and wallpaper-hidden terminal concept | Chairman approves the visual direction before broad implementation | One approved layout/interaction contract, with readable output and bounded status chrome |
| P1 — maintained terminal spike | Compare original frontend around QTermWidget 6 with KonsolePart if appropriate, preserving Konsole fallback | **New dependencies/major frontend change require approval**; use isolated build/guest scope, not Parrot changes | Real PTY, Unicode/IME, selection, resize/process continuity, SSH/TUI/screen-reader and scaling results on the new frontend |
| P1 — original panel/meter/navigation | Build the compact instrument and anchored navigator using maintained shell services | Isolated reversible experiments using existing dependencies are within the review; broad deployment/migration or new dependencies need approval | Wallpaper-hidden runtime capture; task/tray/focus/keyboard/crash-recovery/large-text checks |
| P2 — unified shift pipeline | Route GUI, meter, IBN/local D-Mail through a versioned staged request path | **Meaningful service architecture change requires approval**; preserve legacy/headless compatibility | Single writer/job ordering, failure/cancel/restart tests; confirmed state distinct from selected destination |
| P2 — native optional effects | Qualify the restrained ripple on exact shipped KWin, with Reduced/Off fallback | Approved effect implementation/dependencies; separately reviewed acceleration capability | Input/app continuity and real renderer/frame-time evidence; no fullscreen focus-stealing substitute |
| P2 — optional audio | Add deliberate output-only VM transport, then bounded user-session cue dispatcher | Use a separate disposable run; approval applies to new dependencies or broader deployment, not every reversible output-device experiment. No host microphone, passthrough or automatic unmute | Audible synthetic fixture, mute/volume/no-sink/repeated-event/error/login tests; silence never blocks boot/shift |
| P3 — session/application finish | Package login/decorations/icons, notifications/settings/file manager and six scenes | Selected logo and approved integration surfaces; secure auth design | Authentication/error/layout/AT tests, coherent real apps at target sizes, user-profile preservation |
| P3 — release artifact | Build separately versioned Plasma ISO and migrations | Broad desktop/package migration approval; earlier gates pass | Fresh BIOS/UEFI supported installs, installed reboot, update/removal/profile/rollback matrix on the exact ISO |

No new dependencies were installed for this review. Existing Konsole/Plasma behaviour is the functional baseline while the creative and architectural choices are reviewed. Approval of a logo does not automatically approve a terminal engine, service rewrite, audio device or desktop migration.

## Requested deliverables map

1. **Implementation inventory:** [IMPLEMENTATION-INVENTORY.md](IMPLEMENTATION-INVENTORY.md), with working/partial/mock-up/unimplemented rows and fresh V2 scope.
2. **Review response:** the recommendation table above.
3. **Polish plan:** the priority/dependency/evidence table above.
4. **Logo concepts:** [current plus alternatives](../identity/LOGO-REVIEW.md) and [comparison sheet](../identity/comparison-sheet.png); existing mark retained.
5. **Terminal refinement:** [floating](../boards/terminal-floating-steins-gate-1920x1080.png), [maximised](../boards/terminal-maximised-steins-gate-1920x1080.png) and [tiled](../boards/terminal-tiled-steins-gate-1920x1080.png) previews, with actual inherited-terminal tests kept separate in the evidence inventory.
6. **Boot/login concept:** [boot storyboard](../startup/boot-storyboard.png), [sequence spec](../startup/BOOT-SEQUENCE.json), [login preview](../boards/login-steins-gate-1920x1080.png) and [integration audit](../startup/BOOT-AUDIO-AUDIT.md). Review-window animation is not a newly booted Plymouth/SDDM pipeline.
7. **Audio audit:** the startup/audio audit and actual guest no-card/null-sink inventory; sample existence is separated from integration.
8. **VM environment:** [VM-VALIDATION-PLAN.md](VM-VALIDATION-PLAN.md), `vm_lab.py`, `push_guest.py` and the real V2 fork's evidence.
9. **Verification:** helper unit tests; source/meter flow checks; 21/21 actual runtime checks; PTY/resize/clipboard/basic-vi/lock results; real screenshots; final shutdown/reset results in the lead engineer's completed ledger.

## Boundaries on the current results

The new flagship terminal, original shell, logo selection, cinematic boot/login and native worldline effect are not installed by this pass. Meter motion handling is a verified small runtime change in the fork; it is not the complete 800-ms shift. Plymouth wording is a verified source correction, not proof of an updated booted initramfs. SSH/Zsh/Neovim and physical sound are untested because the required capabilities are absent; the basic `vi` test does not imply a broader editor matrix. Those limits are stated so the next approval is concrete and evidence-based.
