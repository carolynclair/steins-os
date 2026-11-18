#!/usr/bin/env python3
"""Replay tested meter/service source fixes in the named V2 fork only.

No host root, packages, image rebuild or Plymouth deployment. Original guest
files are backed up, and cold reset restores the inherited baseline.
"""
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import uuid
from vm_lab import Lab

lab=Lab();lab.qmp('query-status');lab.login()
entries=[
 ('config/includes.chroot/usr/local/bin/steins-meter','/usr/bin/steins-meter','755'),
 ('config/includes.chroot/usr/local/lib/steins/meterlib.py','/usr/lib/steins/meterlib.py','644'),
 ('prototype/worldline/lib/worldline_service.py','/usr/lib/steins/worldline_service.py','644'),
]
commands=['set -e','mkdir -p /tmp/v2-validation/source-fix-backups']
expected=[]
for source,target,mode in entries:
    path=lab.project/source
    name='patch-'+uuid.uuid4().hex[:12]+'-'+path.name
    subprocess.run([sys.executable,str(Path(__file__).with_name('push_guest.py')),str(path),'--name',name],check=True)
    backup='/tmp/v2-validation/source-fix-backups/'+Path(target).name+'.packaged'
    commands.append('if [ -e '+shlex.quote(backup)+' ]; then :; else sudo -n cp -p '+shlex.quote(target)+' '+shlex.quote(backup)+'; fi')
    commands.append('sudo -n install -m '+mode+' '+shlex.quote('/tmp/v2-validation/'+name)+' '+shlex.quote(target))
    expected.append({'source':source,'guest_target':target,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
commands+=['pkill -TERM -f "^/usr/bin/python3 /usr/bin/steins-worldline-service$" || true',
           'pkill -TERM -f "^/usr/bin/python3 /usr/bin/steins-meter$" || true',
           'export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 STEINS_DESKTOP_BACKEND=plasma',
           'gdbus call --session --dest org.steinsos.Worldline1 --object-path /org/steinsos/Worldline --method org.steinsos.Worldline1.GetState',
           'sha256sum '+ ' '.join(shlex.quote(target) for _,target,_ in entries)]
rc,out=lab.serial('; '.join(commands),55)
print(out)
if rc:sys.exit(rc)
for item in expected:
    if item['sha256'] not in out:sys.exit('Guest source hash mismatch: '+item['guest_target'])
print(json.dumps({'scope':'named disposable V2 fork only','sources':expected},indent=2))
