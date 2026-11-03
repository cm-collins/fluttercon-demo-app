# Talk deck

The slides for *Beyond Skia*: 30 slides plus 2 backup tables. The spoken words and the demo cues are
in the speaker notes and the [Demo script](../demo-script.md).

The finished presentation lives outside the codebase, in `~/Documents/fluttercon/`:

| File | What it is |
|---|---|
| `Beyond-Skia.pptx` | **The stage deck**, dark. It matches the demo app |
| `Beyond-Skia.pdf` | Still copy, the fallback |
| `light-version/` | The same deck, light, for a very bright room |
| `demo-clips/` | The demo recordings, numbered in playing order, for when there is no phone |
| `fonts/` | Inter, Inter Display and JetBrains Mono. Embedded in the decks; install them too on the presenting machine, as a backup |

Animations only run in Slide Show mode in PowerPoint or LibreOffice Impress, never in a file preview
such as a code editor extension.

After any layout change, run `check_layout.py` on the deck: it checks every size against the scale, and looks for text that wraps, overflows or collides. `build_pptx.py` writes the decks to `~/Documents/fluttercon/`. Rebuild with `python3 docs/talk/slides/build_pptx.py` (needs `python-pptx`, Pillow, numpy for the mountain, and the photo, logos, fonts and images in `local/`). Colours come from the
`THEMES` table, so one edit restyles a whole deck. Speaker notes live in `speaker_notes.json`, one entry per slide; the [Demo script](../demo-script.md) repeats them, so change both.

`index.html` is an outdated browser draft, kept for reference and marked with a banner. It has claims that the
[Fact check](../fact-check.md) corrects, so don't present from it.

## Design rules

The slides support the speaker and the demo app. They don't replace them.

- **One message, one visual.** A title, one picture, diagram, number or code sample, and nothing else. No subtitles, captions or small labels competing for attention. Everything else goes in the speaker notes.
- **A few quiet words only where honesty needs them.** "Illustration", "Emulator" or the test phone, on the bottom line.
- **Real material first.** Pictures generated from the demo's own code and traces, real numbers and real code. See "Where the pictures come from" in the [Fact check](../fact-check.md).
- **Big-screen pictures.** Rendered at 2560 × 1440 in `visuals/`, on dark slides in both decks.
- **Animations explain.** Each one shows one concept beside one sentence that states it. They start and loop by themselves, with Morph between slides and a fade in older PowerPoint.
- **No decoration.** No cards, icon tiles, gradient fog, shadows, section labels or progress markers. Blocks appear only in diagrams and data.
- **Grid.** 72 px side margins and a 12-column grid with 32 px gutters (`gx` and `gw` in `build_pptx.py`). The title starts at y=44. Content runs from y=160 to y=636. The tag and the logo share the bottom line at y=664. Never put text over a video: a slide show may draw video on top of everything.
- **Blocks.** `plate()` is the deck's one block: a flat top with a thin darker edge below, so it reads as a solid layer, like the engine stack on slide 6. Cyan, ember, plain, or dashed for what isn't there.
- **Type.** One scale, with each size doing one job:

  | Size | Job |
  |---|---|
  | 104 | Statement titles and the scoreboard |
  | 72 | Big numbers, the verbs on slide 3, and the title on slide 30 |
  | 60 | Slide titles and key statements |
  | 36 | Section headings and supporting statements |
  | 28 | Body text, and the one sentence under an animated title |
  | 24 | Code and dense labels |
  | 20 | Quiet labels and table headers |
  | 18 | The tag on the bottom line |

  Inter Display Medium for headlines, tracked tight, Inter and Inter Medium for text, JetBrains Mono for code and thread names. Bold is never used, because the weights are their own families.
- **Fonts.** All four are embedded in each `.pptx`, so a machine without them still shows them in PowerPoint for Windows or Mac. Keynote and Google Slides ignore embedded fonts, so use the PDF there, or install the fonts.
- **Colour.** Warm paper and ink in the light deck, near-black and warm white in the dark deck, and a grey light enough to survive a projector. Two colours have fixed meanings: ember is the cost, or late; cyan is Impeller, or on time.
- **Tables.** Native and editable. A quiet header and a hairline under each row, with no fills.
- **Numbers.** Only the Infinix measurements count as evidence. Emulator screens are labelled and quote no timing. Anything drawn rather than measured is labelled "Illustration".

## What is in git and what is not

The finished decks are not in git: they contain the speaker photo and the FlutterCon logo, and the repository is public. `local/` is ignored too. It holds the speaker photo, the FlutterCon logo (from the organisers' `droidconKE/flutterconKEApp` repo),
the videos, screenshots and the PDF backup. **Copy the whole `slides` folder and the concept
video to a USB drive**; from a fresh clone, `local/` has to be restored from that copy.

| Path | Contents | In git |
|---|---|---|
| `build_pptx.py` | Builds the decks | Yes |
| `check_layout.py` | Checks font sizes, fit and collisions | Yes |
| `make_mountain.py` | Renders the mountain on slide 11, as original artwork | Yes |
| `visuals/` | Pages and scripts that render the other pictures and the animated explainers (`capture.py`), from the demo's code and traces | Yes |
| `speaker_notes.json` | The speaker notes, one entry per slide | Yes |
| `index.html`, `deck.css`, `deck.js` | Outdated browser draft and engine, marked with a banner | Yes |
| `trace-data.js` | Real frame timings from the stage phone's traces | Yes |
| `fonts/` | Outfit and JetBrains Mono, with their open font licences | Yes |
| `local/` | Source photo and logos, videos, installable fonts, screenshots, QR code, PDF, previews | **No** |
| `../media/skia-to-impeller-concept.mp4` | Concept video | Yes |

The videos in `local/` are re-encoded from the originals in
`~/fluttercon-captures/2026-10-31-infinix-x6873/videos/`, with a key frame every 30 frames, so
jumping between clips does not stall.

