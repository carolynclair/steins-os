#!/usr/bin/python3
"""Explicit V4 guest presets; normal reboot subsequently refreshes UI code."""
import os
from pathlib import Path
import socket
import subprocess as sp

assert os.getuid() == 1000 and socket.gethostname() == 'steins-prototype'
assert sp.check_output(['systemd-detect-virt', '--vm'], text=True).strip() in ('kvm', 'qemu')
assert Path('/usr/share/steins-v4/tokens.json').is_file()
os.environ.update(DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/1000/bus',
    XDG_RUNTIME_DIR='/run/user/1000', WAYLAND_DISPLAY='wayland-0', STEINS_DESKTOP_BACKEND='plasma')
sp.run(['python3', '/usr/share/steins-v4/panel/apply.py', '--replace-v3'], check=True)
sp.run(['steins-v4-window-preset', '--apply'], check=True)
print('V4 guest presets saved with backups; reboot this disposable guest to activate all code/caches.')
