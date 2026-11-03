# Stage runbook

How to run the talk. The demos run live on a mirrored phone, from their scripts. The recordings made
on the Infinix test phone are the fallback, and every `>>> DEMO` cue in the speaker notes names its clip. The words are in the
[Demo script](demo-script.md); this page is the setup and the recovery plan.

## What you need

| Item | Where | Check |
|---|---|---|
| Demo phone | Both profile flavors installed, 120 Hz, logging Vulkan (see [Set up the phone](#set-up-the-phone)) | `adb logcat` shows `Using the Impeller rendering backend (Vulkan)` |
| USB cable and `scrcpy` | Bag and laptop | The mirror keeps up at 8× |
| Captures folder | `~/fluttercon-captures/2026-10-31-infinix-x6873/` (its README lists every file) | All three videos play to the end |
| **Second copy** of the captures folder | USB drive and cloud storage | Opens on another machine |
| Slides | [`slides/beyond-skia-dark.pptx`](slides/beyond-skia-dark.pptx) in Slide Show mode, with the PDF `local/beyond-skia-dark.pdf` as the fallback. Use `beyond-skia.pptx` in a very bright room. The fonts are embedded; install `slides/local/pptx/fonts/` too, as a backup | Inter shows on every slide; animations run |
| Video player | VLC or mpv, with `slides/local/clips-stage/` open. Clips are numbered in playing order | Full screen, plays smoothly, and you can switch back to the slides quickly |
| Browser with ui.perfetto.dev | Chrome or Edge | Loads with Wi-Fi off once cached (step 4 below) |
| Laptop power, HDMI/USB-C adapter, clicker | Bag | Tested with the venue projector if possible |

The Canvas Thrash video is 253 MB; copy the folder, don't stream it.

## The evening before

1. Set up the phone, below, and run the backend check.
2. Rehearse the whole talk once against the clock, with the live demos and the votes, not slides alone.
3. Open every clip in `slides/local/clips-stage/` once in the player you'll use, so the fallback is ready.
4. Charge everything. Turn off notifications and auto-updates on the laptop.

## Set up the phone

Numbers on a different phone will differ. Re-run the benches on it, or say the scoreboard came from your test phone.

1. Install both profile flavors (`tool/benchmark/README.md`, "Before measuring").
2. **Check the backend.** Clear the log, open **Kiln Impeller**, then read the line the engine wrote:

   ```text
   adb logcat -c
   adb logcat -d | grep "Impeller rendering backend"
   ```

   It must say `(Vulkan)`. If it says `(OpenGLES)`, the Vulkan parts of the talk don't match this phone: use another phone, or run the demos from the recordings. [Fact check](fact-check.md#which-backend-an-android-phone-gets) lists the reasons and the commands to find which one applies.
3. **Refresh rate fixed at 120 Hz for Kiln**, checked while Canvas Thrash animates
   (`adb shell dumpsys SurfaceFlinger | grep activeMode`). On Infinix: Screen Refresh Rate →
   High → Customize App Refresh Rate → Kiln and Kiln Skia → 120 Hz.
4. **Auto-rotate off.** **Stay awake on.** Notifications silenced.
5. `adb logcat -G 16M` before running any script.
6. Mirror the phone (for example `scrcpy`) and check the mirror keeps up at 8×.
7. Check whether the phone exposes GPU render stages (`adb shell perfetto --query | grep
   gpu.renderstages`). If it does, a GPU trace can close the one gap in the talk.

## Thirty minutes before

1. Laptop on power. Display mirrored, or presenter view with the phone mirror, video player and browser on
   the projected screen.
2. **Close Android Studio, the emulator and any `flutter run`.** They use the most memory and CPU on this laptop.
3. Clear both apps' data so the Shader Storm reveals are cold, then run the backend check again. Don't open Shader Storm after this, because any reveal fills the cache:
   `adb shell pm clear dev.fluttercon.kiln.skia && adb shell pm clear dev.fluttercon.kiln`
4. Deck open on the cover in Slide Show mode, phone mirror beside it, and the clips folder open as the fallback. Practise switching between them.
5. **Perfetto tabs, for Q&A only.** Slide 28 already draws the real frames, so keep these to the
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

6. Turn Wi-Fi off and click through the tabs once to confirm they still work.
7. Water. Your own phone on silent.

## Timing cues

Estimated from the [run of show](demo-script.md#run-of-show). Replace them with your own times after the rehearsal.

| Clock | Slide | You should be starting |
|---|---|---|
| 01:15 | 3 | How Flutter draws |
| 04:45 | 6 | Before: Skia |
| 07:45 | 8 | Now: Impeller |
| 13:15 | 13 | The proof: Shader Storm |
| 17:00 | 16 | Inside a frame |
| 21:00 | 19 | What Impeller didn't fix: Canvas Thrash |
| 28:15 | 26 | Your own shader |
| 29:15 | 27 | Prove it: DevTools and Perfetto |
| 33:00 | 30 | Finish |
| 34:30 | 33 | Q&A |

Running late: say slide 10 in one sentence, give the answers on slides 24 and 28 without a vote, then shorten Q&A. Keep slides 11, 23 and 29, because they carry promises from the abstract.

## Failure recovery

| If… | Then… |
|---|---|
| The phone logs `(OpenGLES)` | Use another phone, or run the demos from the recordings. Don't describe the live run as Vulkan |
| The phone or the mirror fails during a demo | Play the clip named in the `>>> DEMO` cue and carry on. Say it's a recording from your test phone |
| A clip won't play | Stay on the slide and narrate from the segment script; the numbers are on the slide |
| The video player freezes | Restart it. Keep talking from the script meanwhile |
| A Perfetto tab is blank or the page won't load | Use slide 28, which draws the real frames |
| The projector crops the portrait phone mirror | Pause and point at what matters; the lanes and counters are in the lower half |
| Laptop dies | Second copy on USB: the slides PDF and the videos run on any machine |
| No phone, and someone asks to see it live | "These are recordings from my test phone. The scripts in the repo reproduce every number on your phone" |

## After the talk

Return any borrowed phone with its settings restored (refresh rate back to its original mode,
per-app entries removed, apps uninstalled if the owner wants).
