# Claude UI changes — Codex runtime review, 2026-10-31

**2026-11-01 update:** the reviewed UI is now embedded in the tested 0.1.0-8 packaged ISO. See VALIDATION.md for current artifact results. The report below retains the original review's overlay/preview provenance.

Imported `/home/developer/Downloads/steins-os-claude-ui-changes.zip` after checking it against the outgoing source snapshot. No paths removed. Earlier local versions are preserved in `handoff/pre-claude-ui-merge-2026-10-31.zip`.

## Requested checks

| Check | Observed result |
|---|---|
| Calamares stylesheet and pages | Loaded in real Debian Calamares 3.3.14, UEFI live XFCE, 1280x800. Reviewed Welcome, Location/map, locale dialog, Keyboard, automatic/manual partition views, partition dialogs, Users/error, Summary, final confirmation, Install and Finish. Fixed the issues below. |
| Slideshow | Automatically advanced through the four original slides during an actual installation, which completed. Final background/progress corrections also rendered in a real Calamares preview. |
| Welcome links | Support, known-issues and release-notes links are absent on the completed welcome page with the three URL strings blank. |
| GTK selection | Real Mousepad: base theme amber/dark selection and per-user worldline dark-amber/white selection both readable. |
| GTK focus | Real Mousepad entry focus and real About button focus tested. Found the dark-variant hook bug below; after correction the button's computed style is solid, 2px, RGBA(0.913725, 0.603922, 0.270588, 1). |
| About colours | New screenshots are from Steins;OS using Steins-Lab. Overview and Worldlines reviewed; six rows fit. Your sandbox light-theme images remain correctly identified as layout evidence. |

## Confirmed issues and fixes applied by Codex

1. **Blank keyboard preview.** Reproduced with and without the QSS. `ckbcomp` was absent. Installed Debian `console-setup` in the VM and the key labels appeared. Added it to the image package list and prerequisite check. No Calamares code fork.
2. **Black partition legends on dark background.** Calamares 3.3.14 `PartitionLabelsView::drawLabel()` uses hard-coded black/grey pens, so normal QSS text colour cannot fix it. Added a white backing only to `PartitionLabelsView`. Verified before/after legends in automatic/manual partitioning and Summary. Its secondary size labels retain upstream grey; this is not a claim that every upstream painted element meets WCAG AA.
3. **Faint checkbox/radio indicators.** Encryption, flags and selection states were difficult to distinguish. Added explicit indicator borders plus original SVG check/dot assets. Verified checked/unchecked controls on the actual partition page and the checked restart control on Finish.
4. **Progress percentage contrast.** At 76% the light percentage was painted over bright amber (1.77:1). Changed the fill to `#8a521e` (4.91:1 with `#e7e2d6`) and added a contrast regression. Verified the final style at 75% in Calamares.
5. **White slideshow frame.** The upstream `Slide` component reserves margins; the QQuickWidget white clear colour showed outside each dark slide. Added a background rectangle to the Presentation root. Verified the corrected frame in Calamares.
6. **Dark GTK apps missed the hook overrides.** The shipped settings prefer the dark variant, which loads `gtk-dark.css`. The hook previously changed only `gtk.css`. It now appends the same selection/focus rules to both variants. Used explicit outline longhands; retested the computed style after GTK's transition settled. No user GTK CSS is overwritten by this hook.

Also removed the redundant `branding.desc` top-level `stylesheet` key: this Calamares version loads `stylesheet.qss` by filename convention. The file copy is what activates it. Installer modules, partitioning logic, authentication wrapper and final disk confirmation are unchanged.

## Evidence and provenance

- `evidence/vm/ui-calamares-welcome.png`: real welcome page, three links absent.
- `ui-calamares-location.png`, `ui-calamares-locale-dialog.png`, `ui-calamares-keyboard-fixed.png`: map, locale selection, restored key labels.
- `ui-calamares-partitions.png` versus `ui-calamares-partitions-fixed.png`: reproduced black legend and its corrected backing.
- `ui-calamares-erase-preview.png`, `ui-calamares-encryption-controls.png`: final indicators and partition legend states.
- `ui-calamares-users.png`, `ui-calamares-summary.png`, `ui-calamares-confirm.png`, `ui-calamares-finish.png`: actual installation path, including completion.
- `ui-calamares-slide-1.png`, `ui-calamares-slide-2.png`, `ui-calamares-slide-3.png`, `ui-calamares-progress.png`: actual installation slideshow before frame/progress corrections. The filename numbers are capture labels; read the slide text for identity.
- `ui-calamares-slide-fixed-1.png`, `ui-calamares-slide-fixed-worldlines.png`, `ui-calamares-progress-fixed.png`: corrected native Calamares renderer. These screenshots say **UI preview**: a temporary configuration runs only `sleep 1` and `sleep 75`, weighted to hold progress at 75%. They are renderer tests, not a second installation. Production sequence was never changed.
- `ui-gtk-mousepad-selection.png`, `ui-gtk-base-selection.png`, `ui-gtk-mousepad-focus.png`, `ui-gtk-about-focus-fixed.png`, `ui-about-worldlines-dark.png`: real GTK runtime captures.
- `evidence/claude-ui-runtime.txt`, `claude-ui-gtk-runtime.txt`: native runtime/style logs. Upstream QML deprecated-signal-parameter and finished-module configuration warnings were observed; no stylesheet/QML loading failure in the successful runs.
- `evidence/ui-review/`: source/archive hashes and temporary preview/smoke-test scripts. Screenshots and tests are VM-only; host desktop settings were untouched. VM and transfer server shut down after testing.

## Validation and limits

Source checks pass. All 49 worldline tests pass. UI suite: 19 tests, 18 passed and the optional Xvfb test skipped on the host; real GTK construction, focus and Escape were separately exercised in the VM. Both artwork generators reproduce all checked-in SVG/JSON bytes.

The source was applied to a live VM booted from ISO SHA-256 `5d19a142470a3eadc254f445a9c7fcad572eac47c08e69be069f2b621e60a98a`. The reviewed hook ran there; Calamares installed that ISO's filesystem to a disposable 32 GiB disk. The new source UI changes are **not yet rebuilt into the ISO**, and that installed disk has not been boot-tested in this review. The final preview specifically verifies the later QML/progress corrections. Other resolutions/scales, long translations, hardware and an exhaustive accessibility audit remain outside this run.
