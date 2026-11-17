"""Zip un/ back into a .pptx with the original's member order and compression (media stored).

  python pack.py user.pptx out.pptx
"""
import os
import sys
import zipfile

src, out = sys.argv[1], sys.argv[2]
with zipfile.ZipFile(src) as orig, zipfile.ZipFile(out, 'w') as z:
    for info in orig.infolist():
        n = info.filename
        stored = n.endswith(('.gif', '.png', '.jpg'))
        z.write(os.path.join('un', n), n, compress_type=zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED)
print(out, os.path.getsize(out))
