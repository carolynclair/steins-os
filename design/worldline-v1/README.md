# Worldline creative review

This folder is the complete first creative proposal based on Gary/Burrito's latest VM review. **These are editable designs and a read-only viewer, not an installed replacement desktop.** The original distro and test VM have not been changed by this pass.

Start with [the full proposal](WORLDLINE-CREATIVE-PROPOSAL.md).

Quick visual review:

- [Desktop with ordinary applications](boards/multi-app-steins-gate-1920x1080.png)
- [Identity with wallpaper hidden](boards/plain-steins-gate-1920x1080.png)
- [Flagship terminal](boards/terminal-steins-gate-1920x1080.png)
- [Launcher](boards/launcher-steins-gate-1920x1080.png)
- [Navigator and expanded meter](boards/navigator-steins-gate-1920x1080.png)
- [Shift storyboard](boards/shift-storyboard.png)
- [Original icon family](system/icon-sheet.png)
- [Larger text study](boards/large-text-steins-gate-1366x768.png)

Run the native review viewer with:

```sh
/usr/bin/python3 '/home/developer/Documents/ChatGPT/Steins;OS/design/worldline-v1/preview/review.py'
```

It selects boards/scenes/resolutions and previews Full/Reduced/Off shift **timing inside its own window**. This does not change the real desktop, divergence state, VM, accounts or audio. Reduced is the preview default. Unauthored scene/layout combinations are explicitly marked as a nearest available board. Ctrl+1 shows the multi-app board; Ctrl+2 shows the wallpaper-hidden identity board; Escape cancels timing playback.

The sound samples are optional original assets in [engineering/audio](engineering/audio/manifest.json); playback is manual. No sample was automatically played on the host.

## Editable sources

- `build_boards.py`: code-native SVG layout source and PNG exporter.
- `boards/*.svg`: editable vector UI compositions; scene links point to `../art/`.
- `art/`: original generated scene PNGs, full image prompts, dimensions and provenance; existing emblem copy.
- `system/`: semantic tokens, contrast report, original SVG icons, construction generator and license.
- `apps/`: terminal/navigator/ordinary-application interaction specifications.
- `engineering/`: shell alternatives, staged service/event proposal, transition spec and original audio generator.
- `preview/review.py`: native read-only viewer, using the existing PySide6 Qt Widgets modules.
- `evidence/`: design-asset and viewer validation, explicitly separate from real-OS evidence under the project's older `evidence/plasma-prototype/`.

To rebuild the drawings, run `python3 design/worldline-v1/build_boards.py` from the project root. It uses the existing `steins-os-builder:trixie` container as a non-root SVG renderer and writes only this design folder. It does not install packages or build an ISO. The viewer smoke check is `QT_QPA_PLATFORM=offscreen /usr/bin/python3 design/worldline-v1/preview/review.py --smoke`.

New design code and original icon family are MIT. Scene/audio assets use their recorded CC-BY-4.0 attribution to Steins;OS contributors. Existing emblem and upstream fonts/apps retain their existing licenses. Native generated scenes are 1672×941; board target size is a layout export, not evidence of 4K source art or runtime qualification.
