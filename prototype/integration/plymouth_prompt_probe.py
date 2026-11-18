#!/usr/bin/python3
"""Dedicated-VT display fixture in the disposable guest; never real disk auth."""
import json,os,subprocess as sp,time
from pathlib import Path
assert os.geteuid()==0 and Path('/etc/hostname').read_text().strip()=='steins-prototype'
status=Path('/tmp/v3-plymouth-prompt.json')
original=int(sp.check_output(['fgconsole'],text=True).strip())
target=3 if original!=3 else 4
daemon=None;ask=None
try:
 sp.run(['chvt',str(target)],check=True)
 with Path('/tmp/v3-plymouth-display.log').open('w') as log:
  daemon=sp.Popen(['plymouthd','--no-daemon','--mode=boot','--tty=/dev/tty'+str(target),'--ignore-serial-consoles','--graphical-boot','--no-boot-log','--debug','--debug-file=/tmp/v3-plymouth-renderer.log','--kernel-command-line=quiet splash'],stdout=log,stderr=sp.STDOUT)
  for attempt in range(50):
   if daemon.poll() is not None:raise RuntimeError('plymouthd exited '+str(daemon.returncode))
   if sp.run(['plymouth','--ping'],stdout=sp.DEVNULL,stderr=sp.DEVNULL).returncode==0:break
   time.sleep(.1)
  else:raise RuntimeError('daemon not ready')
  sp.run(['plymouth','--show-splash'],check=True)
  with Path('/tmp/v3-plymouth-fixture-response').open('w') as response:
   ask=sp.Popen(['plymouth','ask-for-password','--prompt=Validation fixture only'],stdout=response,stderr=log)
   status.write_text(json.dumps({'phase':'prompt-visible-fixture','original_vt':original,'target_vt':target,'not_real_authentication':True}))
   for attempt in range(60):
    if ask.poll() is not None:break
    time.sleep(.5)
   if ask.poll() is None:ask.terminate();ask.wait(timeout=3)
   status.write_text(json.dumps({'phase':'completed-fixture','client_returncode':ask.returncode,'original_vt':original,'target_vt':target,'not_real_authentication':True}))
finally:
 if ask and ask.poll() is None:ask.terminate()
 sp.run(['plymouth','--quit'],timeout=5)
 if daemon:
  try:daemon.wait(timeout=5)
  except sp.TimeoutExpired:daemon.terminate()
 sp.run(['chvt',str(original)],check=True)
