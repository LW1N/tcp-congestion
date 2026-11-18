# Deck and guide tools

The talk is presented from a .pptx in Google Slides (the user's download, with their own speaker notes).
These scripts edit that file in place instead of re-exporting the HTML deck, which would overwrite the
notes and lose the animations. They were used on 2026-11-17 to add the RED follow-ups.

Run from a work folder that holds the user's `user.pptx`; Python needs `lxml` (and `pillow` for render.py):

```bash
uv run --no-project --with lxml --with pillow==11.3.0 python <script> ...
```

| script | does |
| --- | --- |
| `edit_deck.py` | helpers: find, move, clone and recolor shapes, rebuild rounded bar paths, clone click steps, edit note lines |
| `apply_red.py` | the RED edits (slides 6, 8, 9, 11, 12, 14 and notes); run once on a fresh unpack into `un/` |
| `questions_slide.py` | turns the predictions slide (13) into 'What the experiments answered': five questions in talk order with answers, notes rebuilt in the user's paragraph styles (2026-11-17) |
| `conclusions_slide.py` | slide 14 as general recommendations with a scope line, plus slide 13 row 1 (2026-11-17) |
| `pack.py` | zip `un/` back into a .pptx, including parts added since the original (a new slide and its notes) |
| `shapes.py`, `timing.py`, `notes_lines.py` | inspect shapes, click steps and note lines |
| `render.py` | rough PNG of a slide from shape geometry (fills, lines, text; no wrapping), for layout checks |
| `edit_guide.py` | the matching prep-guide update; re-syncs the guide's NOTES from `un/` |

Workflow: unpack (`python3 -c "import zipfile; zipfile.ZipFile('user.pptx').extractall('un')"`), apply,
`pack.py user.pptx out.pptx`, then the pptx skill's `validate.py out.pptx --original user.pptx`, render the
changed slides, and diff the slide text against the original (pptx skill `slide_text.py`).

Google Slides renumbers shape ids on every download, so `apply_red.py` only matches the file it was written for; reuse its helpers, not its ids. To add a slide: the pptx skill's `add_slide.py`, then copy a notesSlide part for it (add_slide.py leaves the new slide without notes) and renumber the footers, labels and progress bars.
