#!/usr/bin/env python3
"""Synthetic SSH endpoint for the disposable V3 terminal test, never host sshd."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess as sp
import time
import uuid

PROJECT = Path(__file__).resolve().parents[3]
ROOT = PROJECT / 'evidence/v3-integration/lab/ssh-fixture'
STATE = ROOT / 'state.json'
LABEL = 'org.steinsos.fixture'


def docker(*args, **kwargs):
    return sp.run(['docker', *args], check=True, **kwargs)


def load():
    if STATE.is_symlink() or ROOT.is_symlink():
        raise ValueError('Fixture files must not be symlinks')
    state = json.loads(STATE.read_text())
    if not re.fullmatch(r'steins-terminal-ssh-[0-9a-f]{12}', state['container']):
        raise ValueError('Unexpected container name')
    return state


def inspect(state):
    result = sp.run(['docker', 'inspect', state['container']], text=True, capture_output=True)
    if result.returncode:
        return None
    item = json.loads(result.stdout)[0]
    labels = item['Config']['Labels'] or {}
    if item['Id'] != state['container_id'] or labels.get(LABEL) != state['token']:
        raise ValueError('Refusing to operate on a container with a different identity')
    return item


def start():
    if STATE.exists():
        raise FileExistsError('A fixture state already exists; inspect/stop it before preparing a new one')
    if ROOT.is_symlink():
        raise ValueError('Fixture directory must not be a symlink')
    ROOT.mkdir(parents=True, mode=0o700)
    ROOT.chmod(0o700)
    token = uuid.uuid4().hex
    name = 'steins-terminal-ssh-' + token[:12]
    identifier = sp.check_output(['docker', 'run', '-d', '--name', name,
        '--label', LABEL + '=' + token, '-p', '127.0.0.1::2222',
        'steins-os-builder:trixie', 'sleep', 'infinity'], text=True).strip()
    state = {'container': name, 'container_id': identifier, 'token': token,
             'scope': 'synthetic SSH fixture; host loopback only; not shipped', 'running': False}
    STATE.write_text(json.dumps(state, indent=2) + '\n')
    STATE.chmod(0o600)
    try:
        with (ROOT / 'apt.log').open('w') as log:
            docker('exec', name, 'apt-get', 'update', stdout=log, stderr=sp.STDOUT)
            docker('exec', name, 'apt-get', 'install', '-y', '--no-install-recommends', 'openssh-server', stdout=log, stderr=sp.STDOUT)
        docker('exec', name, 'sh', '-c', 'pkill -x sshd || true; mkdir -p /run/sshd; useradd -m -s /bin/bash labremote; mkdir -p /home/labremote/.ssh; chmod 700 /home/labremote/.ssh')
        # Random test-only password unlocks the Unix account. Password login is
        # disabled in sshd; no personal password or host account is involved.
        docker('exec', '-i', name, 'chpasswd', input=('labremote:' + uuid.uuid4().hex + '\n').encode())
        docker('exec', name, 'ssh-keygen', '-q', '-t', 'ed25519', '-N', '', '-C', 'steins-synthetic-fixture-only', '-f', '/tmp/client_key')
        docker('exec', name, 'sh', '-c', 'cp /tmp/client_key.pub /home/labremote/.ssh/authorized_keys; chmod 600 /home/labremote/.ssh/authorized_keys; chown -R labremote:labremote /home/labremote/.ssh')
        config = '''Port 2222
ListenAddress 0.0.0.0
HostKey /etc/ssh/ssh_host_ed25519_key
PidFile /run/steins-sshd.pid
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
UsePAM no
PermitRootLogin no
PermitEmptyPasswords no
AllowUsers labremote
AuthorizedKeysFile .ssh/authorized_keys
StrictModes yes
DisableForwarding yes
PermitUserEnvironment no
PermitTTY yes
PrintMotd no
PrintLastLog no
LogLevel VERBOSE
'''
        docker('exec', '-i', name, 'sh', '-c', 'cat > /tmp/steins-sshd.conf', input=config.encode())
        profile = '''export PS1='remote@fixture:\\w$ '
if test -t 0; then
  printf '\\nSteins;OS synthetic SSH fixture / no external relay\\n'
  printf 'REMOTE_TTY=%s\\n' "$(tty)"
  printf 'REMOTE_PID=%s\\n' "$$"
  printf 'UNICODE=λ → Δ 日本語\\n'
fi
'''
        docker('exec', '-i', name, 'sh', '-c', 'cat > /home/labremote/.bash_profile; chown labremote:labremote /home/labremote/.bash_profile', input=profile.encode())
        docker('exec', name, '/usr/sbin/sshd', '-t', '-f', '/tmp/steins-sshd.conf')
        docker('exec', name, '/usr/sbin/sshd', '-f', '/tmp/steins-sshd.conf', '-E', '/tmp/steins-sshd.log')
        details = inspect(state)
        binding = details['NetworkSettings']['Ports']['2222/tcp']
        if len(binding) != 1 or binding[0]['HostIp'] != '127.0.0.1':
            raise ValueError('SSH fixture is not bound exclusively to host loopback')
        port = int(binding[0]['HostPort'])
        hostkey = sp.check_output(['docker', 'exec', name, 'cat', '/etc/ssh/ssh_host_ed25519_key.pub'], text=True).split()
        keyline = ' '.join(hostkey[:2])
        for remote, local in [('/tmp/client_key', 'client_key'), ('/tmp/client_key.pub', 'client_key.pub')]:
            (ROOT / local).write_bytes(sp.check_output(['docker', 'exec', name, 'cat', remote]))
            (ROOT / local).chmod(0o600)
        (ROOT / 'known_hosts').write_text('[10.0.2.2]:' + str(port) + ' ' + keyline + '\n')
        (ROOT / 'known_hosts').chmod(0o600)
        state.update(running=True, host_address='127.0.0.1', guest_address='10.0.2.2', port=port,
            username='labremote', client_key=str((ROOT / 'client_key').relative_to(PROJECT)),
            known_hosts=str((ROOT / 'known_hosts').relative_to(PROJECT)),
            host_key_fingerprint=sp.check_output(['docker', 'exec', name, 'ssh-keygen', '-lf', '/etc/ssh/ssh_host_ed25519_key.pub'], text=True).strip(),
            openssh=sp.check_output(['docker', 'exec', name, 'dpkg-query', '-W', 'openssh-server'], text=True).strip())
        STATE.write_text(json.dumps(state, indent=2) + '\n')
        # Only read the public SSH banner to establish bounded server readiness.
        with socket.create_connection(('127.0.0.1', port), timeout=5) as client:
            client.settimeout(5)
            state['banner'] = client.recv(256).decode().strip()
        STATE.write_text(json.dumps(state, indent=2) + '\n')
        print(json.dumps({k: v for k, v in state.items() if k not in ('token', 'container_id')}, indent=2))
    except BaseException:
        stop()
        raise


def stop():
    state = load()
    if inspect(state):
        docker('rm', '-f', state['container'], stdout=sp.DEVNULL)
    for name in ('client_key', 'client_key.pub', 'known_hosts'):
        path = ROOT / name
        if path.is_symlink():
            raise ValueError('Refusing to remove redirected fixture file')
        path.unlink(missing_ok=True)
    state.update(running=False, container_removed=True, private_fixture_files_removed=True)
    STATE.write_text(json.dumps(state, indent=2) + '\n')
    print('Only the owned synthetic SSH container and generated key files were removed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['start', 'status', 'stop'])
    action = parser.parse_args().action
    if action == 'start':
        start()
    elif action == 'stop':
        stop()
    else:
        state = load()
        print(json.dumps({**state, 'container_present': bool(inspect(state))}, indent=2))
