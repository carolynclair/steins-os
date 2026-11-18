#!/usr/bin/env python3
"""Validate source contracts that prevent an unbootable or unlaunchable image."""
from pathlib import Path
import ast, subprocess, sys, xml.etree.ElementTree as ET
r=Path(__file__).resolve().parents[1]; o=r/'config/includes.chroot'
for p in [r/'auto/config',r/'build-tools/build.sh',*r.glob('config/hooks/live/*'),*o.glob('usr/local/bin/*'),r/'packaging/configure-system']:
 if not p.is_file():continue
 s=p.read_text()
 if s.startswith('#!/bin/sh') or s.startswith('#!/bin/bash'):subprocess.run(['bash','-n',str(p)],check=True)
 elif s.startswith('#!/usr/bin/python3'):ast.parse(s)
for p in o.rglob('*.xml'):ET.parse(p)
for p in o.rglob('*.svg'):ET.parse(p)
packages=set((r/'config/package-lists/steins.list.chroot').read_text().split())
assert {'live-boot','linux-image-amd64','calamares','calamares-settings-debian','python3-yaml','zenity','lightdm','xfce4'}<=packages
assert {'python3-gi','librsvg2-bin','conky-all','mate-polkit'}<=packages
assert 'console-setup' in packages, 'Calamares keyboard preview needs ckbcomp from console-setup'
for frontend in ('grub-efi', 'grub-pc'):
 assert frontend in (r / f'config/package-lists/{frontend}.list.binary').read_text().split(), f'offline installer needs {frontend} in the media pool'
assert 'calamares-install-debian' in (o/'usr/local/bin/install-steins-os').read_text()
assert '/usr/bin/calamares-install-debian' in (r/'packaging/configure-system').read_text()
assert 'prompt-install' in (r/'packaging/configure-system').read_text()
assert 'SetDisplayPasswordFunction' in (o/'usr/share/plymouth/themes/steins/steins.script').read_text()
print('PASS: shell/Python/XML/SVG syntax, package prerequisites, installer launcher, install confirmation, boot password rendering')
subprocess.run([sys.executable,str(r/'tests/check_ui.py')],check=True,env={**__import__('os').environ,'PYTHONDONTWRITEBYTECODE':'1'})
print('PASS: UI contract tests (tests/check_ui.py)')
