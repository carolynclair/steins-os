#!/usr/bin/env python3
"""V4 isolated visual integration lab; reuses reviewed V2 storage guards without modifying it."""
import importlib.util
from pathlib import Path
import sys
import time
import json
import shutil
import subprocess
import datetime as dt
import socket
import shlex
import uuid
import re
PROJECT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('_steins_v2_lab',PROJECT/'design/worldline-v2/engineering/vm_lab.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
engine.NAME='SteinsOS-V4-Design'
BaseLab=engine.Lab

def completed_frame(data, marker):
    # An echoed command contains the marker too, but never this complete status line.
    return re.search(rb'(?:^|\r?\n)' + re.escape(marker.encode()) + rb': ([0-9]{1,3})\r?\n', data)

class Lab(BaseLab):
    def __init__(self,project=PROJECT):
        super().__init__(project)
        self.root=self.project/'evidence/v4-design/lab'
        self.control=self.root/'control'
        self.state_path=self.root/'state.json'
    def serial(self, command, timeout=30):
        self.qmp('query-status')
        marker='V4_DONE_'+uuid.uuid4().hex
        begin=marker+'_BEGIN'
        with socket.socket(socket.AF_UNIX) as s:
            s.connect(str(self.control/'serial.sock'));s.settimeout(.5)
            s.sendall(('printf "\\n'+begin+'\\n"; bash -c '+shlex.quote(command)+' </dev/null; printf "\\n'+marker+': %s\\n" "$?"\n').encode())
            data=b'';end=time.monotonic()+timeout
            while time.monotonic()<end:
                try:
                    chunk=s.recv(65536)
                    if not chunk:break
                    data+=chunk
                    match=completed_frame(data,marker)
                    starts=list(re.finditer(rb'(?:^|\r?\n)'+re.escape(begin.encode())+rb'\r?\n',data[:match.start()] if match else data))
                    if match and starts:return int(match.group(1)),data[starts[-1].end():match.start()].decode(errors='replace').strip()
                except TimeoutError:pass
            raise RuntimeError('Guest command timeout: '+data.decode(errors='replace')[-12000:])
    def ensure_layout(self):
        for directory in [self.project/'evidence',self.root.parent]:
            if directory.is_symlink() or (directory.exists() and directory.resolve()!=directory):
                raise ValueError('Integration directories must not redirect through symlinks')
            directory.mkdir(exist_ok=True)
            if directory.stat().st_uid!=engine.os.getuid():raise ValueError('Integration directory owner differs')
        super().ensure_layout()
    def seed(self, name='v3-base'):
        """Cold, byte-preserving copy of the frozen V3 milestone only."""
        name=engine.label(name);self.assert_cold();self.ensure_layout();self.space()
        spec=importlib.util.spec_from_file_location('_readonly_v3_lab',self.project/'prototype/integration/vm_lab.py')
        previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
        origin=previous.Lab(self.project);data=origin.verify('native-v3')
        source=origin.owned(origin.root/'checkpoints/native-v3/system.qcow2')
        variables=origin.owned(source.with_name('OVMF_VARS.fd'))
        destination=self.root/'checkpoints'/name
        if destination.exists():raise FileExistsError('V4 seed exists; never overwritten')
        ancestors=[]
        for item in self.chain(source)[1:]:
            path=regular(item['filename'])
            if item.get('format')!='qcow2' or not(path==self.base.resolve() or path.is_relative_to(self.project/'evidence/v3-integration/lab/checkpoints')):
                raise ValueError('Unexpected frozen V3 ancestor')
            ancestors.append({'path':str(path),'sha256':engine.digest(path)})
        self.assert_cold();destination.mkdir()
        copied=destination/'system.qcow2';nv=destination/'OVMF_VARS.fd'
        subprocess.run(['cp','--reflink=auto','--sparse=always','--',str(source),str(copied)],check=True)
        shutil.copyfile(variables,nv)
        if engine.digest(copied)!=data['disk_sha256'] or engine.digest(nv)!=data['nvram_sha256']:
            raise RuntimeError('Seed copy hash mismatch')
        if engine.digest(source)!=data['disk_sha256'] or engine.digest(variables)!=data['nvram_sha256']:
            raise RuntimeError('Frozen V3 source changed during capture')
        copied.chmod(0o400);nv.chmod(0o400)
        metadata={'format':'v4-frozen-chain-1','name':name,'source_milestone':'V3/native-v3',
                  'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
                  'disk_sha256':data['disk_sha256'],'nvram_sha256':data['nvram_sha256'],
                  'ancestors':ancestors,'disk_check':subprocess.check_output(['qemu-img','check',str(copied)],text=True)}
        engine.write_json(destination/'checkpoint.json',metadata);self.verify(name)
        return metadata
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
            if item.get('format')!='qcow2' or not(path==self.base.resolve() or path.is_relative_to(self.root/'checkpoints') or path.is_relative_to(self.project/'evidence/v3-integration/lab/checkpoints')):
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
        metadata={'format':'v4-frozen-chain-1','name':name,'source_run':state['run'],
                  'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
                  'disk_sha256':before,'nvram_sha256':nv_before,'ancestors':ancestors,'disk_check':checked.strip()}
        engine.write_json(destination/'checkpoint.json',metadata)
        self.verify(name)
        return metadata
    def verify(self, name):
        name=engine.label(name);folder=self.root/'checkpoints'/name
        metadata=json.loads(self.owned(folder/'checkpoint.json').read_text())
        if metadata.get('format')!='v4-frozen-chain-1':return super().verify(name)
        if metadata['name']!=name:raise ValueError('Frozen checkpoint identity differs')
        disk=self.owned(folder/'system.qcow2');nv=self.owned(folder/'OVMF_VARS.fd')
        for path,key in [(disk,'disk_sha256'),(nv,'nvram_sha256')]:
            if engine.digest(path)!=metadata[key]:raise ValueError('Frozen checkpoint hash mismatch: '+str(path))
        expected=[]
        for item in metadata['ancestors']:
            path=regular(item['path'])
            if not(path==self.base.resolve() or path.is_relative_to(self.root/'checkpoints') or path.is_relative_to(self.project/'evidence/v3-integration/lab/checkpoints')):
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
        if sys.argv[1:] in (['--help'], ['-h']):
            print(__doc__ + '\nUsage: vm_lab.py ACTION [VALUE] [--timeout SECONDS]\nActions: seed, freeze, checkpoint, verify, reset, start, status, stop, view, login, guest, query, screenshot, key, text, click\nseed v3-base captures frozen V3; freeze NAME captures a tested cold V4 run.\nAll launch/reset/capture operations require other VMs to be off.')
            sys.exit(0)
        if len(sys.argv) in (2,3) and sys.argv[1]=='seed':
            print(json.dumps(Lab().seed(sys.argv[2] if len(sys.argv)==3 else 'v3-base'),indent=2));sys.exit(0)
        if len(sys.argv)==3 and sys.argv[1]=='freeze':
            print(json.dumps(Lab().freeze(sys.argv[2]),indent=2));sys.exit(0)
        sys.exit(engine.main())
    except Exception as error:sys.exit('V4 lab: '+str(error))
