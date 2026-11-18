#!/usr/bin/python3
"""Package the V4 navigator/preset without installing or configuring anything."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[1]
OUT = ROOT / 'dist/v4/surfaces'
VERSION = '0.4.0~prototype1'
OUT.mkdir(parents=True, exist_ok=True)
with tempfile.TemporaryDirectory(prefix='steins-surfaces-v4-package-') as temp:
    stage = Path(temp)
    def copy(source, dest, mode=0o644):
        target = stage / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(mode)
    def write(dest, content):
        target = stage / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    for source in (SOURCE / 'bin').iterdir():
        if source.is_file(): copy(source, 'usr/bin/' + source.name, 0o755)
    for source in (SOURCE / 'share').iterdir():
        if source.is_file(): copy(source, 'usr/share/steins-v4/' + source.name)
    copy(SOURCE / 'README.md', 'usr/share/doc/steins-surfaces-v4/README.md')
    copy(SOURCE / 'terminal/LICENSE', 'usr/share/doc/steins-surfaces-v4/copyright')
    for subdir in ('bin', 'share', 'tests'):
        for source in (SOURCE / subdir).rglob('*'):
            if source.is_file() and '__pycache__' not in source.parts:
                copy(source, 'usr/share/doc/steins-surfaces-v4/source/' + str(source.relative_to(SOURCE)))
    copy(SOURCE / 'build.py', 'usr/share/doc/steins-surfaces-v4/source/build.py')
    write('usr/share/applications/steins-navigator-v4.desktop',
          '[Desktop Entry]\nType=Application\nName=Worldlines\nComment=Choose the atmosphere of your Steins;OS desktop\n'
          'Exec=steins-navigator-v4\nIcon=steins-navigator-v4\nTerminal=false\nCategories=Settings;DesktopSettings;\n'
          'StartupWMClass=steins-navigator-v4\nKeywords=worldline;divergence;appearance;\n')
    write('DEBIAN/control', 'Package: steins-surfaces-v4\nVersion: ' + VERSION + '\nArchitecture: all\n'
          'Maintainer: Steins OS contributors <steins@localhost>\nSection: x11\nPriority: optional\n'
          'Depends: steins-identity-v4 (>= 0.4.0~prototype1), steins-plasma-prototype (>= 0.1.0~prototype7v4.1), '
          'python3, python3-dbus, python3-pyside6.qtquick, python3-pyside6.qtdbus, '
          'qml6-module-qtquick-controls, qml6-module-qtquick-layouts, qml6-module-qtquick-window, '
          'qml6-module-qtqml-workerscript, libkf6config-bin\n'
          'Description: Experimental neutral Steins OS native surface styling\n'
          ' Token-driven worldline navigator and explicit guest-only Breeze preset.\n'
          ' Uses the shared session service and does not create a second state store.\n')
    package = OUT / ('steins-surfaces-v4_' + VERSION + '_all.deb')
    subprocess.run(['dpkg-deb', '--root-owner-group', '--build', str(stage), str(package)], check=True)
    result = {'package': str(package.relative_to(ROOT)), 'version': VERSION,
              'sha256': hashlib.sha256(package.read_bytes()).hexdigest(),
              'desktop_id': 'steins-navigator-v4.desktop', 'automatic_configuration': False,
              'host_install_performed': False}
    (OUT / 'PACKAGE.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
