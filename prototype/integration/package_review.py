#!/usr/bin/python3
"""Package source/DEBs/evidence; never includes VM images or private fixture keys."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'dist/steins-os-v3-native-prototype-2026-11-02.zip'
if OUT.exists():raise FileExistsError('Review archives are never overwritten')
paths=set()
for name in ['prototype/terminal','prototype/panel','prototype/startup','prototype/greeter','prototype/integration','prototype/artwork-v3','prototype/worldline']:
 for path in (ROOT/name).rglob('*'):
  if path.is_file() and '__pycache__' not in path.parts and path.suffix!='.pyc':paths.add(path)
for name in ['prototype/build.py','prototype/README.md','LICENSE','design/worldline-v2/engineering/vm_lab.py','dist/v3/BUILD-SET.json',
 'config/includes.chroot/usr/local/bin/steins-worldline','config/includes.chroot/usr/local/bin/ibm5100','config/includes.chroot/usr/local/bin/dmail','config/includes.chroot/usr/local/bin/steins-meter',
 'config/includes.chroot/usr/local/lib/steins/steinslib.py','config/includes.chroot/usr/local/lib/steins/meterlib.py','config/includes.chroot/usr/share/plymouth/themes/steins/steins.script','tests/check_source.py']:
 paths.add(ROOT/name)
selected=json.loads((ROOT/'dist/v3/BUILD-SET.json').read_text())
for item in selected['install_packages']:
 path=ROOT/item['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'];paths.add(path)
for path in (ROOT/'evidence/v3-integration').rglob('*'):
 if path.is_file() and not path.is_relative_to(ROOT/'evidence/v3-integration/lab') and '__pycache__' not in path.parts:paths.add(path)
files=[]
for path in sorted(paths):
 if path.is_symlink() or path.suffix in {'.qcow2','.iso','.fd','.pid','.sock','.pyc'}:raise ValueError('Unexpected unsafe review member: '+str(path))
 files.append({'path':str(path.relative_to(ROOT)),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
manifest=json.dumps({'scope':'native prototype review; external VM backing files and upstream runtime DEBs not bundled','files':files},indent=2)+'\n'
with zipfile.ZipFile(OUT,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
 for item in files:archive.write(ROOT/item['path'],'steins-native-v3/'+item['path'])
 archive.writestr('steins-native-v3/MANIFEST.json',manifest)
 archive.writestr('steins-native-v3/START-HERE.md',(ROOT/'prototype/integration/README.md').read_text()+'\nThis capsule contains the new component sources, selected local DEBs and evidence. It requires the existing local QA backing/checkpoints for VM replay; it is not a portable VM image or complete distribution/ISO build. The full distro checkout remains in the shared workspace. Extract into a separate review folder, never over a working checkout as an update.\n')
with zipfile.ZipFile(OUT) as archive:
 assert archive.testzip() is None
 for item in files:assert hashlib.sha256(archive.read('steins-native-v3/'+item['path'])).hexdigest()==item['sha256']
sha=hashlib.sha256(OUT.read_bytes()).hexdigest();OUT.with_suffix('.zip.sha256').write_text(sha+'  '+OUT.name+'\n')
print(json.dumps({'archive':str(OUT),'files':len(files)+2,'bytes':OUT.stat().st_size,'sha256':sha,'crc_and_file_hashes_pass':True},indent=2))
