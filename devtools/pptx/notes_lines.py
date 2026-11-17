"""Print the speaker-note lines of notes slides (run from the folder holding un/), with run counts.

  python notes_lines.py 3 5 8
"""
import sys
from lxml import etree
A='{http://schemas.openxmlformats.org/drawingml/2006/main}'
P='{http://schemas.openxmlformats.org/presentationml/2006/main}'
def body(root):
    for sp in root.iter(P+'sp'):
        ph=sp.find('.//'+P+'ph')
        if ph is not None and ph.get('type')=='body': return sp.find(P+'txBody')
def lines(tx):
    out=[]; cur=[]
    for p in tx.findall(A+'p'):
        for ch in p:
            if ch.tag==A+'r': cur.append(ch)
            elif ch.tag==A+'br': out.append(cur); cur=[]
        out.append(cur); cur=[]
    return out
if __name__=='__main__':
    for n in sys.argv[1:]:
        root=etree.parse(f'un/ppt/notesSlides/notesSlide{n}.xml').getroot()
        tx=body(root); print('== notes',n,'paras',len(tx.findall(A+'p')))
        for i,l in enumerate(lines(tx)):
            print(i, len(l), repr(''.join(r.findtext(A+'t') or '' for r in l))[:110])
