#!/usr/bin/env python3
"""Build isolated prototype package; never installs packages on the host."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'prototype/worldline-v4'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=ROOT / 'dist/v4/core')
parser.add_argument('--version', default='0.1.0~prototype7v4.3')
parser.add_argument('--artwork-dir', type=Path, default=ROOT / 'prototype/artwork-v3')
args = parser.parse_args()
OUT = args.output.resolve()
VERSION = args.version
ART = args.artwork_dir.resolve()
subprocess.run(['dpkg', '--validate-version', VERSION], check=True)
OUT.mkdir(parents=True, exist_ok=True)
theme = {
    'manifest_version': 2,
    'name': 'D-Mail — Laboratory', 'version': '0.1.0',
    'description': 'Original graphite and amber theme for Thunderbird. No message or account access.',
    'author': 'Steins;OS contributors',
    'browser_specific_settings': {'gecko': {'id': '{a170e392-21f1-4ca2-9600-ddcc318894ba}', 'strict_min_version': '128.0'}},
    'theme': {'colors': {
        'frame': '#141a20', 'frame_inactive': '#1b242c', 'tab_background_text': '#b9c5cc',
        'tab_selected': '#26333d', 'tab_text': '#f0e8da', 'tab_line': '#e99a45',
        'toolbar': '#1c252d', 'toolbar_text': '#e9e6df', 'toolbar_field': '#11181e',
        'toolbar_field_text': '#e9e6df', 'toolbar_field_border': '#43535e',
        'toolbar_field_focus_border': '#e99a45', 'toolbar_field_highlight': '#303b43',
        'toolbar_field_highlight_text': '#ffffff', 'sidebar': '#171f26',
        'sidebar_text': '#e9e6df', 'sidebar_highlight': '#303b43',
        'sidebar_highlight_text': '#ffffff', 'popup': '#1c252d', 'popup_text': '#e9e6df',
        'popup_highlight': '#303b43', 'popup_highlight_text': '#ffffff',
        'icons': '#bdc9cf', 'icons_attention': '#e99a45',
        'button_background_hover': '#35444f', 'button_background_active': '#303b43',
    }, 'properties': {'color_scheme': 'dark', 'content_color_scheme': 'dark'}}}
with tempfile.TemporaryDirectory(prefix='steins-prototype-') as tmp:
    stage = Path(tmp)
    def write(path, data, executable=False):
        dest = stage / path.lstrip('/')
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(data)
        dest.chmod(0o755 if executable else 0o644)
    def copy(source, dest):
        target = stage / dest.lstrip('/')
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        target.chmod(0o755 if '/bin/' in dest else 0o644)
    for path in (SOURCE / 'bin').iterdir(): copy(path, '/usr/bin/' + path.name)
    for path in (SOURCE / 'lib').glob('*.py'): copy(path, '/usr/lib/steins/' + path.name)
    for name in ('Navigator.qml', 'panel.js'):
        copy(SOURCE / 'share' / name, '/usr/share/steins-prototype/' + name)
    for path in ART.glob('*.png'):
        copy(path, '/usr/share/backgrounds/steins-prototype/' + path.name)
    copy(ART / 'PROVENANCE.json', '/usr/share/doc/steins-plasma-prototype/artwork-provenance.json')
    write('/usr/share/doc/steins-plasma-prototype/copyright',
          (ROOT / 'LICENSE').read_text() + '\nOriginal prototype wallpapers and D-Mail icon: '
          'CC-BY-4.0. Attribution: Steins;OS contributors. New prototype code: MIT.\n')
    xpi = stage / 'usr/share/steins-prototype/dmail-laboratory.xpi'
    xpi.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(xpi, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('manifest.json', json.dumps(theme, indent=2))
    shutil.copyfile(xpi, OUT / xpi.name)
    for name, title, icon in [('steins-navigator', 'Worldlines', 'steins-worldlines'),
                              ('steins-terminal', 'Laboratory Terminal', 'utilities-terminal'),
                              ('steins-dmail', 'D-Mail', 'steins-dmail')]:
        write('/usr/share/applications/' + name + '.desktop',
              '[Desktop Entry]\nType=Application\nName=' + title + '\nExec=' + name +
              '\nIcon=' + icon + '\nCategories=' + ('Network;Email;' if name == 'steins-dmail' else 'Utility;') + '\n')
    write('/usr/share/icons/hicolor/scalable/apps/steins-dmail.svg',
          '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect x="3" y="3" width="58" height="58" rx="14" fill="#17212a"/>'
          '<path d="M14 22h36v26H14z M14 22l18 15 18-15" fill="none" stroke="#e99a45" stroke-width="3" stroke-linejoin="round"/>'
          '<path d="M27 15h20m-6-6 6 6-6 6" fill="none" stroke="#b4c5c9" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/></svg>')
    write('/etc/xdg/plasma-workspace/env/steins-prototype.sh',
          '#!/bin/sh\nexport STEINS_DESKTOP_BACKEND=plasma\n', True)
    write('/etc/xdg/autostart/steins-plasma-prototype.desktop',
          '[Desktop Entry]\nType=Application\nName=Steins worldline session\nExec=steins-prototype-session\nOnlyShowIn=KDE;\n')
    write('/usr/share/dbus-1/services/org.steinsos.Worldline1.service',
          '[D-BUS Service]\nName=org.steinsos.Worldline1\nExec=/usr/bin/steins-worldline-service\n')
    write('/usr/share/doc/steins-plasma-prototype/README',
          'Experimental opt-in Plasma integration, not a release desktop migration.\n'
          'XFCE packages remain for comparison. Real mail uses Thunderbird unchanged.\n'
          'D-Mail theme is optional; install XPI through Thunderbird Add-ons. No personal profiles are modified.\n'
          'No compositor effect is shipped. Motion preferences govern the optional expanded meter.\n')
    write('/DEBIAN/control',
          'Package: steins-plasma-prototype\nVersion: ' + VERSION + '\nArchitecture: all\n'
          'Maintainer: Steins OS contributors <steins@localhost>\nSection: x11\nPriority: optional\n'
          'Depends: steins-desktop (>= 0.1.0-9~prototype1), plasma-desktop, plasma-workspace, konsole, dolphin, '
          'steins-identity-v4 (>= 0.4.0~prototype1), python3, python3-dbus, python3-gi, python3-pyside6.qtquick, python3-pyside6.qtdbus, '
          'qml6-module-qtquick-controls, qml6-module-qtquick-layouts, qml6-module-qtquick-window, '
          'qml6-module-qtqml-workerscript, thunderbird\n'
          'Description: Experimental Steins worldline integration for Plasma 6\n'
          ' Per-user worldline service, navigator, Konsole profiles and optional D-Mail theme.\n')
    subprocess.run(['dpkg-deb', '--root-owner-group', '--build', str(stage), str(OUT / ('steins-plasma-prototype_' + VERSION + '_all.deb'))], check=True)
print(OUT)
