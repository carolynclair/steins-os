#!/usr/bin/python3
"""Run as root only inside the named disposable integration guest."""
import json,os,subprocess as sp
from pathlib import Path
assert Path('/etc/hostname').read_text().strip()=='steins-prototype'
assert os.geteuid()==0
log=Path('/tmp/v3-startup-job.log');status=Path('/tmp/v3-startup-job.json')
try:
 with log.open('w') as output:
  for command in [['dpkg','-i','/tmp/v3-integration/startup-v3.deb'],['plymouth-set-default-theme','steins-lab-v3'],['update-initramfs','-u','-k',os.uname().release]]:
   output.write('RUN '+repr(command)+'\n');output.flush()
   sp.run(command,stdout=output,stderr=sp.STDOUT,check=True)
 status.write_text(json.dumps({'passed':True,'theme':'steins-lab-v3','kernel':os.uname().release}))
except Exception as error:
 status.write_text(json.dumps({'passed':False,'error':str(error)}));raise
