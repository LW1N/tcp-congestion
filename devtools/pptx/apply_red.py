"""Apply the RED follow-up edits to un/ (run once on a fresh unpack of user.pptx)."""
from edit_deck import *

S = 'un/ppt/slides/slide{}.xml'
N = 'un/ppt/notesSlides/notesSlide{}.xml'


def slide(n):
    t = load(S.format(n))
    return t, t.getroot()


# ---------- slide 6: RED now in all three experiments ----------
t, r = slide(6)
chip = shape(r, 153)                                       # '+ RED' chip on the S3 card
s1chip, s1id = clone(r, chip)
place(s1chip, x=399.4, y=690.8)                            # after 'mixed algorithms' on S1
s2chip, s2id = clone(r, chip)
place(s2chip, x=738.0, y=690.8)                            # second chip row on S2
add_with(r, 0, 142, s1id)
add_with(r, 1, 147, s2id)
strip = shape(r, 162)
runs = strip.findall('.//' + A + 'r')
assert runs[-1].findtext(A + 't') == ' in S3 · 5+ runs per setting'
runs[-1].find(A + 't').text = ' in all three (2nd machine) · 5+ runs per setting'
save(t, S.format(6))

# ---------- slide 8: a RED bar per row ----------
t, r = slide(8)
set_runs(shape(r, 197), 'On FIFO or RED, BBR usually takes the link')
rows = [(344, 208, 209, 210, 211, 5.2), (462, 213, 214, 215, 216, 7.0), (580, 218, 219, 220, 221, 2.2),
        (698, 223, 224, 225, 226, 2.9), (816, 228, 229, 230, 231, 4.9)]
SCALE = 730 / 48.6                                         # px per percent, from the existing bars
idmap = {}
for y0, pb, pl, fb, fl, red in rows:
    for bar, lbl, y in ((pb, pl, y0 - 11), (fb, fl, y0 + 53)):
        place(shape(r, bar), y=y, h=26, corners=('tr', 'br'))
        place(shape(r, lbl), y=y - 6)
    src_bar, src_lbl = shape(r, pb), shape(r, pl)
    nb, nbid = clone(r, src_bar, after=shape(r, pl))
    w = round(red * SCALE)
    place(nb, x=500, y=y0 + 21, w=w, h=26, corners=('tr', 'br'))
    recolor(nb, RED)
    nl, nlid = clone(r, src_lbl, after=nb)
    place(nl, x=500 + w + 12, y=y0 + 15)
    set_runs(nl, f'{red}%')
    for run in nl.iter(A + 'rPr'):                        # row 3's pfifo label is dark text inside its bar
        c = run.find('.//' + A + 'srgbClr')
        if c is not None:
            c.set('val', 'F4F3F7')
    idmap[str(pb)], idmap[str(pl)] = str(nbid), str(nlid)
add_click(r, 0, 0, idmap)
# legend: pfifo | RED* | fq_codel | fair 50%
sw, sl = clone(r, shape(r, 200), after=shape(r, 201))[0], None
place(sw, x=676)
recolor(sw, RED)
sl = clone(r, shape(r, 201), after=sw)[0]
place(sl, x=714, w=70)
set_runs(sl, 'RED*')
for sid, x in ((202, 802), (203, 840), (204, 961), (205, 999)):
    place(shape(r, sid), x=x)
save(t, S.format(8))

# ---------- slide 9: a RED bar per UDP load ----------
t, r = slide(9)
set_runs(shape(r, 254), 'On FIFO or RED, TCP gets only what UDP leaves')
foot = shape(r, 288)
set_runs(foot, text_of(foot) + ' · *second test machine')
centers = [337, 612, 887, 1162]
pf = [(266, 267), (268, 269), (270, 271), (272, 273)]
fq = [(274, 275), (276, 277), (278, 279), (280, 281)]
reds = [34.0, 22.4, 10.9, 2.1]
idmap = {}
for c, (pb, pl), (fb, fl), red in zip(centers, pf, fq, reds):
    for bar, lbl, x in ((pb, pl, c - 118), (fb, fl, c + 46)):
        place(shape(r, bar), x=x, corners=('tl', 'tr'))
        place(shape(r, lbl), x=x - 13)
    h = round(red * 10)
    nb, nbid = clone(r, shape(r, pb), after=shape(r, pl))
    place(nb, x=c - 36, y=820 - h, h=h, corners=('tl', 'tr'))
    recolor(nb, RED)
    nl, nlid = clone(r, shape(r, pl), after=nb)
    place(nl, x=c - 49, y=820 - h - 38)
    set_runs(nl, f'{red}')
    idmap[str(pb)], idmap[str(pl)] = str(nbid), str(nlid)
