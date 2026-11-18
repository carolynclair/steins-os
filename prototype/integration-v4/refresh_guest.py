#!/usr/bin/python3
"""Refresh only the owned service/preset in this disposable guest."""
import json,os,signal,socket,subprocess,time
from pathlib import Path
import dbus
assert os.getuid()==1000 and socket.gethostname()=='steins-prototype'
assert subprocess.check_output(['systemd-detect-virt','--vm'],text=True).strip() in ('qemu','kvm')
os.environ.update(DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/1000/bus',XDG_RUNTIME_DIR='/run/user/1000',WAYLAND_DISPLAY='wayland-0',STEINS_DESKTOP_BACKEND='plasma',XDG_MENU_PREFIX='plasma-')
bus=dbus.SessionBus();name='org.steinsos.Worldline1'
if bus.name_has_owner(name):
    owner=bus.get_name_owner(name)
    daemon=dbus.Interface(bus.get_object('org.freedesktop.DBus','/org/freedesktop/DBus'),'org.freedesktop.DBus')
    pid=int(daemon.GetConnectionUnixProcessID(owner))
    assert Path('/proc',str(pid),'cmdline').read_bytes().split(b'\0')[:2]==[b'/usr/bin/python3',b'/usr/bin/steins-worldline-service']
    os.kill(pid,signal.SIGTERM)
    for _ in range(100):
        if not bus.name_has_owner(name) or bus.get_name_owner(name)!=owner:break
        time.sleep(.05)
    else:raise RuntimeError('Old service did not stop')
api=dbus.Interface(bus.get_object(name,'/org/steinsos/Worldline'),name)
state=json.loads(api.ApplyCurrent(timeout=65))
assert state['applied'] is True,state
print(json.dumps(state))
subprocess.run(['python3','/usr/share/steins-v4/panel/apply.py','--replace-v3'],check=True)
subprocess.run(['kbuildsycoca6','--noincremental'],check=True)
