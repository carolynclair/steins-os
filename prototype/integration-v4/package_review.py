#!/usr/bin/python3
"""Hash-verified review capsule; VM disks, host backups and build trees excluded."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'dist/steins-os-v4-panel-icons-2026-11-02.zip'
if OUT.exists():raise FileExistsError('Review capsules are never overwritten')
assert json.loads((ROOT/'evidence/v4-design/qualification-reset-boot.json').read_text())['passed'] is True
assert json.loads((ROOT/'evidence/v4-design/preservation-final.json').read_text())['reset_boot_passed'] is True
paths=set()
for name in ['prototype/identity-v4','prototype/panel-v4','prototype/surfaces-v4','prototype/worldline-v4','prototype/integration-v4','prototype/artwork-v3','config/includes.chroot/etc/steins']:
 for p in (ROOT/name).rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and 'build' not in p.relative_to(ROOT/name).parts and p.suffix!='.pyc':paths.add(p)
for name in ['LICENSE','build-tools/Dockerfile','packaging/SOURCE_DATE_EPOCH','prototype/integration/vm_lab.py','design/worldline-v2/engineering/vm_lab.py',
 'config/includes.chroot/usr/local/lib/steins/steinslib.py','config/includes.chroot/usr/local/lib/steins/meterlib.py','dist/v4/BUILD-SET.json']:
 paths.add(ROOT/name)
paths.add(ROOT/'config/includes.chroot/usr/share/icons/hicolor/scalable/apps/steins-os.svg')
manifest=json.loads((ROOT/'dist/v4/BUILD-SET.json').read_text())
for item in manifest['install_packages']:
 p=ROOT/item['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'];paths.add(p)
for root in [ROOT/'evidence/v4-design',ROOT/'dist/v4/surfaces']:
 for p in root.rglob('*'):
  if not p.is_file() or p.is_relative_to(ROOT/'evidence/v4-design/lab'):continue
  if 'build' in p.relative_to(root).parts or '__pycache__' in p.parts:continue
  if p.name=='review-capsule.json':continue
  if p.suffix in {'.json','.txt','.log','.png','.md'}:paths.add(p)
items=[]
for p in sorted(paths):
 if p.is_symlink() or p.suffix in {'.qcow2','.iso','.fd','.pid','.sock','.pyc'}:raise ValueError('Unexpected capsule member: '+str(p))
 items.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
with zipfile.ZipFile(OUT,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for item in items:z.write(ROOT/item['path'],'steins-native-v4/'+item['path'])
 z.writestr('steins-native-v4/MANIFEST.json',json.dumps({'scope':'V4 source, selected first-party DEBs and runtime evidence; not an ISO or portable VM','files':items},indent=2)+'\n')
 z.writestr('steins-native-v4/START-HERE.md',(ROOT/'prototype/integration-v4/README.md').read_text()+'\nExtract into a separate review directory. This capsule contains no VM images and requires the existing local immutable backing chain to replay the prepared VM. The full distro checkout remains the build authority. No host backup or credential is included; the public guest fixture account is test-only.\n')
with zipfile.ZipFile(OUT) as z:
 assert z.testzip() is None
 for item in items:assert hashlib.sha256(z.read('steins-native-v4/'+item['path'])).hexdigest()==item['sha256']
sha=hashlib.sha256(OUT.read_bytes()).hexdigest();OUT.with_suffix('.zip.sha256').write_text(sha+'  '+OUT.name+'\n')
print(json.dumps({'archive':str(OUT),'bytes':OUT.stat().st_size,'members':len(items)+2,'sha256':sha,'crc_and_member_hashes_pass':True},indent=2))