add_click(r, 0, 0, idmap)
sw = clone(r, shape(r, 257), after=shape(r, 258))[0]
place(sw, x=916)
recolor(sw, RED)
sl = clone(r, shape(r, 258), after=sw)[0]
place(sl, x=954, w=70)
set_runs(sl, 'RED*')
for sid, x in ((259, 1042), (260, 1080)):
    place(shape(r, sid), x=x)
save(t, S.format(9))

# ---------- slide 11: RED bars from the 5 ms RED (s3r) ----------
t, r = slide(11)
for bar, lbl, v in ((348, 349, 2.4), (350, 351, 2.5), (352, 353, 2.4)):
    h = v * 291 / 48.6
    place(shape(r, bar), y=800 - h, h=h)
    place(shape(r, lbl), y=800 - h - 36)
    set_runs(shape(r, lbl), f'{v}%')
set_runs(shape(r, 328), 'RED*')
place(shape(r, 328), w=70)
for sid in (329, 330, 331, 332):
    place(shape(r, sid), x=px(shape(r, sid), 'x') + 16)
set_runs(shape(r, 365), 'RED*:', ' BBR still wins')
foot = shape(r, 367)
assert text_of(foot).endswith(' · *second test machine, 3-minute runs')
set_runs(foot, text_of(foot).replace(' · *second test machine, 3-minute runs',
                                     ' · *second test machine · 51%: 3-minute runs'))
save(t, S.format(11))

# ---------- slide 12: RED column from the 5 ms RED (s3qr) ----------
t, r = slide(12)
set_runs(shape(r, 381), 'RED · 5 ms target')
for bar, lbl, v in ((392, 393, 0.3), (408, 409, 0.4), (424, 425, 2.7), (440, 441, 2.3)):
    place(shape(r, bar), w=max(3, round(v * 3)), corners=('tr', 'br'))
    set_runs(shape(r, lbl), f'{v}%')
save(t, S.format(12))

# ---------- slide 14 footer: the RED data is not from the VM ----------
t, r = slide(14)
foot = shape(r, 511)
assert 'one 50 Mbps link in a VM,' in text_of(foot)
set_runs(foot, text_of(foot).replace('one 50 Mbps link in a VM,', 'one emulated 50 Mbps link,'))
save(t, S.format(14))

# ---------- speaker notes ----------
def notes(n):
    tr = load(N.format(n))
    return tr, notes_runs(tr.getroot())

tr, tx = notes(3)
note_sub(tx, 'Follow-up runs came later on a second machine',
         '205 more runs, including three-minute runs. Ten repeated settings',
         '482 more runs, including three-minute runs and the RED tests. Eighteen repeated settings')
save(tr, N.format(3))

tr, tx = notes(5)
note_insert_after(tx, 'Random Early Detection(RED):',
                  SUB + 'I set it to aim for 5 ms of queue, the same target as fq_codel, so the two compare fairly. '
                        'My first setting tied its thresholds to the buffer size, so its target grew with the buffer.')
save(tr, N.format(5))

tr, tx = notes(6)
note_sub(tx, 'Every experiment compares', 'Follow-ups on a second machine added 205 more runs:',
         'Follow-ups on a second machine added 482 more runs:')
note_sub(tx, 'Every experiment compares', ', plus a deep-buffer test of every algorithm under all three queues.',
         ', a deep-buffer test of every algorithm under all three queues, and RED in all three experiments, '
         'set to the same 5 ms target as fq_codel.')
