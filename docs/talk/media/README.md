# Talk media

Video and backup assets for the live presentation. Keep offline copies on the laptop
(stage runbook checklist).

## Skia → Impeller concept clip

| | |
|---|---|
| **File** | [`skia-to-impeller-concept.mp4`](skia-to-impeller-concept.mp4) |
| **Format** | MP4, 720p, 16:9, ~15 s, no on-screen text |
| **When** | Start of **How we got here** (~03:00), **before** the timeline slide |
| **Purpose** | Hook the room: JIT vs AOT as a story, not a diagram |

### What the metaphor shows

| Act | Visual | Maps to |
|---|---|---|
| Stuttering car + blacksmith on track | Parts forged mid-race, car stops every time | Skia generates a shader and the driver compiles it **during** a frame |
| Warm forge, kiln, racks of finished parts | Work done before the green light | Shaders compiled at **engine build time** (`impellerc`) |
| Same car, one smooth lap, light trails | Steady motion | Predictable frame cost; no first-use compile stutter |

Say clearly that this is a **metaphor**. The next clip (device recording) is the **proof**.

### Suggested narration (optional voice-over)

Play in silence and speak live, or embed a voice-over in your slide tool.

1. *(Stutter)* "Every new effect, the engine stops to forge a part."
2. *(Forge)* "Impeller fires everything in the kiln first."
3. *(Smooth lap)* "Then the race is only about how much work you ask for each frame."

### Embed in slides

**Google Slides:** Insert → Video → Upload → select this file. Set to play on click (or
automatically once). Use full slide or letterbox; dark room reads better with a black slide
behind the video.

**Keynote / PowerPoint:** Insert → Video from file. Prefer "Play Full Screen" for the
concept clip only.

**Reveal.js / HTML deck:** `<video src="skia-to-impeller-concept.mp4" controls playsinline></video>`
(copy the file next to the deck or use a relative path from `docs/talk/media/`).

**OBS (stream backup):** Add as Media Source; trigger from a hotkey if mirroring fails.

### Pair with the device clip

| Order | Asset | Role |
|---|---|---|
| 1 | `skia-to-impeller-concept.mp4` (this file) | Attention, concept |
| 2 | Timeline slide | Dates and names |
| 3 | `storm-skia-144.mp4`, `storm-impeller-144.mp4` | Real Flutter first-use stutter, Skia vs Impeller |

## Stage-phone recordings

Recorded on the Infinix X6873 on 2026-10-31. They are too large for git (the Canvas Thrash
clip is 253 MB) and live in `~/fluttercon-captures/2026-10-31-infinix-x6873/videos/`, with a
README that lists timestamps. Keep a second copy on USB and in cloud storage.

| File | Length | Used in |
|---|---|---|
| `storm-skia-144.mp4` | 27 s | Shader Storm: Skia cold reveal 1,954 ms, repeat 21 ms |
| `storm-impeller-144.mp4` | 27 s | Shader Storm: Impeller cold reveal 148 ms, repeat 39 ms |
| `thrash-impeller-stage.mp4` | 1:33 | Cold open (from 0:19) and the whole Canvas Thrash segment |

Where each is played: [Demo script](../demo-script.md#run-of-show).
