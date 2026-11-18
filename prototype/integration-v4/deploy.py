#!/usr/bin/env python3
"""Install explicitly listed experimental DEBs only into the guarded V4 fork."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
import sys
import uuid
from vm_lab import Lab, regular

ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('packages',nargs='*',type=Path)
parser.add_argument('--tools',action='store_true',help='Add SSH client, Zsh and Neovim only to this test guest')
a=parser.parse_args();lab=Lab();lab.qmp('query-status');lab.login()
paths=a.packages
if not paths:
    manifest=json.loads((ROOT/'dist/v4/BUILD-SET.json').read_text())
    paths=[ROOT/item['path'] for item in manifest['install_packages']]
    for item,path in zip(manifest['install_packages'],paths):
        if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
            sys.exit('Package hash mismatch: '+str(path))
if not paths:sys.exit('No packages selected')
guest=[];report=[]
for index,path in enumerate(paths):
    path=regular(path)
    if not path.is_relative_to(ROOT) or path.suffix!='.deb':sys.exit('Choose a project DEB')
    name='install-'+uuid.uuid4().hex[:10]+'-'+str(index)+'.deb'
    subprocess.run([sys.executable,str(Path(__file__).with_name('push_guest.py')),str(path),'--name',name],check=True)
    guest.append('/tmp/v4-design/'+name)
    report.append({'source':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
command='sudo -n env DEBIAN_FRONTEND=noninteractive apt-get --no-remove --no-install-recommends -y install '+' '.join(shlex.quote(p) for p in guest)
if a.tools:command+=' openssh-client zsh neovim'
rc,out=lab.serial(command,55)
evidence=ROOT/'evidence/v4-design';evidence.mkdir(exist_ok=True)
(evidence/'latest-deploy.log').write_text(out+'\n')
(evidence/'latest-deploy.json').write_text(json.dumps({'vm':'SteinsOS-V4-Design','exit_code':rc,'packages':report},indent=2)+'\n')
print(out[-8000:]);sys.exit(rc)
