#!/usr/bin/python3
"""Explicit optional boot opt-in inside the disposable V3 guest only."""
import json,os,subprocess as sp
from pathlib import Path
assert os.geteuid()==0 and Path('/etc/hostname').read_text().strip()=='steins-prototype'
status=Path('/tmp/v3-final-boot-job.json')
try:
 with Path('/tmp/v3-final-boot-job.log').open('w') as log:
  marker=Path('/run/steins-startup-v3-allow');marker.write_text('SteinsOS-V3-Integration\n');marker.chmod(0o600)
  if not Path('/var/lib/steins-startup-prototype/grub-backups/current.json').exists():
   sp.run(['/usr/lib/steins/startup/grub-lab.py','apply','--resolution','1280x800'],stdout=log,stderr=sp.STDOUT,check=True)
  sp.run(['plymouth-set-default-theme','steins-lab-v3-reduced'],stdout=log,stderr=sp.STDOUT,check=True)
  sp.run(['update-initramfs','-u','-k',os.uname().release],stdout=log,stderr=sp.STDOUT,check=True)
 status.write_text(json.dumps({'passed':True,'theme':'steins-lab-v3-reduced','kernel':os.uname().release,'grub_background':'1280x800','scope':'V3 guest only'}))
except Exception as error:
 status.write_text(json.dumps({'passed':False,'error':str(error)}));raise
