"""Zip un/ back into a .pptx: the original's members in their order, then any new parts (an added
slide, its notes), media stored uncompressed.

  python pack.py user.pptx out.pptx
"""
import os
import sys
import zipfile

src, out = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(src) as orig:
    names = [i.filename for i in orig.infolist()]
extra = sorted(os.path.relpath(os.path.join(d, f), 'un').replace(os.sep, '/')
               for d, _, files in os.walk('un') for f in files)
names += [n for n in extra if n not in names]
with zipfile.ZipFile(out, 'w') as z:
    for n in names:
        stored = n.endswith(('.gif', '.png', '.jpg'))
        z.write(os.path.join('un', n), n, compress_type=zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED)
print(out, os.path.getsize(out))
