#!/usr/bin/env python3
"""V3 isolated integration lab; reuses reviewed V2 storage guards without modifying it."""
import importlib.util
from pathlib import Path
import sys
import time
import json
import shutil
import subprocess
import datetime as dt
PROJECT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('_steins_v2_lab',PROJECT/'design/worldline-v2/engineering/vm_lab.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
engine.NAME='SteinsOS-V3-Integration'
BaseLab=engine.Lab
class Lab(BaseLab):
    def __init__(self,project=PROJECT):
        super().__init__(project)
        self.root=self.project/'evidence/v3-integration/lab'
        self.control=self.root/'control'
        self.state_path=self.root/'state.json'
    def ensure_layout(self):
        for directory in [self.project/'evidence',self.root.parent]:
            if directory.is_symlink() or (directory.exists() and directory.resolve()!=directory):
                raise ValueError('Integration directories must not redirect through symlinks')
            directory.mkdir(exist_ok=True)
            if directory.stat().st_uid!=engine.os.getuid():raise ValueError('Integration directory owner differs')
        super().ensure_layout()
    def chain(self, disk):
        return json.loads(subprocess.check_output(['qemu-img','info','--backing-chain','--output=json',str(disk)]))
    def freeze(self, name):
        """Cold-copy the current tested run; its immutable ancestors stay pinned."""
        name=engine.label(name);self.assert_cold();self.ensure_layout();self.space()
        state=self.state();self.verify(state['checkpoint'])
        source=self.owned(self.root/'runs'/state['run']/'system.qcow2')
        variables=self.owned(source.with_name('OVMF_VARS.fd'))
        destination=self.root/'checkpoints'/name
        if destination.exists():raise FileExistsError('Frozen checkpoint already exists; never overwritten')
        info=self.chain(source)
        if len(info)<2 or info[1]['filename']!=str(self.root/'checkpoints'/state['checkpoint']/'system.qcow2'):
            raise ValueError('Unexpected current run backing')
        ancestors=[]
        for item in info[1:]:
            path=regular(item['filename'])
            if item.get('format')!='qcow2' or not(path==self.base.resolve() or path.is_relative_to(self.root/'checkpoints')):
                raise ValueError('Unexpected ancestor')
            ancestors.append({'path':str(path),'sha256':engine.digest(path)})
        before=engine.digest(source);nv_before=engine.digest(variables)
        self.assert_cold();destination.mkdir()
        copied=destination/'system.qcow2';nv=destination/'OVMF_VARS.fd'
        subprocess.run(['cp','--reflink=auto','--sparse=always','--',str(source),str(copied)],check=True)
        shutil.copyfile(variables,nv)
        self.assert_cold()
        if engine.digest(source)!=before or engine.digest(copied)!=before or engine.digest(variables)!=nv_before or engine.digest(nv)!=nv_before:
            raise RuntimeError('Run changed during freeze; incomplete checkpoint must not be used')
        checked=subprocess.check_output(['qemu-img','check',str(copied)],text=True)
        copied.chmod(0o400);nv.chmod(0o400)
        metadata={'format':'v3-frozen-chain-1','name':name,'source_run':state['run'],
                  'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
                  'disk_sha256':before,'nvram_sha256':nv_before,'ancestors':ancestors,'disk_check':checked.strip()}
        engine.write_json(destination/'checkpoint.json',metadata)
        self.verify(name)
        return metadata
    def verify(self, name):
        name=engine.label(name);folder=self.root/'checkpoints'/name
        metadata=json.loads(self.owned(folder/'checkpoint.json').read_text())
        if metadata.get('format')!='v3-frozen-chain-1':return super().verify(name)
        if metadata['name']!=name:raise ValueError('Frozen checkpoint identity differs')
        disk=self.owned(folder/'system.qcow2');nv=self.owned(folder/'OVMF_VARS.fd')
        for path,key in [(disk,'disk_sha256'),(nv,'nvram_sha256')]:
            if engine.digest(path)!=metadata[key]:raise ValueError('Frozen checkpoint hash mismatch: '+str(path))
        expected=[]
        for item in metadata['ancestors']:
            path=regular(item['path'])
            if not(path==self.base.resolve() or path.is_relative_to(self.root/'checkpoints')):
                raise ValueError('Frozen ancestor escapes lab/backing boundary')
            if engine.digest(path)!=item['sha256']:raise ValueError('Frozen ancestor hash mismatch: '+str(path))
            expected.append(str(path))
        info=self.chain(disk)
        if [item['filename'] for item in info[1:]]!=expected or any(item.get('format')!='qcow2' for item in info):
            raise ValueError('Frozen backing chain differs')
        return metadata
    def qmp(self, command, args=None):
        result=super().qmp(command,args)
        if command=='input-send-event' and any(e.get('type')=='btn' and e.get('data',{}).get('down') for e in (args or {}).get('events',[])):
            time.sleep(.12)  # Give the guest a real press frame before releasing.
        return result
engine.Lab=Lab
regular=engine.regular
if __name__=='__main__':
    try:
        if len(sys.argv)==3 and sys.argv[1]=='freeze':
            print(json.dumps(Lab().freeze(sys.argv[2]),indent=2));sys.exit(0)
        sys.exit(engine.main())
    except Exception as error:sys.exit('V3 lab: '+str(error))
