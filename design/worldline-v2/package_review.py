#!/usr/bin/env python3
"""Validate and package V2 review artifacts; never reads/writes a VM image."""
import ast
import hashlib
import json
from pathlib import Path
import re
import struct
from urllib.parse import unquote
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
OUTPUT = PROJECT / 'dist/steins-os-v2-review-2026-11-02.zip'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    if OUTPUT.exists():
        raise FileExistsError('Review archives are never overwritten: ' + str(OUTPUT))
    boards = json.loads((ROOT / 'BOARDS.json').read_text())
    checks = []
    for board in boards:
        svg, png = ROOT / board['svg'], ROOT / board['png']
        element = ET.parse(svg).getroot()
        raw = png.read_bytes()
        assert raw[:8] == b'\x89PNG\r\n\x1a\n', png
        dimensions = struct.unpack('>II', raw[16:24])
        expected = (board['width'], board['height'] + 72)
        assert dimensions == expected, (png, dimensions)
        assert (int(element.attrib['width']), int(element.attrib['height'])) == expected
        text = svg.read_text()
        assert 'DESIGN PROPOSAL' in text and 'Not installed' in text, svg
        checks.append({'id': board['id'], 'dimensions': dimensions, 'passed': True})
    for path in ROOT.rglob('*.svg'):
        ET.parse(path)
    for path in ROOT.rglob('*.py'):
        ast.parse(path.read_text(), filename=str(path))
    links = 0
    for path in ROOT.rglob('*.md'):
        for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', path.read_text()):
            target = target.strip('<>').split('#')[0]
            if not target or re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target):
                continue
            resolved = path.parent / unquote(target)
            assert resolved.exists(), (path, target)
            assert resolved.resolve().is_relative_to(ROOT), (path, 'nonportable link', target)
            links += 1
    report = {'scope': 'design/source artifact checks, not Linux runtime tests',
              'board_count': len(boards), 'boards': checks,
              'all_svg_xml_valid': True, 'all_python_syntax_valid': True,
              'local_markdown_links_checked': links, 'proposal_labels_present': True}
    (ROOT / 'evidence/artifact-checks.json').write_text(json.dumps(report, indent=2) + '\n')
    paths = []
    for path in sorted(ROOT.rglob('*')):
        if '__pycache__' in path.parts or path.name.startswith('.render-'):
            continue
        if path.is_symlink():
            raise ValueError('Review must not contain symlinks: ' + str(path))
        if not path.is_file() or path.name == 'MANIFEST.json':
            continue
        if path.suffix in {'.qcow2', '.iso', '.fd', '.pid', '.sock', '.pyc'}:
            raise ValueError('VM/runtime artifact excluded from review: ' + str(path))
        paths.append(path)
    manifest = [{'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size,
                 'sha256': digest(path)} for path in paths]
    (ROOT / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
    with zipfile.ZipFile(OUTPUT, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for item in manifest:
            archive.write(ROOT / item['path'], 'worldline-v2/' + item['path'])
        archive.write(ROOT / 'MANIFEST.json', 'worldline-v2/MANIFEST.json')
    with zipfile.ZipFile(OUTPUT) as archive:
        assert archive.testzip() is None
        for item in manifest:
            actual = hashlib.sha256(archive.read('worldline-v2/' + item['path'])).hexdigest()
            assert actual == item['sha256'], item['path']
    checksum = digest(OUTPUT)
    OUTPUT.with_suffix('.zip.sha256').write_text(checksum + '  ' + OUTPUT.name + '\n')
    print(json.dumps({'archive': str(OUTPUT), 'boards': len(boards),
                      'files': len(manifest) + 1, 'bytes': OUTPUT.stat().st_size,
                      'sha256': checksum, 'archive_crc_and_file_hashes_pass': True}, indent=2))


if __name__ == '__main__':
    main()
