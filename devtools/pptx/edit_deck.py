"""Add the RED follow-up results to the user's Google-Slides .pptx in place (unpacked in un/).

Shapes are cloned from their pfifo neighbours, new bars get their own click step cloned from the
pfifo step, and speaker notes are edited line by line so every other line stays as the user wrote it.
"""
import copy
from lxml import etree

A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
EMU = 6350                      # EMU per px of the 1920 x 1080 frame the deck was laid out in
RED = 'A78BFA'
K = 0.5523                      # cubic Bezier quarter-circle constant


def load(path):
    return etree.parse(path)


def save(tree, path):
    tree.write(path, xml_declaration=True, encoding='UTF-8', standalone=True)


# ---------- shapes ----------

def shape(root, sid):
    for el in root.iter(P + 'sp', P + 'cxnSp'):
        nv = el.find('.//' + P + 'cNvPr')
        if nv is not None and nv.get('id') == str(sid):
            return el
    raise KeyError(sid)


def next_id(root):
    return max(int(e.get('id')) for e in root.iter(P + 'cNvPr')) + 1


def bar_path(w, h, corners):
    """Rectangle path in EMU with the named corners ('tl', 'tr', 'br', 'bl') rounded."""
    r = min(38100, w // 2, h // 2)
    c = {k: (r if k in corners else 0) for k in ('tl', 'tr', 'br', 'bl')}
    pts = []
    def ln(x, y): pts.append(f'<a:lnTo><a:pt x="{x}" y="{y}"/></a:lnTo>')
    def cb(x1, y1, x2, y2, x, y):
        pts.append(f'<a:cubicBezTo><a:pt x="{x1}" y="{y1}"/><a:pt x="{x2}" y="{y2}"/><a:pt x="{x}" y="{y}"/></a:cubicBezTo>')
    rk = lambda v: round(v * K)
    start = f'<a:moveTo><a:pt x="{c["tl"]}" y="0"/></a:moveTo>'
    ln(w - c['tr'], 0)
    if c['tr']: cb(w - c['tr'] + rk(c['tr']), 0, w, c['tr'] - rk(c['tr']), w, c['tr'])
    ln(w, h - c['br'])
    if c['br']: cb(w, h - c['br'] + rk(c['br']), w - c['br'] + rk(c['br']), h, w - c['br'], h)
    ln(c['bl'], h)
    if c['bl']: cb(c['bl'] - rk(c['bl']), h, 0, h - c['bl'] + rk(c['bl']), 0, h - c['bl'])
    ln(0, c['tl'])
    if c['tl']: cb(0, c['tl'] - rk(c['tl']), c['tl'] - rk(c['tl']), 0, c['tl'], 0)
    xml = (f'<a:pathLst xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
           f'<a:path extrusionOk="0" h="{h}" w="{w}">{start}{"".join(pts)}<a:close/></a:path></a:pathLst>')
    return etree.fromstring(xml)


def place(el, x=None, y=None, w=None, h=None, corners=None):
    """Move/resize a shape (px); a custom-geometry bar gets a fresh path so its corners stay round."""
    off = el.find('.//' + A + 'xfrm/' + A + 'off')
    ext = el.find('.//' + A + 'xfrm/' + A + 'ext')
    if x is not None: off.set('x', str(round(x * EMU)))
    if y is not None: off.set('y', str(round(y * EMU)))
    if w is not None: ext.set('cx', str(round(w * EMU)))
    if h is not None: ext.set('cy', str(round(h * EMU)))
    cg = el.find('.//' + A + 'custGeom')
    if cg is not None and corners is not None:
        old = cg.find(A + 'pathLst')
        cg.replace(old, bar_path(int(ext.get('cx')), int(ext.get('cy')), corners))


def clone(root, src, after=None):
    new = copy.deepcopy(src)
    sid = next_id(root)
    nv = new.find('.//' + P + 'cNvPr')
    nv.set('id', str(sid))
    nv.set('name', f'RED follow-up;{sid}')
    (after if after is not None else src).addnext(new)
    return new, sid


def recolor(el, color):
    for path in ('./' + P + 'spPr/' + A + 'solidFill/' + A + 'srgbClr',
                 './' + P + 'spPr/' + A + 'effectLst/' + A + 'outerShdw/' + A + 'srgbClr'):
        c = el.find(path)
        if c is not None:
            c.set('val', color)


def set_runs(el, *texts):
    """Set the text of the shape's runs in order; leftover runs are emptied."""
    runs = el.findall('.//' + A + 'r')
    assert len(runs) >= len(texts), (len(runs), texts)
    for r, t in zip(runs, texts):
        r.find(A + 't').text = t
    for r in runs[len(texts):]:
        r.find(A + 't').text = ''


def text_of(el):
    return ''.join(t.text or '' for t in el.iter(A + 't'))


def px(el, attr):
    off = el.find('.//' + A + 'xfrm/' + A + 'off')
    ext = el.find('.//' + A + 'xfrm/' + A + 'ext')
    return {'x': int(off.get('x')), 'y': int(off.get('y')), 'w': int(ext.get('cx')), 'h': int(ext.get('cy'))}[attr] / EMU


# ---------- click steps ----------

def clicks(root):
    seq = root.find('.//' + P + 'cTn[@nodeType="mainSeq"]')
    return seq.find(P + 'childTnLst')


def add_click(root, src_index, after_index, idmap):
    """Clone click src_index, retarget it with idmap (old spid -> new spid), insert after after_index."""
    lst = clicks(root)
    steps = list(lst)
    new = copy.deepcopy(steps[src_index])
    for t in new.iter(P + 'spTgt'):
        assert t.get('spid') in idmap, t.get('spid')
        t.set('spid', idmap[t.get('spid')])
    steps[after_index].addnext(new)


def add_with(root, click_index, template_spid, new_spid):
    """Add a with-previous copy of template_spid's effect in click click_index, for new_spid."""
    step = list(clicks(root))[click_index]
    for t in step.iter(P + 'spTgt'):
        if t.get('spid') == str(template_spid):
            par = t
            while not (par.tag == P + 'par' and par.find(P + 'cTn').get('presetClass')):
                par = par.getparent()
            new = copy.deepcopy(par)
            new.find(P + 'cTn').set('nodeType', 'withEffect')
            for tt in new.iter(P + 'spTgt'):
                tt.set('spid', str(new_spid))
            par.addnext(new)
            return
    raise KeyError(template_spid)


# ---------- notes ----------

def notes_runs(root):
    for sp in root.iter(P + 'sp'):
        ph = sp.find('.//' + P + 'ph')
        if ph is not None and ph.get('type') == 'body':
            return sp.find(P + 'txBody')


def find_run(tx, prefix):
    hits = [r for r in tx.iter(A + 'r') if (r.findtext(A + 't') or '').startswith(prefix)]
    assert len(hits) == 1, (prefix, len(hits))
    return hits[0]


def note_sub(tx, prefix, old, new):
    r = find_run(tx, prefix)
    t = r.find(A + 't')
    assert t.text.count(old) == 1, (prefix, old)
    t.text = t.text.replace(old, new)


def note_set(tx, prefix, new):
    find_run(tx, prefix).find(A + 't').text = new


def note_insert_after(tx, prefix, *lines):
    """New lines after the line starting with prefix, formatted like it (br-separated or one paragraph each)."""
    r = find_run(tx, prefix)
    para = r.getparent()
    nxt = r.getnext()
    if nxt is not None and nxt.tag == A + 'br' or any(c.tag == A + 'br' for c in para):
        br_template = next(c for c in para if c.tag == A + 'br')
        anchor = r
        for text in lines:
            br = copy.deepcopy(br_template)
            nr = copy.deepcopy(r)
            nr.find(A + 't').text = text
            anchor.addnext(br)
            br.addnext(nr)
            anchor = nr
    else:
        anchor = para
        for text in lines:
            np_ = copy.deepcopy(para)
            runs = np_.findall(A + 'r')
            runs[0].find(A + 't').text = text
            for extra in runs[1:]:
                np_.remove(extra)
            anchor.addnext(np_)
            anchor = np_


SUB = ' ' * 4 + '- '       # the user's indented sub-point
