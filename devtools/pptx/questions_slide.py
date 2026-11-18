"""Turn the predictions slide (slide13.xml) into 'What the experiments answered': four questions in
talk order (slides 8, 9, 11, 12), each with its answer; the fifth row and its click are removed.
The proposal's predictions stay in the report (Table II); the notes say so. Layout, click steps and
formatting are kept: only the text of the existing cells changes, and the notes reuse the user's
paragraph styles (header line, '-' bullet). Run from the folder holding un/.
"""
import copy
from edit_deck import A, P, load, save, shape, set_runs, text_of, notes_runs

SLIDE = 'un/ppt/slides/slide13.xml'
NOTES = 'un/ppt/notesSlides/notesSlide13.xml'
ROWS = [  # (question cell id, answer cell id, question, answer)
    (485, 486, 'Who wins when TCP flows compete?', 'FIFO: BBR wins, CUBIC 10.6% · fq_codel: ~49%'),
    (489, 490, 'What if one flow never slows down?', 'FIFO: TCP gets 0.05 Mbps · fq_codel: 35 Mbps'),
    (493, 494, 'Does queue size change who wins?', 'FIFO: BBR wins up to 1× BDP, even split at 4×'),
    (497, 498, 'How full does a deep buffer stay?', 'FIFO: CUBIC 85% (~170 ms) · fq_codel under 1%'),
]
NOTE_LINES = [
    ('h', 'The questions the experiments answered, in the order of the talk:'),
    ('h', 'Who wins when TCP flows compete?'),
    ('-', 'On a FIFO, BBR: CUBIC kept 10.6% and Reno 10% against one BBR flow. fq_codel brought CUBIC back to about 49%.'),
    ('-', 'The exception: when BBR had the short path, CUBIC kept 47%.'),
    ('h', 'What if one flow never slows down?'),
    ('-', 'On a FIFO, TCP got 0.05 megabits next to full-speed UDP. fq_codel gave it 35 back. RED doesn’t fix it: TCP still got only about 2.'),
    ('h', 'Does queue size change who wins?'),
    ('-', 'Yes on a FIFO: BBR wins up to one BDP, and at four BDPs CUBIC catches up to an even split once the run settles. Under RED, BBR won at every buffer size.'),
    ('h', 'How full does a deep buffer stay?'),
    ('-', 'Four CUBIC flows kept a 4x BDP FIFO 85 percent full, about 170 milliseconds of waiting. fq_codel kept it under 1 percent, as its 5 ms target intends.'),
    ('-', 'One CUBIC flow on the 150 millisecond path, with a 4x BDP buffer, added 494 milliseconds.'),
    ('', ''),
    ('h', 'NOTE: before any runs, my proposal made five predictions. The report checks each one (Table II): three held (one only on a FIFO) and two held partly. Reno did favor short paths more than CUBIC, and BBR turned out to favor the long path.'),
]

t = load(SLIDE); r = t.getroot()
assert text_of(shape(r, 478)) == 'Five predictions made before any runs'
set_runs(shape(r, 478), 'What the experiments answered')
set_runs(shape(r, 481), 'Question')
set_runs(shape(r, 482), 'Answer')
for q_id, a_id, q, a in ROWS:
    set_runs(shape(r, q_id), q)
    set_runs(shape(r, a_id), a)
ROW5 = {'499', '500', '501', '502'}                 # background, number, question, answer of row 5
for el in list(r.iter(P + 'sp')):
    if el.find('.//' + P + 'cNvPr').get('id') in ROW5:
        el.getparent().remove(el)
seq = r.find('.//' + P + 'cTn[@nodeType="mainSeq"]').find(P + 'childTnLst')
for step in list(seq):                              # drop the click that revealed row 5
    if {t.get('spid') for t in step.iter(P + 'spTgt')} <= ROW5:
        seq.remove(step)
save(t, SLIDE)

nt = load(NOTES); tx = notes_runs(nt.getroot())
paras = tx.findall(A + 'p')
def first(pred):
    return next(p for p in paras if pred(p))
lvl = lambda p: (p.find(A + 'pPr').get('lvl') if p.find(A + 'pPr') is not None else '0') or '0'
bullet = lambda p: p.find('.//' + A + 'buChar') is not None
text = lambda p: ''.join(x.text or '' for x in p.iter(A + 't')).strip()
tmpl = {'h': first(lambda p: not bullet(p) and text(p) and p.find(A + 'br') is None),
        '-': first(lambda p: bullet(p) and lvl(p) == '0')}
blank = copy.deepcopy(tmpl['h'])
for run in blank.findall(A + 'r'):
    blank.remove(run)
tmpl[''] = blank
new = []
for kind, line in NOTE_LINES:
    p = copy.deepcopy(tmpl[kind])
    runs = p.findall(A + 'r')
    if runs:
        runs[0].find(A + 't').text = line
        for extra in runs[1:]:
            p.remove(extra)
    new.append(p)
for p in paras:
    tx.remove(p)
for p in new:
    tx.append(p)
save(nt, NOTES)
print('questions slide done')
