"""Print a slide's click steps: which shape ids each click reveals and with which effects.

  python timing.py un/ppt/slides/slide8.xml
"""
import sys
from lxml import etree
ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
root=etree.parse(sys.argv[1]).getroot()
tm=root.find('.//p:timing',ns)
if tm is None: print('no timing'); sys.exit()
# top-level click sequence: p:par children of the main seq's childTnLst
seq=tm.find('.//p:cTn[@nodeType="mainSeq"]',ns)
for i,par in enumerate(seq.find('p:childTnLst',ns)):
    ids=[]; kinds=[]
    for c in par.iter('{%s}cTn'%ns['p']):
        if c.get('presetClass'): kinds.append((c.get('presetClass'),c.get('presetID'),c.get('nodeType')))
    for t in par.iter('{%s}spTgt'%ns['p']): ids.append(t.get('spid'))
    print('click',i+1,'spids',sorted(set(ids),key=int),'effects',sorted(set(kinds))[:4])
