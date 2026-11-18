#!/usr/bin/env python3
"""Build/test/package in an owned disposable container; no host apt actions."""
from pathlib import Path
import json
import os
import subprocess as sp
import uuid

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'dist/v4/surfaces/terminal'
OUT.mkdir(parents=True, exist_ok=True)
name = 'steins-terminal-v4-build-' + uuid.uuid4().hex[:10]
image = 'steins-os-builder:trixie'
created = False
try:
    sp.run(['docker', 'run', '-d', '--name', name, '-v', str(ROOT) + ':/work', '-w', '/work', image, 'sleep', 'infinity'], check=True)
    created = True
    with (OUT / 'apt-build.log').open('w') as log:
        for command in [['apt-get', 'update'], ['apt-get', 'install', '-y', '--no-install-recommends',
                        'build-essential', 'cmake', 'qt6-base-dev', 'libqtermwidget-dev', 'libutf8proc-dev',
                        'python3-pyside6.qtquick', 'python3-pyside6.qttest', 'qml6-module-qtquick-controls',
                        'qml6-module-qtquick-layouts', 'qml6-module-qtquick-window', 'qml6-module-qtqml-workerscript']]:
            sp.run(['docker', 'exec', name, *command], stdout=log, stderr=sp.STDOUT, check=True)
    uid = str(os.getuid()) + ':' + str(os.getgid())
    def run(command, logfile):
        with (OUT / logfile).open('w') as log:
            sp.run(['docker', 'exec', '--user', uid, name, *command], stdout=log, stderr=sp.STDOUT, check=True)
    run(['cmake', '-S', 'prototype/surfaces-v4/terminal', '-B', 'dist/v4/surfaces/terminal/build', '-DCMAKE_BUILD_TYPE=Release'], 'configure.log')
    run(['cmake', '--build', 'dist/v4/surfaces/terminal/build', '-j2'], 'build.log')
    run(['sh', '-c', 'mkdir -p /tmp/steins-terminal-fixture/runtime /tmp/steins-terminal-fixture/home && chmod 700 /tmp/steins-terminal-fixture/runtime && HOME=/tmp/steins-terminal-fixture/home XDG_RUNTIME_DIR=/tmp/steins-terminal-fixture/runtime QT_QPA_PLATFORM=offscreen LANG=C.UTF-8 /work/dist/v4/surfaces/terminal/build/steins-terminal-tests -v1'], 'engine-tests.log')
    run(['python3', 'prototype/surfaces-v4/tests/test_tokens.py'], 'token-tests.log')
    run(['sh', '-c', 'XDG_RUNTIME_DIR=/tmp/steins-terminal-fixture/runtime QT_QPA_PLATFORM=offscreen QT_QUICK_BACKEND=software LANG=C.UTF-8 python3 prototype/surfaces-v4/tests/qml_probe.py'], 'qml-tests.log')
    run(['python3', 'prototype/surfaces-v4/terminal/package.py'], 'package.log')
    run(['python3', 'prototype/surfaces-v4/build.py'], 'surfaces-package.log')
    versions = sp.check_output(['docker', 'exec', name, 'dpkg-query', '-W', 'libqtermwidget-dev', 'libqtermwidget6-2', 'qt6-base-dev', 'cmake', 'g++'], text=True)
    (OUT / 'BUILD-ENVIRONMENT.json').write_text(json.dumps({'builder_image': image,
        'image_id': sp.check_output(['docker', 'inspect', '--format={{.Image}}', name], text=True).strip(),
        'packages': versions.splitlines(), 'host_packages_installed': False}, indent=2) + '\n')
    print((OUT / 'PACKAGE.json').read_text())
finally:
    if created:
        sp.run(['docker', 'rm', '-f', name], check=True)
