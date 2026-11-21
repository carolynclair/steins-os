#!/usr/bin/env python3
"""Package the already-built terminal inside the disposable Debian container."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'prototype/surfaces-v4/terminal'
OUT = ROOT / 'dist/v4/surfaces/terminal'
VERSION = '0.3.0~v4.2'
binary = OUT / 'build/steins-terminal-v3'
if not binary.is_file():
    raise SystemExit('Build the terminal in Debian13 before packaging')

with tempfile.TemporaryDirectory(prefix='steins-terminal-package-') as tmp:
    stage = Path(tmp)
    def write(name, content):
        path = stage / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    def copy(path, name):
        target = stage / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    copy(binary, 'usr/bin/steins-terminal-v3')
    write('usr/share/applications/steins-terminal-v3.desktop',
          '[Desktop Entry]\nType=Application\nName=Steins;OS Terminal\n'
          'Comment=Worldline-aware terminal using maintained QTermWidget 6\nExec=steins-terminal-v3\n'
          'Icon=utilities-terminal\nTerminal=false\nCategories=System;TerminalEmulator;Utility;\n'
          'StartupWMClass=steins-terminal-v3\nKeywords=shell;console;worldline;\n')
    for path in SOURCE.rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            copy(path, 'usr/share/doc/steins-terminal-v3/source/' + str(path.relative_to(SOURCE)))
    copy(Path('/usr/share/common-licenses/GPL-2'), 'usr/share/doc/steins-terminal-v3/GPL-2')
    copy(Path('/usr/share/doc/libqtermwidget6-2/copyright'), 'usr/share/doc/steins-terminal-v3/qtermwidget-copyright')
    write('usr/share/doc/steins-terminal-v3/copyright',
          'Steins;OS original frontend source: Copyright 2026 Steins;OS contributors, MIT.\n'
          'See source/LICENSE for the MIT grant. The linked executable is distributed under\n'
          'GPL-2-or-later because QTermWidget contains GPL-2+ / LGPL-2+ components.\n'
          'GPL-2 and qtermwidget-copyright are included. Upstream engine is unmodified\n'
          'and supplied by Debian libqtermwidget6-2, not copied into this package.\n'
          'Source/build instructions for this frontend are in source/.\n')
    debian = stage / 'debian'
    debian.mkdir()
    (debian / 'control').write_text('Source: steins-terminal-v3\nSection: x11\nPriority: optional\n'
        'Maintainer: Steins OS contributors <steins@localhost>\n\n'
        'Package: steins-terminal-v3\nArchitecture: any\nDescription: Experimental Steins terminal\n')
    dependencies = subprocess.check_output(['dpkg-shlibdeps', '-O', '-e' + str(stage / 'usr/bin/steins-terminal-v3')], cwd=stage, text=True).strip().split('=', 1)[1]
    shutil.rmtree(debian)
    write('DEBIAN/control', 'Package: steins-terminal-v3\nVersion: ' + VERSION + '\nArchitecture: amd64\n'
          'Maintainer: Steins OS contributors <steins@localhost>\nSection: x11\nPriority: optional\n'
          'Depends: ' + dependencies + ', qtermwidget-data, steins-identity-v4 (>= 0.4.0~prototype1)\n'
          'Recommends: qt6-wayland, konsole\n'
          'Description: Experimental worldline-aware Steins OS terminal\n'
          ' Original tabs and linked session rail around maintained QTermWidget 6.\n'
          ' Updates supported palette surfaces without restarting shell processes.\n'
          ' Does not replace Konsole or change existing default terminal settings.\n')
    package = OUT / ('steins-terminal-v3_' + VERSION + '_amd64.deb')
    subprocess.run(['dpkg-deb', '--root-owner-group', '--build', str(stage), str(package)], check=True)
    result = {'package': str(package.relative_to(ROOT)), 'version': VERSION,
              'sha256': hashlib.sha256(package.read_bytes()).hexdigest(),
              'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
              'depends': dependencies + ', qtermwidget-data, steins-identity-v4 (>= 0.4.0~prototype1)',
              'desktop_id': 'steins-terminal-v3', 'source_included': True,
              'host_install_performed': False}
    (OUT / 'PACKAGE.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
