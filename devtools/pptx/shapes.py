"""List a slide's shapes in px of the 1920 x 1080 frame: id, kind, position, size, fill, line, font size, color, text.

  python shapes.py un/ppt/slides/slide8.xml
"""
import sys
from lxml import etree
ns={'p':'http://schemas.openxmlformats.org/presentationml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
t=etree.parse(sys.argv[1]); root=t.getroot()
W=int(sys.argv[2]) if len(sys.argv)>2 else 0
for el in root.iter('{%s}sp'%ns['p'], '{%s}pic'%ns['p'], '{%s}cxnSp'%ns['p']):
    nv=el.find('.//p:cNvPr',ns); off=el.find('.//a:xfrm/a:off',ns); ext=el.find('.//a:xfrm/a:ext',ns)
    fill=el.find('./p:spPr/a:solidFill/a:srgbClr',ns); ln=el.find('./p:spPr/a:ln',ns)
    lnc=ln.find('.//a:srgbClr',ns) if ln is not None else None
    dash=ln.find('a:prstDash',ns) if ln is not None else None
    txt=''.join(x.text or '' for x in el.iter('{%s}t'%ns['a']))
    sz=[r.get('sz') for r in el.iter('{%s}rPr'%ns['a']) if r.get('sz')]
    col=[c.get('val') for r in el.iter('{%s}rPr'%ns['a']) for c in r.iter('{%s}srgbClr'%ns['a'])]
    k=lambda v:int(v)/6350 if v else 0  # EMU -> px: 12192000 EMU slide width / 1920 px
    print(f"id={nv.get('id'):>4} {etree.QName(el).localname:6s} x={k(off.get('x')) if off is not None else 0:7.1f} y={k(off.get('y')) if off is not None else 0:6.1f} w={k(ext.get('cx')) if ext is not None else 0:6.1f} h={k(ext.get('cy')) if ext is not None else 0:6.1f} fill={fill.get('val') if fill is not None else '-'} ln={lnc.get('val') if lnc is not None else '-'}{'/dash' if dash is not None else ''} sz={sz[:1]} col={col[:1]} txt={txt[:50]!r}")
