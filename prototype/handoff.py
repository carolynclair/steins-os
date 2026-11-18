#!/usr/bin/env python3
"""Create a bounded source/screenshot handoff, excluding VM disks and build trees."""
import hashlib
import argparse
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=ROOT / 'dist/steins-os-plasma-prototype-handoff-2026-11-01.zip')
parser.add_argument('--brief', type=Path, default=ROOT / 'prototype/CLAUDE-START-HERE.md')
parser.add_argument('--review', type=Path)
parser.add_argument('--prompt', type=Path)
args = parser.parse_args()
output = args.output.resolve()
output.parent.mkdir(parents=True, exist_ok=True)
paths = subprocess.check_output(['git', 'ls-files', '-c', '-o', '--exclude-standard', '-z'], cwd=ROOT).decode().split('\0')
sources = []
for name in paths:
    p = Path(name)
    if not name or not (ROOT / p).is_file(): continue
    if p.parts[0] in ('evidence', 'handoff', '.git', 'build', 'dist') or '__pycache__' in p.parts: continue
    if p.suffix in ('.qcow2', '.fd', '.pid', '.iso', '.zip'): continue
    sources.append(p)
evidence = ROOT / 'evidence/plasma-prototype'
captures = ['desktop-navigator-final.png', 'reboot-desktop.png', 'navigator-coastal.png',
            'meter-wayland.png', 'dmail-compose.png', 'dmail-received.png']
records = ['VALIDATION.md', 'runtime-results.json', 'service-tests.log', 'legacy-tests.log',
           'source-check.log', 'navigator-keyboard.log', 'meter-terminal.log', 'pre-shutdown.log',
           'mail-roundtrip.log', 'reboot-check.log', 'final-session.log', 'disk-check.log',
           'kvm.json', 'block-devices.json', 'spice.json', 'baseline-iso.sha256', 'integration.patch']
files = sorted(set(sources + [Path('evidence/plasma-prototype') / name for name in captures + records]))
payload = {'START-HERE.md': args.brief.read_bytes()}
if args.review: payload['OWNER-REVIEW.txt'] = args.review.read_bytes()
if args.prompt: payload['PROMPT-FOR-CLAUDE.txt'] = args.prompt.read_bytes()
for path in files: payload['steins-os/' + str(path)] = (ROOT/path).read_bytes()
manifest = [{'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
            for name, data in sorted(payload.items())]
with zipfile.ZipFile(output, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    z.writestr('MANIFEST.json', json.dumps(manifest, indent=2) + '\n')
    for name, data in payload.items():
        if name.startswith('steins-os/'):
            # Preserve executable mode/source metadata for scripts.
            z.write(ROOT / name.removeprefix('steins-os/'), name)
        else: z.writestr(name, data)
with zipfile.ZipFile(output) as z:
    assert z.testzip() is None
    for item in manifest:
        assert hashlib.sha256(z.read(item['path'])).hexdigest() == item['sha256']
digest = hashlib.sha256(output.read_bytes()).hexdigest()
output.with_suffix('.zip.sha256').write_text(digest + '  ' + output.name + '\n')
print(output)
print('%d files; %.2f MiB; manifest and ZIP integrity verified' % (len(manifest), output.stat().st_size / 1048576))
print(digest)
