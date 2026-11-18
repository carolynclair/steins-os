#!/usr/bin/env python3
"""Check actual .deb ownership, safe paths, maintainer scripts and moved CLIs."""
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

root = Path(__file__).resolve().parents[1]
directory = Path(sys.argv[1]) if len(sys.argv) > 1 else root / 'dist/packages'
manifest = json.loads((directory / 'manifest.json').read_text())
expected = {'steins-artwork', 'steins-desktop', 'steins-branding', 'steins-live-installer'}
assert {p['package'] for p in manifest['packages']} == expected
owned = {}
with tempfile.TemporaryDirectory(prefix='steins-package-check-') as temporary:
    base = Path(temporary)
    for package in manifest['packages']:
        path = directory / package['file']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == package['sha256']
        data = subprocess.check_output(['dpkg-deb', '--fsys-tarfile', str(path)])
        target = base / package['package']
        target.mkdir()
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            for member in archive.getmembers():
                name = member.name.removeprefix('./')
                assert not name.startswith('/') and '..' not in Path(name).parts
                assert not name.startswith('usr/local/'), name
                if member.isfile():
                    assert name not in owned, f'overlapping package ownership: {name}'
                    owned[name] = package['package']
                    if name.startswith('usr/bin/'):
                        assert member.mode & 0o111, name
            archive.extractall(target, filter='data')
        control = base / (package['package'] + '-control')
        subprocess.run(['dpkg-deb', '--control', str(path), str(control)], check=True)
        for script in ('preinst', 'postinst', 'postrm'):
            if (control / script).exists():
                subprocess.run(['sh', '-n', str(control / script)], check=True)
        for line in (control / 'conffiles').read_text().splitlines() if (control / 'conffiles').exists() else []:
            assert line.startswith('/etc/') and (target / line.lstrip('/')).is_file()
            assert line != '/etc/os-release', 'First install must replace Debian identity, not preserve it as an admin conffile'
    assert owned['etc/os-release'] == 'steins-branding'
    assert 'etc/issue' not in owned
    assert 'etc/lightdm/lightdm-gtk-greeter.conf' not in owned
    assert 'etc/calamares/settings.conf' not in owned
    assert owned['usr/bin/steins-worldline'] == 'steins-desktop'
    assert owned['usr/lib/steins/steinslib.py'] == 'steins-desktop'
    assert owned['usr/bin/install-steins-os'] == 'steins-live-installer'
    assert 'etc/skel/Desktop/steins-install.desktop' not in owned
    desktop = base / 'steins-desktop'
    env = dict(os.environ, STEINS_ETC_DIR=str(desktop / 'etc/steins'),
               STEINS_HOME=str(base / 'home'), PYTHONDONTWRITEBYTECODE='1')
    result = subprocess.run([sys.executable, str(desktop / 'usr/bin/steins-worldline'), 'list'],
                            env=env, text=True, capture_output=True, check=True)
    for name in ('alpha', 'steins-gate', 'hinamizawa', 'hitogashima', 'lugunica', 'mitakihara'):
        assert name in result.stdout
print('PASS: four .debs, unique ownership, no /usr/local payload, config/scripts, relocated worldline CLI and all six packs')
