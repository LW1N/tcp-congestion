"""Rough render of a slide from its shape geometry (fills, outlines, text), for layout checks only."""
import sys
from lxml import etree
from PIL import Image, ImageDraw, ImageFont

A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
EMU = 6350
FONT = '/mnt/c/Windows/Fonts/arial.ttf'


def box(el):
    off = el.find('.//' + A + 'xfrm/' + A + 'off')
    ext = el.find('.//' + A + 'xfrm/' + A + 'ext')
    if off is None or ext is None:
        return None
    return [int(v) / EMU for v in (off.get('x'), off.get('y'), ext.get('cx'), ext.get('cy'))]


def render(path, out):
    root = etree.parse(path).getroot()
    img = Image.new('RGB', (1920, 1080), '#111019')
    d = ImageDraw.Draw(img)
    for el in root.iter(P + 'sp', P + 'cxnSp', P + 'pic'):
        b = box(el)
        if b is None:
            continue
        x, y, w, h = b
        tag = etree.QName(el).localname
        if tag == 'pic':
            d.rectangle([x, y, x + w, y + h], outline='#3a3a55')
            continue
        fill = el.find('./' + P + 'spPr/' + A + 'solidFill/' + A + 'srgbClr')
        ln = el.find('./' + P + 'spPr/' + A + 'ln')
        lc = ln.find('.//' + A + 'srgbClr') if ln is not None else None
        if tag == 'cxnSp':
            if lc is not None:
                d.line([x, y, x + w, y + h], fill='#' + lc.get('val'), width=2)
            continue
        if fill is not None:
            d.rectangle([x, y, x + max(w, 1), y + max(h, 1)], fill='#' + fill.get('val'))
        if lc is not None:
            d.rectangle([x, y, x + w, y + h], outline='#' + lc.get('val'))
        runs = el.findall('.//' + A + 'r')
        text = ''.join(r.findtext(A + 't') or '' for r in runs)
        if text.strip():
            rpr = next((r.find(A + 'rPr') for r in runs if r.find(A + 'rPr') is not None and r.find(A + 'rPr').get('sz')), None)
            sz = int(rpr.get('sz')) / 100 * 2 if rpr is not None else 24
            col = el.find('.//' + A + 'rPr//' + A + 'srgbClr')
            font = ImageFont.truetype(FONT, int(sz))
            tw = d.textlength(text, font=font)
            algn = el.find('.//' + A + 'pPr')
            ax = algn.get('algn') if algn is not None else 'l'
            tx = x + (w - tw) / 2 if ax == 'ctr' else (x + w - tw if ax == 'r' else x + 4)
            d.text((tx, y + (h - sz) / 2), text, font=font, fill='#' + (col.get('val') if col is not None else 'FFFFFF'))
            if tw > w + 2:
                d.rectangle([x, y, x + w, y + h], outline='#FF0000', width=3)   # text wider than its box
    img.save(out)


if __name__ == '__main__':
    render(sys.argv[1], sys.argv[2])
