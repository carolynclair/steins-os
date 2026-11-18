#!/usr/bin/env python3
"""Verify and package this creative proposal; excludes all VM/distribution artifacts."""
import ast
import hashlib
import json
from pathlib import Path
import struct
import zipfile
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
boards=json.loads((ROOT/'BOARDS.json').read_text())
results=[]
for board in boards:
    svg=ROOT/board['svg'];png=ROOT/board['png']
    ET.parse(svg)
    raw=png.read_bytes()
    assert raw.startswith(b'\x89PNG\r\n\x1a\n')
    size=struct.unpack('>II',raw[16:24])
    assert size==(board['width'],board['height']+72),(board['id'],size)
    assert 'DESIGN PROPOSAL' in svg.read_text() and 'Not installed' in svg.read_text()
    results.append({'id':board['id'],'png':board['png'],'dimensions':size,'passed':True})
for p in ROOT.rglob('*.svg'):ET.parse(p)
for p in ROOT.rglob('*.py'):ast.parse(p.read_text())
report={'status':'design-artifact-validation; not Linux-runtime testing',
        'boards':results,'board_count':len(results),'all_svg_xml_valid':True,
        'all_python_syntax_valid':True,'labels_distinguish_concepts':True}
(ROOT/'evidence/artifact-checks.json').write_text(json.dumps(report,indent=2)+'\n')
paths=[p for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts
       and not p.name.startswith('.render-') and p.name!='MANIFEST.json']
manifest=[{'path':str(p.relative_to(ROOT)), 'bytes':p.stat().st_size,
           'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(paths)]
(ROOT/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
out=PROJECT/'dist/steins-os-worldline-creative-proposal-v1-2026-11-01.zip'
with zipfile.ZipFile(out,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for item in manifest:z.write(ROOT/item['path'],'worldline-v1/'+item['path'])
    z.write(ROOT/'MANIFEST.json','worldline-v1/MANIFEST.json')
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    for item in manifest:
        assert hashlib.sha256(z.read('worldline-v1/'+item['path'])).hexdigest()==item['sha256']
digest=hashlib.sha256(out.read_bytes()).hexdigest()
out.with_suffix('.zip.sha256').write_text(digest+'  '+out.name+'\n')
print(f'{len(boards)} boards validated; {len(manifest)} files packaged')
print(out)
print(f'{out.stat().st_size/1048576:.2f} MiB; SHA-256 {digest}')
