# Talk deck

The slides for *Beyond Skia*: 32 slides plus 2 backup tables. The spoken words are
in the speaker notes and the [Demo script](../demo-script.md).

| File | What it is |
|---|---|
| `beyond-skia.pptx` | **The stage deck**, light |
| `beyond-skia-dark.pptx` | The same deck, dark |
| `local/beyond-skia.pdf` | Still copy of the light deck, the fallback |
| `local/clips-stage/` | The videos, numbered in playing order; each slide's notes say when to play them |
| `local/pptx/fonts/` | Inter, Inter Tight and JetBrains Mono. **Install these on the presenting machine** |

Animations only run in Slide Show mode in PowerPoint or LibreOffice Impress, never in a file preview
such as a code editor extension.

Rebuild with `python3 docs/talk/slides/build_pptx.py` (needs `python-pptx`, Pillow, and the photo, logos and images in `local/`). Colours come from the
`THEMES` table, so one edit restyles a whole deck. Speaker notes live in `speaker_notes.json`, one entry per slide; the [Demo script](../demo-script.md) repeats them, so change both.

`index.html` is the earlier browser version, with the older layout and text. It no longer matches the
PowerPoint deck.

## Design rules

- **One topic per slide, taught in full.** A slide holds its diagram and its explanation together, and each slide leads into the next. Numbers tables stay in the backups.
- **Grid.** 56 px side margins and 16 px gutters. Content runs from y=128 (y=164 under a subtitle) to y=648. The source
  line sits on the logo's line at the bottom, and must fit on one line.
- **Hierarchy.** A section label and journey marker, a left-aligned title, then tiles. Gradient tiles carry the headline
  result, and the dark bar carries the one sentence to remember.
- **Tables.** Native and editable, with a header band, hairline rows and one highlighted column.
- **Icons.** [Lucide](https://lucide.dev), stored as white masks in `icons/` and tinted at build time. Licence in `icons/LICENSE.txt`.
- **Type.** Inter Tight for headlines, Inter for text, JetBrains Mono only for code and logs. Apple's SF
  Pro is not licensed for this. Fine print is at least 18 px. Line spacing is 1.08 for text and 0.96 for headings.
- **Colour.** Blue is the main result and Impeller. Ink is the comparison and Skia. Red means over budget.
- **Charts.** No scales or gridlines where they add nothing; label lines directly.
- **Numbers.** Only the Infinix measurements count as evidence. Emulator screens are labelled and quote
  no timing. Anything drawn rather than measured is labelled "Illustration".

## What is in git and what is not

The two decks are in git, and they contain the speaker photo, the FlutterCon logo and the speaker notes. The repository is public, so `local/` is ignored for everything else. It holds the speaker photo, the FlutterCon logo (from the organisers' `droidconKE/flutterconKEApp` repo),
the videos, screenshots and the PDF backup. **Copy the whole `slides` folder and the concept
video to a USB drive**; from a fresh clone, `local/` has to be restored from that copy.

| Path | Contents | In git |
|---|---|---|
| `beyond-skia.pptx`, `beyond-skia-dark.pptx` | The decks, including the photo, logo and speaker notes | Yes |
| `build_pptx.py` | Builds the decks | Yes |
| `speaker_notes.json` | The speaker notes, one entry per slide | Yes |
| `icons/` | Lucide icon masks and their licence | Yes |
| `index.html`, `deck.css`, `deck.js` | Earlier browser deck and engine | Yes |
| `trace-data.js` | Real frame timings from the stage phone's traces | Yes |
| `fonts/` | Outfit and JetBrains Mono, with their open font licences | Yes |
| `local/` | Source photo and logos, videos, installable fonts, screenshots, QR code, PDF, previews | **No** |
| `../media/skia-to-impeller-concept.mp4` | Concept video | Yes |

The videos in `local/` are re-encoded from the originals in
`~/fluttercon-captures/2026-10-31-infinix-x6873/videos/`, with a key frame every 30 frames, so
jumping between clips does not stall.

