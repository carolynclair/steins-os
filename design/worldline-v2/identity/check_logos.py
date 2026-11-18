#!/usr/bin/python3
"""Verify tiny raster visibility/bounds; does not measure brand recognition."""
import json
from pathlib import Path
from PySide6.QtGui import QImage

ROOT=Path(__file__).resolve().parent
rows=[]
for path in sorted((ROOT/'sizes').glob('*.png')):
    expected=int(path.stem.rsplit('-',1)[1])
    image=QImage(str(path))
    assert not image.isNull(),path
    assert (image.width(),image.height())==(expected,expected),path
    pixels=[(x,y) for y in range(expected) for x in range(expected)
            if image.pixelColor(x,y).alpha()>=64]
    assert pixels,path
    bounds=[min(x for x,y in pixels),min(y for x,y in pixels),
            max(x for x,y in pixels),max(y for x,y in pixels)]
    clear=bounds[0]>0 and bounds[1]>0 and bounds[2]<expected-1 and bounds[3]<expected-1
    assert clear,path
    rows.append({'file':path.name,'size':[expected,expected],
                 'alpha_ge_64_pixels':len(pixels),'bounds':bounds,'not_clipped':clear})
assert len(rows)==12
(ROOT/'RASTER-CHECKS.json').write_text(json.dumps({
    'scope':'Rendering bounds/visible ink, not user-recognition testing','checks':rows},indent=2)+'\n')
print('PASS: 12 logo rasters have expected dimensions, visible ink and clear margins')
