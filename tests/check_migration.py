#!/usr/bin/env python3
"""Run only in a disposable container: exercise actual legacy-file preinst logic."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

if os.environ.get('STEINS_DISPOSABLE_CONTAINER') != '1' or not Path('/.dockerenv').exists() or os.geteuid() != 0:
    raise SystemExit('Run inside the disposable builder container with STEINS_DISPOSABLE_CONTAINER=1')
source = Path('/src/config/includes.chroot')
binary = Path('/usr/local/bin/steins-worldline')
library = Path('/usr/local/lib/steins/steinslib.py')
with tempfile.TemporaryDirectory() as temporary:
    package = next(Path('/src/dist/packages').glob('steins-desktop_*_all.deb'))
    subprocess.run(['dpkg-deb', '--control', str(package), temporary], check=True)
    script = Path(temporary) / 'preinst'
    for p in (binary, library):
        p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / p.relative_to('/'), p)
    binary.chmod(0o755)
    original_binary = binary.read_bytes()
    original_library = library.read_bytes()
    binary.write_bytes(original_binary + b'\n# administrator override\n')
    subprocess.run(['sh', str(script), 'install'], check=True)
    assert binary.read_bytes().endswith(b'# administrator override\n')
    assert library.exists(), 'An edited legacy script must retain its companion private library'
    assert library.read_bytes() == original_library
    binary.write_bytes(original_binary)
    subprocess.run(['sh', str(script), 'install'], check=True)
    assert not binary.exists() and not library.exists(), 'Known legacy release files should migrate'
    for p, content in ((binary, original_binary), (library, original_library)):
        backup = Path('/var/lib/steins/legacy') / p.relative_to('/')
        assert backup.read_bytes() == content
    subprocess.run(['sh', str(script), 'upgrade'], check=True)
    for p, content in ((binary, original_binary), (library, original_library)):
        p.write_bytes(content)
    backup = Path('/var/lib/steins/legacy') / binary.relative_to('/')
    backup.write_bytes(b'# differing earlier backup\n' + original_binary)
    subprocess.run(['sh', str(script), 'upgrade'], check=True)
    assert binary.exists() and library.exists(), 'A backup conflict must not split the legacy script/library group'
    branding = next(Path('/src/dist/packages').glob('steins-branding_*_all.deb'))
    control = Path(temporary) / 'branding'
    subprocess.run(['dpkg-deb', '--control', str(branding), str(control)], check=True)
    debootstrap = Path('/etc/os-release.debootstrap')
    debootstrap.write_bytes(Path('/usr/lib/os-release').read_bytes() + b'\nBUILD_FIXTURE=debootstrap\n')
    subprocess.run(['dpkg-divert', '--local', '--add', '--no-rename', '--divert', str(debootstrap), '/etc/os-release'], check=True)
    subprocess.run(['sh', str(control / 'preinst'), 'install'], check=True)
    owner = subprocess.check_output(['dpkg-divert', '--listpackage', '/etc/os-release'], text=True).strip()
    assert owner == 'steins-branding'
    assert Path('/etc/os-release.debian').read_bytes() == debootstrap.read_bytes()
print('PASS: edited legacy overrides keep their library, known files back up, repeated migration is harmless')
print('PASS: live-build debootstrap diversion hands over to the identity package')
