#!/usr/bin/python3
"""Explicit, backed-up greeter presets for the isolated V3 guest only."""
import argparse,base64,hashlib,json,os,stat,subprocess,tempfile
from pathlib import Path

STORE=Path('/var/lib/steins-login-prototype')
FILES={Path('/etc/sddm.conf.d/90-steins-lab.conf'):b'[Theme]\nCurrent=breeze\n',
       Path('/usr/share/sddm/themes/breeze/theme.conf.user'):Path('/usr/share/steins-login/breeze-theme.conf')}
def sha(data):return hashlib.sha256(data).hexdigest()
def safe(path):
 for parent in [path,*path.parents]:
  if parent.is_symlink():raise ValueError('Refusing symlink: '+str(parent))
 if path.exists() and (not path.is_file() or path.stat().st_uid!=0):raise ValueError('Unexpected file: '+str(path))
def atomic(path,data,mode=0o644):
 path.parent.mkdir(parents=True,exist_ok=True)
 fd,name=tempfile.mkstemp(prefix='.'+path.name,dir=path.parent)
 try:
  with os.fdopen(fd,'wb') as stream:stream.write(data)
  os.chmod(name,mode);os.replace(name,path)
 finally:
  if os.path.exists(name):os.unlink(name)
def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['apply','rollback']);args=parser.parse_args()
 if os.geteuid()!=0:raise ValueError('Run only as root inside the V3 guest')
 marker=Path('/run/steins-startup-v3-allow');safe(marker)
 if marker.read_text().strip()!='SteinsOS-V3-Integration':raise ValueError('Explicit V3 opt-in missing')
 if subprocess.check_output(['systemd-detect-virt','--vm'],text=True).strip() not in ('qemu','kvm'):raise ValueError('QEMU/KVM guest required')
 if not Path('/usr/share/sddm/themes/breeze/Main.qml').is_file():raise ValueError('Install sddm-theme-breeze first')
 state=STORE/'backup.json';safe(state)
 if args.action=='rollback':
  records=json.loads(state.read_text())
  for item in records:
   p=Path(item['path']);safe(p)
   if not p.exists() or sha(p.read_bytes())!=item['installed_sha256']:raise ValueError('Later edits preserved: '+str(p))
  for item in records:
   p=Path(item['path'])
   if item['previous'] is None:p.unlink()
   else:atomic(p,base64.b64decode(item['previous']),item['mode'])
  state.rename(STORE/'restored-backup.json');print('Greeter presets rolled back; backup retained');return
 if state.exists():raise ValueError('Already opted in; roll back before applying again')
 records=[];desired={}
 for p,value in FILES.items():
  safe(p);data=value.read_bytes() if isinstance(value,Path) else value
  records.append({'path':str(p),'previous':base64.b64encode(p.read_bytes()).decode() if p.exists() else None,
                  'mode':stat.S_IMODE(p.stat().st_mode) if p.exists() else 0o644,'installed_sha256':sha(data)})
  desired[p]=data
 atomic(state,(json.dumps(records,indent=2)+'\n').encode(),0o600)
 for p,data in desired.items():atomic(p,data)
 print('Breeze + public Steins artwork selected; existing session not restarted')
if __name__=='__main__':
 try:main()
 except Exception as error:raise SystemExit(str(error))
