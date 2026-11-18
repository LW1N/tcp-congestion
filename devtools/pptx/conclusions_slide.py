"""Slide 14 'What to deploy' as general recommendations: scope stated once under the title, each box a
principle (fq_codel if you control the queue; otherwise size a FIFO near 1x BDP), one closing line on
who wins a shared queue. Also fixes slide 13 row 1. Layout and clicks are kept; the closing line joins
the last click. Run from the folder holding un/ (the user's deck unpacked). Shape ids are those of
'(RED v3 questions)(1).pptx' (Google renumbers ids on download: check with shapes.py first).
"""
from edit_deck import A, load, save, shape, place, clone, set_runs, text_of, add_with, notes_runs, note_set

S14 = 'un/ppt/slides/slide14.xml'
S13 = 'un/ppt/slides/slide13.xml'
N14 = 'un/ppt/notesSlides/notesSlide14.xml'


def restyle(el, color, align):
    for c in el.iter(A + 'srgbClr'):
        c.set('val', color)
    for p in el.iter(A + 'pPr'):
        p.set('algn', align)


t = load(S14); r = t.getroot()
assert text_of(shape(r, 509)) == 'What to deploy'
set_runs(shape(r, 509), 'What to deploy at a shared bottleneck')
scope, _ = clone(r, shape(r, 522), after=shape(r, 509))          # 13 pt line, always visible
place(scope, x=128, y=262, w=1664, h=40.4)
set_runs(scope, 'Recommendations from one emulated 50 Mbps link (BBRv1, no ECN): directions, not guarantees')
restyle(scope, 'A9A7BB', 'l')
set_runs(shape(r, 517), 'Can you change the bottleneck queue?')
set_runs(shape(r, 522), 'fair to every sender, even UDP')
set_runs(shape(r, 523), 'Stuck with a FIFO? Size it near 1× BDP')
set_runs(shape(r, 524), 'Too small: senders that halve on loss leave the link idle')
set_runs(shape(r, 525), 'About 1× BDP: link stays full, delay up to one RTT')
set_runs(shape(r, 526), 'Too large: loss-based senders keep it mostly full, adding delay')
close, close_id = clone(r, shape(r, 522), after=shape(r, 526))
place(close, x=128, y=840, w=1664, h=40.4)
set_runs(close, 'On a FIFO or RED queue, senders that ignore loss (BBR, UDP) usually take bandwidth from those that back off.')
restyle(close, 'F4F3F7', 'l')
add_with(r, 3, 526, close_id)                                     # appears with the FIFO size boxes
set_runs(shape(r, 527), 'CMPE 206 · TCP congestion and network performance')
save(t, S14)

nt = load(N14); tx = notes_runs(nt.getroot())
note_set(tx, 'If you’re stuck with a plain FIFO', 'If you’re stuck with a plain FIFO, size the buffer near one BDP:')
save(nt, N14)

t = load(S13); r = t.getroot()
row1 = [el for el in r.iter() if el.tag.endswith('}sp') and text_of(el).startswith('FIFO: BBR wins(unless shorter RTT)')]
assert len(row1) == 1
set_runs(row1[0], 'FIFO: BBR, mostly · fq_codel: even split')   # fits one line; the short-path exception is in the notes
save(t, S13)
print('slides 13 and 14 done')
