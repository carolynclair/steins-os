#!/usr/bin/python3
"""Capture the owned V3 display during normal reboot; no extra boot delay."""
import hashlib,json,time
from pathlib import Path
from vm_lab import Lab
lab=Lab();folder=lab.project/'evidence/v3-integration/native-boot-final'
folder.mkdir(exist_ok=False)
rc,out=lab.serial('sudo -n systemctl reboot --no-block',10)
if rc:raise RuntimeError(out)
records=[];previous=None;start=time.monotonic()
for index in range(130):
 path=folder/('frame-%03d.png'%index)
 lab.qmp('screendump',{'filename':str(path),'format':'png'})
 sha=hashlib.sha256(path.read_bytes()).hexdigest()
 if sha==previous:path.unlink()
 else:
  records.append({'file':path.name,'capture_elapsed_seconds':round(time.monotonic()-start,3),'sha256':sha});previous=sha
 time.sleep(.25)
(folder/'captures.json').write_text(json.dumps({'scope':'real QMP display during native guest reboot; capture overhead means not a performance measurement','frames':records},indent=2)+'\n')
print('Retained',len(records),'distinct frames in',folder)
