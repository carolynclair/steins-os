# Worldline shift — motion and audio specification

**Proposal v1.** Timings below describe a future coordinated shell/compositor interaction. They are not measurements or implemented service events. Assets in `audio/` are quiet original synthetic previews, not configured system sounds. No sound was played on the host during this work.

The change has an immediate input acknowledgement, an optional preparation state, then a finite visual sequence. Never hide slow preparation behind a frozen desktop or keep an animation running indefinitely. The new number is an ephemeral destination preview until the service commits it; all compact, expanded and terminal-header displays share that distinction.

## Full sequence: target 800 ms after assets are ready

| Stage | Interval | Visual/interaction specification | Optional sound |
|---|---:|---|---|
| Request/preparation | Before t=0, variable | Origin control highlights immediately; service accepts/prepares or reports failure. Current divergence stays confirmed. If preparation is visible, show a small progress state and Cancel; do not block typing/windows | None; failure has no success cue |
| 1. Activation | 0–90 ms | Compact tubes warm slightly; origin accent becomes solid. Source and destination are readable. No desktop dim/flash or modal overlay | `activation.wav`, one warm, soft electronic touch |
| 2. Instability | 90–220 ms | Eight glyph cells make one restrained roll/crossfade towards the destination; maximum one value change per cell in the initial design. Keep foreground text and mouse unaffected; no random rapid digit loop | `meter.wav`, one short resonant texture, not one click per digit |
| 3. Reality distortion | 220–400 ms | One shallow elliptical ripple travels from the compact meter's shell region. Proposed peak displacement ≤3 logical px, optional chromatic offset ≤1 px only at ripple edge; no flashing or full-scene repeated judder. Targets need real KWin evaluation | No additional transient; let the meter texture decay |
| Commit boundary | 400 ms target | Persist canonical divergence once. Change shared shell tokens and stage supported wallpaper/application appearance. Emit confirmed state. Exact cross-process frame simultaneity is not promised | No success cue yet |
| 4. Transformation | 400–620 ms | Destination environment crossfades in; surfaces use destination accent. Ripple resolves; text/controls remain legible. Unsupported native apps retain their reliable theme and are reported honestly | Optional very soft airy tail, included only in the composite exploration |
| 5. Stabilisation | 620–800 ms | Tubes settle at the one confirmed value. Temporary origin/destination hint recedes. Return to steady idle without a persistent banner. Announce the completed worldline once to assistive technology | `stabilise.wav`, one soft descending/resolving pair only on successful supported apply |

Only animate supported surfaces through the native compositor/shell path. The scene should stay recognisable throughout. An ordinary app-sized scene mockup may illustrate the proposal, but must be labelled and never mistaken for a working compositor effect.

The proposed meter highlight and ripple are visual aspirations. Tune amplitude/duration downward if frame time or legibility fails. Do not stretch the timeline to hide loading. A partial apply suppresses success audio, settles the confirmed number and offers a quiet explicit Reapply action.

## Reduced and Off

| Policy | Timeline | Required treatment |
|---|---:|---|
| Reduced | 0–180 ms | At commit, replace the digits once; crossfade local accent/wallpaper treatment. No rolling digits, spatial warp, chromatic separation, flicker or moving scene. Keep a readable text success/partial state |
| Off | Immediate presentation | Persist/apply using the reliable adapter path. Confirm state without a cinematic sequence. A normal focus/selection indicator is sufficient |

Actual appearance operations may take longer than these visual targets. Their outcomes remain observable; the shell never claims an unacknowledged native surface applied in 180 ms. Locked/suspended, software-rendered or unsupported-compositor cases use the reliable Reduced/Off path without replaying a queued cinematic on recovery.

## Audio policy and previews

Audio is a separate opt-in preference, initially **off**. Expose sound enable, volume and preview controls in one worldline setting; preserve global mute and system event sound policy. No audio is essential to understand success/failure. Avoid earcons resembling security alarms, chat pings or real error notifications. No voices, songs or franchise audio.

The samples are synthesized by `generate_audio.py` with Python's standard library. They are 48 kHz, 16-bit mono PCM. Raised-cosine attacks/releases avoid discontinuities. Per-file peak and RMS dBFS, duration and SHA-256 are in `audio/manifest.json`. These figures are digital levels, **not calibrated playback loudness/SPL or a safety guarantee**; the user's sound system controls playback volume. Preview at a user-selected level. The combined exploration is limited to a quiet −26 dBFS peak.

| File | Intent | UI use |
|---|---|---|
| `activation.wav` | 90 ms warm electronic touch | Once after the prepared visual sequence starts |
| `meter.wav` | 160 ms soft resonant tube movement | Once for the whole meter; never a repetitive typing sound |
| `stabilise.wav` | 180 ms resolving pair | Successful finish only; no cue on partial/failed apply |
| `shift-preview.wav` | 800 ms assembled exploration | Design review sample only, not an installer/default system sound |

The four samples are a restrained first exploration. No ambient loop, notification replacement or login/shutdown sound is shipped by this proposal. A future audio implementation must cancel stale cues and avoid stacking queued jobs' sounds. Disable or reduce cues if they interfere with assistive output or the user's chosen accessibility/sound preferences.

### Six worldline ambience directions — optional, future assets

| Worldline | Original sonic atmosphere | Constraints |
|---|---|---|
| Alpha | Sparse laboratory room tone; soft electronics and distant ventilation | No constant high-pitched oscillator; no audible fake fault alarms |
| Steins Gate | Open-window summer city, soft rooftop wind and distant electronics-district texture | No intelligible voices, branded shop jingles or copyrighted music |
| Hinamizawa | Gentle rural summer air, sparse original cicada-like texture and foliage | Peaceful by default. Horror/anomaly cues remain separate explicit opt-in work; never a hidden scare |
| Hitogashima | Long soft coastal wash and breeze | Avoid repetitive crash peaks, piercing gulls or audible looping seams |
| Lugunica | Garden air, distant water and occasional soft original resonant material | No musical tune borrowed from a soundtrack; no implied gameplay alert |
| Mitakihara | Spacious quiet city/glass atmosphere with low distant movement | No real transit announcements or recognisable station melodies |

Ambience should default off, use long non-repetitive low-density material and pause under conferencing/recording where supported through an explicit user policy. These are creative directions, not generated loops or implemented application detection.

## Acceptance and failure storyboard variants

- Pointer, keyboard, IBN `SET`, secrets and fictional D-Mail produce the same accepted/ready/commit/finished semantics. Compact meter clicking simply opens navigation.
- Cancel before commit: return to the old confirmed number without a completion cue. After commit: report that it already changed; offer another deliberate shift instead of pretending cancellation undid it.
- Asset preparation failure: no number change, no ripple, no success sound; origin shows the real error with Retry.
- Compositor/effect absent: apply via Reduced/Off without a fullscreen application pretending to be the compositor.
- Partial application: confirmed new number remains, affected surfaces are named in a recovery affordance; no false complete state or success cue.
- Service restart: discard old animation/audio schedules, read canonical state and reapply quietly. No queued D-Mail is replayed automatically.
- Lock/suspend/output change during a shift: stop cinematic presentation, retain truthful canonical state and finish reliable appearance recovery without interrupting user applications.

Test frame pacing, input continuity, screen-reader announcements, large text, mixed DPI, video/fullscreen, keyboard-only paths, render failures, 2-vCPU software graphics and qualified hardware graphics. None of those new effect tests are asserted complete by this document.
