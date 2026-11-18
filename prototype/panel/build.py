#!/usr/bin/env python3
"""Build a separate, opt-in panel package without installing anything."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).resolve().parent
OUT = ROOT / 'dist/v3/panel'
VERSION = '0.1.0~prototype2'
OUT.mkdir(parents=True, exist_ok=True)
package = OUT / ('steins-worldline-panel_' + VERSION + '_all.deb')
with tempfile.TemporaryDirectory(prefix='steins-panel-build-') as tmp:
    stage = Path(tmp)
    dest = stage / 'usr/share/plasma/plasmoids/org.steinsos.worldline'
    shutil.copytree(SOURCE / 'package', dest)
    doc = stage / 'usr/share/doc/steins-worldline-panel'
    doc.mkdir(parents=True)
    shutil.copyfile(ROOT / 'LICENSE', doc / 'copyright')
    shutil.copyfile(SOURCE / 'README.md', doc / 'README.md')
    helper = stage / 'usr/share/steins-panel/attach.js'
    helper.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE / 'attach.js', helper)
    control = stage / 'DEBIAN/control'
    control.parent.mkdir()
    control.write_text('Package: steins-worldline-panel\nVersion: '+VERSION+'\nArchitecture: all\n'
        'Maintainer: Steins OS contributors <steins@localhost>\nSection: x11\nPriority: optional\n'
        'Depends: steins-plasma-prototype (>= 0.1.0~prototype6), plasma-workspace (>= 4:6.3), plasma-desktoptheme, '
        'qml6-module-qtquick, qml6-module-qtquick-controls, qml6-module-qtquick-layouts, qml6-module-org-kde-kirigami\n'
        'Description: Experimental compact Steins worldline panel instrument\n'
        ' Live shared-service state, worldline selection and motion preferences.\n'
        ' No panel layout is changed automatically.\n')
    for p in stage.rglob('*'):
        p.chmod(0o755 if p.is_dir() else 0o644)
    subprocess.run(['dpkg-deb', '--root-owner-group', '--build', str(stage), str(package)], check=True)
print(json.dumps({'package':str(package),'sha256':hashlib.sha256(package.read_bytes()).hexdigest(),'bytes':package.stat().st_size,'host_installed':False},indent=2))
