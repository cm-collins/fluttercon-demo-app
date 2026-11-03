# Stage runbook

How to run the talk from a laptop alone. Both demos play from recordings made on the stage
phone, and the trace walkthrough opens traces captured in the same session. The words are in
the [Demo script](demo-script.md); this page is the setup and the recovery plan.

## What you need

| Item | Where | Check |
|---|---|---|
| Captures folder | `~/fluttercon-captures/2026-10-31-infinix-x6873/` (its README lists every file) | All three videos play to the end |
| **Second copy** of the captures folder | USB drive and cloud storage | Opens on another machine |
| Slides | [`slides/beyond-skia.pptx`](slides/beyond-skia.pptx) in Slide Show mode, with the PDF `local/beyond-skia.pdf` as the fallback. **Install the fonts first:** `slides/local/pptx/fonts/` | Inter shows on every slide; animations run |
| Video player | VLC or mpv, with `slides/local/clips-stage/` open. Clips are numbered in playing order | Full screen, plays smoothly, and you can switch back to the slides quickly |
| Browser with ui.perfetto.dev | Chrome or Edge | Loads with Wi-Fi off once cached (step 4 below) |
| Laptop power, HDMI/USB-C adapter, clicker | Bag | Tested with the venue projector if possible |

The Canvas Thrash video is 253 MB; copy the folder, don't stream it.

## The evening before

1. Open every video once in the player you'll use on stage. Note that `storm-skia-144.mp4`
   reveals at about **0:10**, `storm-impeller-144.mp4` at about **0:04**, and the Canvas
   Thrash steps are at the timestamps in the [Demo script](demo-script.md#1630--canvas-thrash-700).
2. Rehearse the whole talk once against the clock with the videos and traces, not slides
   alone.
3. Charge everything. Turn off notifications and auto-updates on the laptop.

## Thirty minutes before

1. Laptop on power. Display mirrored, or presenter view with the video player and browser on
   the projected screen.
2. **Close Android Studio, the emulator and any `flutter run`.** They use the most memory and CPU on this laptop.
3. Deck open on the cover in Slide Show mode; video player open on `01-broken-chart-8x.mp4`. Practise switching between them.
4. **Perfetto tabs, for Q&A only.** Slide 28 already draws the real frames, so keep these to the
   tabs you may need; each trace holds memory. Open https://ui.perfetto.dev once while online, then open each file
   below in its own tab (drag the file onto the page). Once loaded, the page keeps working
   without a network.

   | Tab | File (under `traces/`) | Prepare |
   |---|---|---|
   | 1 | `perfetto-system/thrash-trace-none.txt` | Pin the app main thread and `1.raster`; zoom to 3–4 frames |
   | 2 | `perfetto-system/thrash-trace-all.txt` | Same pins and zoom |
   | 3 | `dart-timeline/devtools-timeline-8x-broken.perfetto-trace` | Search box ready: `KILN::Thrash` |
   | 4 | `dart-timeline/devtools-timeline-8x-isolate.perfetto-trace` | Search box ready: `KILN::Thrash::grid` |
   | 5 (Q&A) | `perfetto-system/skia-144.txt` | Search `GrGLProgramBuilder::finalize` |
   | 6 (Q&A) | `perfetto-system/impeller-144.txt` | Search `PipelineVK::Create` |

5. Turn Wi-Fi off and click through the tabs once to confirm they still work.
6. Water. Phone on silent.

## Timing cues

| Clock | You should be starting |
|---|---|
| 06:00 | Shader Storm |
| 12:00 | One frame on Vulkan |
| 16:30 | Canvas Thrash |
| 23:30 | Your own pre-compiled pathway |
| 24:30 | Into the traces |
| 32:00 | Takeaways |

Running late: cut demo script line 27 (the fixed trace tab), then shorten Q&A.

## Failure recovery

| If… | Then… |
|---|---|
| A video won't play | Show the screenshot slide for that moment; the numbers are on it. Narrate from the segment script |
| The video player freezes | Restart it; the timestamps are in the demo script. Keep talking from the script meanwhile |
| A Perfetto tab is blank or the page won't load | Switch to the trace screenshot slides for lines 23–29 |
| The projector crops the portrait video | Pause and point at what matters; the lanes and counters are in the lower half |
| Laptop dies | Second copy on USB: slides PDF and videos run on any machine |
| Someone asks for it live | "These are recordings from the stage phone. The scripts in the repo reproduce every number on your phone" |

## If a phone becomes available

Run the two demo segments live from their scripts and keep the recordings as fallback.
Numbers on a different phone will differ: re-run the benches on it first and say which phone
the scoreboard came from. Setup, from what went wrong on the Infinix:

1. Install both profile flavors (`tool/benchmark/README.md`, "Before measuring").
2. **Refresh rate fixed at 120 Hz for Kiln**, checked while Canvas Thrash animates
   (`adb shell dumpsys SurfaceFlinger | grep activeMode`). On Infinix: Screen Refresh Rate →
   High → Customize App Refresh Rate → Kiln and Kiln Skia → 120 Hz.
3. **Auto-rotate off.** **Stay awake on.** Notifications silenced.
4. `adb logcat -G 16M` before running any script.
5. Clear both apps' data right before the talk so the Shader Storm reveals are cold:
   `adb shell pm clear dev.fluttercon.kiln.skia && adb shell pm clear dev.fluttercon.kiln`.
6. Mirror the phone (for example `scrcpy`) and check the mirror keeps up at 8×.
7. Check whether the phone exposes GPU render stages (`adb shell perfetto --query | grep
   gpu.renderstages`). If it does, a GPU trace can close the one gap in the talk.

## After the talk

Return any borrowed phone with its settings restored (refresh rate back to its original mode,
per-app entries removed, apps uninstalled if the owner wants).
