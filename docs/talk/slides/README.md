# Talk deck

The slides for *Beyond Skia*: 32 slides plus 2 backup tables. The spoken words and the demo cues are
in the speaker notes and the [Demo script](../demo-script.md).

| File | What it is |
|---|---|
| `beyond-skia-dark.pptx` | The dark deck. It matches the demo app, so the switch to the phone is seamless |
| `beyond-skia.pptx` | The same deck, light, for a bright room |
| `local/beyond-skia.pdf` | Still copy of the light deck, the fallback |
| `local/clips-stage/` | The videos, numbered in playing order; each slide's notes say when to play them |
| `local/pptx/fonts/` | Inter, Inter Tight and JetBrains Mono. Embedded in the decks; install them too on the presenting machine, as a backup |

Animations only run in Slide Show mode in PowerPoint or LibreOffice Impress, never in a file preview
such as a code editor extension.

Rebuild with `python3 docs/talk/slides/build_pptx.py` (needs `python-pptx`, Pillow, and the photo, logos, fonts and images in `local/`). Colours come from the
`THEMES` table, so one edit restyles a whole deck. Speaker notes live in `speaker_notes.json`, one entry per slide; the [Demo script](../demo-script.md) repeats them, so change both.

`index.html` is an outdated browser draft, kept for reference and marked with a banner. It has claims that the
[Fact check](../fact-check.md) corrects, so don't present from it.

## Design rules

The slides support the speaker and the demo app. They don't replace them.

- **One idea per slide.** A title that states the point, one visual, and as few words as it takes. Explanations go in the speaker notes.
- **Real material first.** Screens from the demo app, real traces, real numbers and real code.
- **No decoration.** No cards, icon tiles, gradients, shadows, section labels or progress markers. Hairlines and space do the structure. Flat blocks appear only in diagrams and data.
- **Grid.** 72 px side margins. The title starts at y=50. The source and the logo share the bottom line at y=664.
- **Type.** Inter Tight SemiBold for headlines, Inter and Inter Medium for text, JetBrains Mono for code and thread names. Bold is never used, because the weights are their own families.
- **Fonts.** All four are embedded in each `.pptx`, so a machine without them still shows them in PowerPoint for Windows or Mac. Keynote and Google Slides ignore embedded fonts, so use the PDF there, or install the fonts.
- **Colour.** Warm paper and ink in the light deck, near-black and warm white in the dark deck, and a grey. One ember accent marks the one thing to look at, usually what is over budget. The cover, the turning point (slide 19) and the close are ink in both decks.
- **Tables.** Native and editable. A quiet header and a hairline under each row, with no fills.
- **Numbers.** Only the Infinix measurements count as evidence. Emulator screens are labelled and quote no timing. Anything drawn rather than measured is labelled "Illustration".

## What is in git and what is not

The two decks are in git, and they contain the speaker photo, the FlutterCon logo and the speaker notes. The repository is public, so `local/` is ignored for everything else. It holds the speaker photo, the FlutterCon logo (from the organisers' `droidconKE/flutterconKEApp` repo),
the videos, screenshots and the PDF backup. **Copy the whole `slides` folder and the concept
video to a USB drive**; from a fresh clone, `local/` has to be restored from that copy.

| Path | Contents | In git |
|---|---|---|
| `beyond-skia.pptx`, `beyond-skia-dark.pptx` | The decks, including the photo, logo, fonts and speaker notes | Yes |
| `build_pptx.py` | Builds the decks | Yes |
| `speaker_notes.json` | The speaker notes, one entry per slide | Yes |
| `index.html`, `deck.css`, `deck.js` | Outdated browser draft and engine, marked with a banner | Yes |
| `trace-data.js` | Real frame timings from the stage phone's traces | Yes |
| `fonts/` | Outfit and JetBrains Mono, with their open font licences | Yes |
| `local/` | Source photo and logos, videos, installable fonts, screenshots, QR code, PDF, previews | **No** |
| `../media/skia-to-impeller-concept.mp4` | Concept video | Yes |

The videos in `local/` are re-encoded from the originals in
`~/fluttercon-captures/2026-10-31-infinix-x6873/videos/`, with a key frame every 30 frames, so
jumping between clips does not stall.

