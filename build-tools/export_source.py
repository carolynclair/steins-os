#!/usr/bin/env python3
"""Create a new, curated source-publication directory; never push or overwrite."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
DIRS = ('auto', 'assets', 'build-tools', 'config', 'packaging', 'tests',
        'lab', 'prototype', 'design', '.github')
DOCS = ('ARCHITECTURE.md', 'BUILDING.md', 'PACKAGING.md', 'PROJECT-STATUS.md',
        'RELEASE.md', 'TEST-MATRIX.md', 'UPDATES.md', 'VALIDATION.md',
        'CLAUDE-UI-REVIEW.md', 'PUBLICATION.md')
TOP = ('.gitignore', 'README.md', 'LICENSE', 'LICENSING.md', 'CONTRIBUTING.md',
       'SECURITY.md')
SCREENSHOTS = ('final-hinamizawa.png', 'final-hitogashima.png',
               'terminal-typed-native.png', 'final-meter-popup.png',
               'final-calendar.png', 'final-launcher.png',
               'navigator-real-wayland-settled.png', 'gtk-real-wayland.png',
               'lock-prompt-four-seconds.png')
EXCLUDED_PARTS = {'__pycache__', '.git', 'build', 'node_modules', 'lab-state'}
EXCLUDED_SUFFIXES = {'.pyc', '.iso', '.qcow2', '.img', '.raw', '.vdi', '.vmdk',
                     '.fd', '.pid', '.sock', '.deb', '.xpi', '.ppm'}


def source_files():
    paths = {ROOT / p for p in TOP}
    paths.update(ROOT / 'docs' / p for p in DOCS)
    for folder in DIRS:
        for path in (ROOT / folder).rglob('*'):
            rel = path.relative_to(ROOT)
            if any(part in EXCLUDED_PARTS for part in rel.parts):
                continue
            # Historical design boards are generated; keep their generators/art.
            if rel.parts[0] == 'design' and any(
                    part in {'boards', 'preview', 'evidence'} for part in rel.parts[2:]):
                continue
            if path.is_symlink():
                raise ValueError(f'Symlink requires manual review: {rel}')
            if path.is_file() and path.suffix not in EXCLUDED_SUFFIXES:
                if path.name in {'client_key', 'client_key.pub', 'authorized_keys'}:
                    raise ValueError(f'Key material requires manual review: {rel}')
                paths.add(path)
    paths.add(ROOT / 'evidence/v4-design/VALIDATION.md')
    paths.update(ROOT / 'evidence/v4-design' / p for p in SCREENSHOTS)
    return sorted(paths)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    dest = args.destination.absolute()
    if dest.exists() or dest.is_symlink():
        raise FileExistsError('Destination must be a new directory')
    if dest == ROOT or ROOT in dest.parents:
        raise ValueError('Export outside the development checkout')
    files = source_files()
    for path in files:
        if not path.is_file() or path.is_symlink():
            raise ValueError(f'Missing or unsafe publication input: {path.relative_to(ROOT)}')
        if path.stat().st_size > 10 * 1024 * 1024:
            raise ValueError(f'Unexpected large publication input: {path.relative_to(ROOT)}')
    dest.mkdir(parents=True)
    sanitized = []
    records = []
    for path in files:
        rel = path.relative_to(ROOT)
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        # Public prose/provenance needs no personal workstation home paths.
        if path.suffix == '.md' or path.name == 'PROVENANCE.json':
            before = target.read_text()
            after = re.sub(r'/home/(?:gary|claude|oai)(?=/|\b)', '/home/developer', before)
            if after != before:
                target.write_text(after)
                sanitized.append(str(rel))
        records.append({'path': str(rel), 'bytes': target.stat().st_size,
                        'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
    manifest = {'scope': 'Curated source snapshot; no ISO, VM disks or local lab state',
                'sanitized_prose_and_provenance': sanitized, 'files': records}
    (dest / 'SOURCE-MANIFEST.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'files': len(records), 'bytes': sum(p['bytes'] for p in records),
                      'sanitized_files': len(sanitized), 'destination': str(dest)}, indent=2))


if __name__ == '__main__':
    main()