save(tr, N.format(6))

tr, tx = notes(8)
note_insert_after(tx, '- Bottom row: Reno does no better.',
                  '- Next click, purple bars = RED, also from the second machine. With one flow of each it’s even '
                  'worse than the FIFO: CUBIC and Reno keep about 5% against BBR, and only 2% when BBR has the short path.',
                  SUB + 'RED drops packets from both flows, but only the loss-based one slows down, so BBR likely takes what it gives up.')
note_insert_after(tx, 'NOTE: flows running the same algorithm',
                  '- Under RED, the short path’s advantage got bigger: Reno and CUBIC on mixed paths fell to a fairness '
                  'index of about 0.75 to 0.8, likely because RED keeps the queue nearly empty, so nothing evens out the '
                  '20 vs 80 ms gap. As designed, RED kept their delay under a millisecond, but Reno lost 13 to 17 percent of the link.')
save(tr, N.format(8))

tr, tx = notes(9)
note_sub(tx, '- As UDP takes a quarter', ' Next click, the cyan bars are fq_codel', '')
note_insert_after(tx, '- As UDP takes a quarter',
                  '- Next click, purple bars = RED, from the second machine. No help: TCP still gets only what UDP '
                  'leaves, 34, 22 and 11 megabits, then about 2 at full speed, because UDP ignores RED’s early drops '
                  'just like the FIFO’s.',
                  '- Next click, the cyan bars are fq_codel')
save(tr, N.format(9))

tr, tx = notes(11)
note_set(tx, '- I expected RED (Random Early Detection)',
         '- I expected RED (Random Early Detection) to even things out, but it doesn\'t. These bars are the 5 ms RED '
         'from the second machine, 2.4 to 2.5 percent, and my first RED setting gave about the same, 2.2 to 2.5.')
save(tr, N.format(11))

tr, tx = notes(12)
note_set(tx, '- Click, RED:',
         '- Click, RED: this is the 5 ms RED from the second machine, so it keeps the buffer nearly empty by design. '
         '5 ms is about 21 packets, 2.5 percent of this buffer. Reno and CUBIC stay well under that, 0.3 and 0.4 '
         'percent, and Reno pays for it with only 86 percent of the link. With BBR it sits right at the target, '
         'about 2.5 percent, likely because BBR doesn’t slow down for the early drops.')
note_insert_after(tx, '- Click, RED:', SUB + 'My first RED setting tied its thresholds to the buffer, and there the '
                                             'fill was 12 to 26 percent.')
save(tr, N.format(12))

tr, tx = notes(13)
note_insert_after(tx, '- yes, its 20 millisecond flow recovers',
                  '- Under RED the bias got stronger, a fairness index of about 0.75 for Reno, likely because RED '
                  'keeps the queue almost empty, so the raw 20 vs 80 ms gap decides.')
note_sub(tx, '- clearly yes.', '- clearly yes.', '- clearly yes. RED doesn’t fix it: TCP still got only about 2 '
                                                  'megabits next to full-speed UDP.')
save(tr, N.format(13))

tr, tx = notes(14)
note_set(tx, '- RED isn’t a substitute.',
         '- RED isn’t a substitute. Even aimed at the same 5 ms as fq_codel, it left CUBIC with about two percent '
         'against BBR, didn’t protect TCP from UDP, and cost Reno 13 to 17 percent of the link. A slower RED '
         'average only made that worse.')
note_sub(tx, 'One caveat:', 'one 50 Mbps link in a VM, with BBR version 1, no ECN and a single RED setting, so',
         'one emulated 50 Mbps link, with BBR version 1 and no ECN, so')
save(tr, N.format(14))

tr, tx = notes(15)
note_sub(tx, 'To wrap up:', 'across almost 500 runs,', 'across almost a thousand runs on two machines,')
note_sub(tx, 'To wrap up:', 'which kept up to 35 milliseconds in its own queue.',
         'which kept up to 35 milliseconds in its own queue. RED, aimed at the same 5 ms, fixed the delay but none of the rest.')
save(tr, N.format(15))
print('applied')
