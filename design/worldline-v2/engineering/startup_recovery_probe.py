#!/usr/bin/env python3
"""Controlled transient-dependency probe for the disposable V2 guest only."""
import ast
import json
import os
from pathlib import Path
import subprocess as sp
import time
os.environ.update(DBUS_SESSION_BUS_ADDRESS='unix:path=/run/user/1000/bus', XDG_RUNTIME_DIR='/run/user/1000', STEINS_DESKTOP_BACKEND='plasma')
def call(method):
    output=sp.check_output(['gdbus','call','--session','--dest','org.steinsos.Worldline1','--object-path','/org/steinsos/Worldline','--method','org.steinsos.Worldline1.'+method],text=True)
    return json.loads(ast.literal_eval(output)[0])
state_file=Path.home()/'.local/state/steins/divergence'
before=state_file.read_bytes()
started=time.monotonic()
observations=[]
try:
    sp.run(['systemctl','--user','stop','plasma-plasmashell.service'],check=True)
    failed=call('ApplyCurrent')
    observations.append({'phase':'dependency-absent','state':failed})
    assert failed.get('applied') is False, failed
    assert all(e['step']=='wallpaper' for e in failed['errors']), failed
    assert any('ServiceUnknown' in e['message'] or 'NameHasNoOwner' in e['message'] for e in failed['errors']), failed
    time.sleep(4)
finally:
    sp.run(['systemctl','--user','start','plasma-plasmashell.service'],check=True)
for attempt in range(30):
    current=call('GetState')
    if current.get('applied') is True:
        break
    time.sleep(1)
else:
    raise AssertionError(current)
assert state_file.read_bytes()==before, 'Recovery rewrote divergence'
observations.append({'phase':'dependency-restored-without-manual-reapply','state':current})
print(json.dumps({'scope':'disposable V2 fork','passed':True,'elapsed_seconds':round(time.monotonic()-started,2),'divergence_unchanged':True,'observations':observations},indent=2))
sp.run(['journalctl','--user','-b','--no-pager','--grep','Transient wallpaper dependency|worldline .*applied=','-n','25'],check=True)
