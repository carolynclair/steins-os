#!/usr/bin/env python3
"""Isolated V2 validation forks. Never changes the original prototype or libvirt VM.

Checkpoint/reset are cold-only. Old runs are retained; no reset deletes data.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import socket
import stat
import subprocess as sp
import sys
import tempfile
import time
import uuid

PROJECT = Path(__file__).resolve().parents[3]
NAME = 'SteinsOS-V2-Validation'
GIB = 1024**3


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024**2),b''):h.update(chunk)
    return h.hexdigest()


def label(value):
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,39}',value):
        raise ValueError('Use a label of 1–40 letters, digits, hyphens or underscores')
    return value


def regular(path):
    p=Path(path)
    if p.is_symlink() or not stat.S_ISREG(p.stat().st_mode):
        raise ValueError('Expected a regular, non-symlink lab file: '+str(p))
    if p.stat().st_uid != os.getuid():raise ValueError('File owner differs from current user: '+str(p))
    return p.resolve(strict=True)


def write_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,temp=tempfile.mkstemp(prefix='.'+path.name,dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:json.dump(data,f,indent=2);f.write('\n')
        os.replace(temp,path)
    finally:
        if Path(temp).exists():Path(temp).unlink()


class Lab:
    def __init__(self,project=PROJECT):
        self.project=Path(project).resolve()
        self.root=self.project/'evidence/v2-vm-validation'
        self.source=self.project/'evidence/plasma-prototype/system.qcow2'
        self.base=self.project/'evidence/vm/packaged-uefi.qcow2'
        self.vars=self.project/'evidence/plasma-prototype/OVMF_VARS.fd'
        self.control=self.root/'control'
        self.state_path=self.root/'state.json'

    def ensure_layout(self):
        for directory in [self.project/'evidence',self.root,self.root/'checkpoints',self.root/'runs',self.control]:
            if directory.is_symlink() or (directory.exists() and directory.resolve()!=directory):
                raise ValueError('Lab directories must not redirect through symlinks')
            directory.mkdir(exist_ok=True)
            if directory.stat().st_uid!=os.getuid():raise ValueError('Lab directory owner differs')
            if directory!=self.project/'evidence':directory.chmod(0o700)

    def owned(self,path):
        p=regular(path)
        if not p.is_relative_to(self.root):raise ValueError('Path escapes V2 lab')
        return p

    def state(self):
        data=json.loads(self.owned(self.state_path).read_text())
        if data['name']!=NAME:raise ValueError('Wrong lab identity')
        label(data['checkpoint']);label(data['run'])
        return data

    def qmp(self,command,args=None):
        with socket.socket(socket.AF_UNIX) as s:
            s.settimeout(8);s.connect(str(self.control/'qmp.sock'))
            f=s.makefile('rwb',buffering=0);f.readline()
            def call(cmd,arguments=None):
                f.write((json.dumps({'execute':cmd,'arguments':arguments or {}})+'\n').encode())
                while True:
                    line=f.readline()
                    if not line:raise RuntimeError('QMP disconnected')
                    reply=json.loads(line)
                    if 'error' in reply:raise RuntimeError(reply['error'])
                    if 'return' in reply:return reply['return']
            call('qmp_capabilities')
            if call('query-name').get('name')!=NAME:raise RuntimeError('Unexpected QEMU identity')
            return call(command,args)

    def running(self):
        try:return self.qmp('query-status')
        except (OSError,RuntimeError,ValueError):
            pid=self.root/'qemu.pid'
            if pid.exists() and Path('/proc',pid.read_text().strip()).exists():
                raise RuntimeError('Recorded QEMU process exists but QMP is unavailable; inspect it first')
            return None

    def assert_cold(self):
        if self.running():raise RuntimeError('Shut down the V2 guest completely first')
        # No assumptions from a missing socket: reject other QEMU processes too.
        for proc in Path('/proc').iterdir():
            if not proc.name.isdecimal():continue
            try:
                cmd=proc.joinpath('cmdline').read_bytes().split(b'\0')
                if cmd and b'qemu-system-' in Path(os.fsdecode(cmd[0])).name.encode():
                    raise RuntimeError('A QEMU guest is running; shut it down before cold operations')
            except (FileNotFoundError,PermissionError,ProcessLookupError):pass
        other=sp.run(['virsh','-c','qemu:///system','list','--name'],text=True,capture_output=True,check=True)
        if other.stdout.strip():raise RuntimeError('A libvirt guest is running')

    def space(self,extra=0):
        if shutil.disk_usage(self.project).free < max(10*GIB,extra+8*GIB):
            raise RuntimeError('Insufficient space: retain at least 8 GiB after capture and 10 GiB before launch')

    def checkpoint(self,name):
        name=label(name);self.assert_cold();self.ensure_layout()
        source=regular(self.source);base=regular(self.base);vars=regular(self.vars)
        self.space(source.stat().st_size)
        info=json.loads(sp.check_output(['qemu-img','info','--output=json',str(source)]))
        if info.get('format')!='qcow2' or info.get('full-backing-filename')!=str(base):
            raise ValueError('Unexpected prototype backing chain')
        base_info=json.loads(sp.check_output(['qemu-img','info','--output=json',str(base)]))
        if base_info.get('format')!='qcow2' or base_info.get('backing-filename'):
            raise ValueError('Expected a standalone QA backing image')
        dest=self.root/'checkpoints'/name
        if dest.exists():raise FileExistsError('Checkpoint exists; never overwritten')
        before=digest(source);nv_before=digest(vars);base_sha=digest(base)
        self.assert_cold();dest.mkdir(parents=True)
        copied=dest/'system.qcow2';nv=dest/'OVMF_VARS.fd'
        shutil.copyfile(source,copied);shutil.copyfile(vars,nv)
        self.assert_cold()
        if digest(source)!=before or digest(copied)!=before or digest(vars)!=nv_before or digest(nv)!=nv_before:
            raise RuntimeError('Source changed during capture; checkpoint is incomplete and must not be used')
        result=sp.run(['qemu-img','check',str(copied)],text=True,capture_output=True,check=True)
        copied.chmod(0o400);nv.chmod(0o400)
        metadata={'name':name,'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
            'source':str(source),'disk_sha256':before,'base':str(base),'base_sha256':base_sha,
            'nvram_sha256':nv_before,'disk_check':result.stdout.strip(),
            'note':'Original prototype untouched. QA backing must remain immutable.'}
        write_json(dest/'checkpoint.json',metadata)
        return metadata

    def verify(self,name):
        name=label(name);folder=self.root/'checkpoints'/name
        data=json.loads(self.owned(folder/'checkpoint.json').read_text())
        disk=self.owned(folder/'system.qcow2');nv=self.owned(folder/'OVMF_VARS.fd')
        base=regular(self.base)
        if data['name']!=name or data['base']!=str(base):raise ValueError('Checkpoint identity/backing mismatch')
        for path,key in [(disk,'disk_sha256'),(nv,'nvram_sha256'),(base,'base_sha256')]:
            if digest(path)!=data[key]:raise ValueError('Checkpoint hash mismatch: '+str(path))
        info=json.loads(sp.check_output(['qemu-img','info','--output=json',str(disk)]))
        if info.get('format')!='qcow2' or info.get('full-backing-filename')!=str(base):
            raise ValueError('Checkpoint backing metadata differs')
        return data

    def reset(self,name=None):
        self.assert_cold();self.space();self.ensure_layout()
        if name is None:name=self.state()['checkpoint']
        name=label(name);self.verify(name)
        run='run-'+uuid.uuid4().hex[:16];folder=self.root/'runs'/run;folder.mkdir(parents=True)
        snapshot=self.root/'checkpoints'/name
        sp.run(['qemu-img','create','-f','qcow2','-F','qcow2','-b',str(snapshot/'system.qcow2'),str(folder/'system.qcow2')],check=True)
        shutil.copyfile(snapshot/'OVMF_VARS.fd',folder/'OVMF_VARS.fd');(folder/'OVMF_VARS.fd').chmod(0o600)
        state={'name':NAME,'checkpoint':name,'run':run,'created_utc':dt.datetime.now(dt.timezone.utc).isoformat()}
        write_json(folder/'run.json',state);write_json(self.state_path,state)
        return state

    def start(self,name=None):
        self.assert_cold();self.space();self.ensure_layout()
        mem=dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())
        if int(mem['MemAvailable'].split()[0])<8*1024**2:raise RuntimeError('Need at least 8 GiB available RAM')
        if not self.state_path.exists() or (name and self.state()['checkpoint']!=name):self.reset(name)
        state=self.state();self.verify(state['checkpoint'])
        folder=self.root/'runs'/state['run'];disk=self.owned(folder/'system.qcow2');nv=self.owned(folder/'OVMF_VARS.fd')
        info=json.loads(sp.check_output(['qemu-img','info','--output=json',str(disk)]))
        expected=self.root/'checkpoints'/state['checkpoint']/'system.qcow2'
        if info.get('full-backing-filename')!=str(expected):raise ValueError('Run backing differs from checkpoint')
        self.control.mkdir(parents=True,exist_ok=True);self.control.chmod(0o700)
        if len(str(self.control/'serial.sock').encode())>=104:raise ValueError('Workspace path too long for control sockets')
        pid=self.root/'qemu.pid'
        if pid.exists():pid.unlink()  # assert_cold already rejects a live recorded PID.
        args=['qemu-system-x86_64','-name',NAME,'-enable-kvm','-m','6144','-smp','2',
            '-drive','file='+str(disk)+',if=virtio,format=qcow2',
            '-drive','if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd',
            '-drive','if=pflash,format=raw,file='+str(nv),'-device','virtio-vga','-device','qemu-xhci','-device','usb-tablet',
            '-nic','user,model=virtio-net-pci','-display','none','-daemonize','-pidfile',str(pid),
            '-qmp','unix:'+str(self.control/'qmp.sock')+',server=on,wait=off',
            '-chardev','socket,id=serial0,path='+str(self.control/'serial.sock')+',server=on,wait=off,logfile='+str(folder/'serial.log'),
            '-serial','chardev:serial0','-spice','unix=on,addr='+str(self.control/'spice.sock')+',disable-ticketing=on,disable-copy-paste=on,disable-agent-file-xfer=on']
        write_json(folder/'launch-args.json',args)
        sp.run(['sg','kvm','-c',shlex.join(args)],check=True)
        return state

    def serial(self,command,timeout=30):
        self.qmp('query-status')
        marker='V2_DONE_'+uuid.uuid4().hex
        with socket.socket(socket.AF_UNIX) as s:
            s.connect(str(self.control/'serial.sock'));s.settimeout(.5)
            s.sendall(('bash -c '+shlex.quote(command)+' </dev/null; printf "\\n'+marker+': %s\\n" "$?"\n').encode())
            buf=b'';end=time.monotonic()+timeout
            while time.monotonic()<end:
                try:
                    chunk=s.recv(65536)
                    if not chunk:break
                    buf+=chunk
                    if (marker+': ').encode() in buf:
                        before,status=buf.decode(errors='replace').split(marker+': ',1)
                        if '\n' not in status:continue
                        return int(status.splitlines()[0].strip()),before.strip()
                except TimeoutError:pass
            raise RuntimeError('Guest command timeout: '+buf.decode(errors='replace'))

    def login(self):
        self.qmp('query-status')
        with socket.socket(socket.AF_UNIX) as s:
            s.connect(str(self.control/'serial.sock'));s.settimeout(.5)
            def until(pattern,seconds=20):
                data=b'';end=time.monotonic()+seconds
                while time.monotonic()<end:
                    try:
                        data+=s.recv(65536)
                        if re.search(pattern,data):return data
                    except TimeoutError:pass
                raise RuntimeError('Serial login did not reach the expected fixture prompt')
            s.sendall(b'\n');initial=until(rb'(login:|observer@[^\n]+\$)')
            if b'login:' in initial:
                s.sendall(b'observer\n');until(rb'Password:');s.sendall(b'SteinerTest42\n');until(rb'observer@[^\n]+\$')
            s.sendall(b'export TERM=dumb PAGER=cat; stty -echo\n');until(rb'observer@[^\n]+\$')
        # The public disposable fixture password is not a host credential.
        rc,out=self.serial("printf '%s\\n' 'SteinerTest42' | sudo -S -v",20)
        if rc:raise RuntimeError(out)
        return 'Disposable guest serial authenticated; sudo cache ready'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('checkpoint','verify','reset','start','status','stop','view','login','guest','query','screenshot','key','text','click'))
    p.add_argument('value',nargs='?');p.add_argument('--timeout',type=int,default=30);a=p.parse_args();lab=Lab()
    if a.action=='checkpoint':result=lab.checkpoint(a.value or 'baseline')
    elif a.action=='verify':lab.assert_cold();result=lab.verify(a.value or lab.state()['checkpoint'])
    elif a.action=='reset':result=lab.reset(a.value)
    elif a.action=='start':result=lab.start(a.value)
    elif a.action=='status':result=lab.running() or {'running':False,'status':'off'}
    elif a.action=='stop':result=lab.qmp('system_powerdown')
    elif a.action=='view':
        lab.qmp('query-status');os.execvp('remote-viewer',['remote-viewer','spice+unix://'+str(lab.control/'spice.sock')])
    elif a.action=='login':result=lab.login()
    elif a.action=='guest':
        rc,out=lab.serial(a.value or 'true',a.timeout);print(out);return rc
    elif a.action=='query':
        if a.value not in ('query-status','query-name','query-kvm','query-block','query-spice'):raise ValueError('Unsupported read-only query')
        result=lab.qmp(a.value)
    elif a.action=='screenshot':
        path=Path(a.value).resolve()
        if not path.is_relative_to(lab.project) or path.exists():raise ValueError('Choose a new screenshot path inside the project')
        path.parent.mkdir(parents=True,exist_ok=True)
        result=lab.qmp('screendump',{'filename':str(path),'format':'png'})
    elif a.action in ('key','text'):
        chars=[a.value] if a.action=='key' else list(a.value or '')
        mapping={'-':'minus',' ':'spc','.':'dot','@':'shift-2','_':'shift-minus','/':'slash',':':'shift-semicolon','\n':'ret'}
        for ch in chars:
            chord=ch if a.action=='key' else mapping.get(ch,('shift-'+ch.lower()) if ch.isupper() else ch)
            if a.action=='text' and not(ch.isascii() and(ch.isalnum() or ch in mapping)):raise ValueError('Unsupported test character')
            lab.qmp('send-key',{'keys':[{'type':'qcode','data':k} for k in chord.split('-')],'hold-time':30});time.sleep(.07)
        result='Sent to '+NAME
    else:
        x,y,w,h=map(int,a.value.split(','))
        if not(0<=x<=w and 0<=y<=h and w>0 and h>0):raise ValueError('Invalid coordinates')
        lab.qmp('input-send-event',{'events':[{'type':'abs','data':{'axis':'x','value':round(x/w*32767)}},{'type':'abs','data':{'axis':'y','value':round(y/h*32767)}},{'type':'btn','data':{'button':'left','down':True}}]})
        lab.qmp('input-send-event',{'events':[{'type':'btn','data':{'button':'left','down':False}}]});result='Clicked in '+NAME
    print(json.dumps(result,indent=2));return 0


if __name__=='__main__':
    try:sys.exit(main())
    except Exception as e:sys.exit('V2 lab: '+str(e))
