#!/usr/bin/python3
"""Capture normal shutdown of the owned V3 guest; never force-kill it."""
import json,time
from pathlib import Path
from vm_lab import Lab
lab=Lab();lab.login();folder=lab.project/'evidence/v3-integration/native-shutdown';folder.mkdir(exist_ok=False)
rc,out=lab.serial('sudo -n systemctl poweroff --no-block',10)
if rc:raise RuntimeError(out)
records=[]
for index in range(60):
 try:
  path=folder/('frame-%03d.png'%index);lab.qmp('screendump',{'filename':str(path),'format':'png'});records.append(path.name)
 except (OSError,RuntimeError):break
 time.sleep(.2)
for attempt in range(30):
 try:state=lab.running()
 except RuntimeError:state={'status':'exiting'}
 if not state:break
 time.sleep(.3)
if state:raise RuntimeError('Guest has not completed normal shutdown: '+str(state))
(folder/'captures.json').write_text(json.dumps({'normal_shutdown_completed':True,'frames':records},indent=2)+'\n')
print('Guest off after normal shutdown; frames',len(records))
