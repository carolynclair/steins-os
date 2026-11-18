#!/usr/bin/env python3
"""Start/view/stop the standalone disposable prototype, without root or libvirt edits."""
import argparse
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / 'evidence/plasma-prototype'
ap = argparse.ArgumentParser()
ap.add_argument('action', choices=('start', 'view', 'stop', 'status'))
a = ap.parse_args()
monitor = [sys.executable, str(ROOT / 'prototype/monitor.py')]
running = subprocess.run(monitor + ['query', 'query-status'], capture_output=True)
if a.action == 'status':
    print(running.stdout.decode() if running.returncode == 0 else 'Prototype is off')
    sys.exit(0)
if a.action == 'stop':
    if running.returncode == 0: subprocess.run(monitor + ['poweroff'], check=True)
    else: print('Prototype is already off')
    sys.exit(0)
if a.action == 'start':
    if running.returncode == 0: sys.exit('Prototype is already running')
    # Small host: avoid running alongside the review VM or another libvirt guest.
    domains = subprocess.run(['virsh', '-c', 'qemu:///system', 'list', '--name'], capture_output=True, text=True, check=True)
    if domains.stdout.strip(): sys.exit('Shut down running libvirt guests before starting the prototype')
    memory = dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())
    if int(memory['MemAvailable'].split()[0]) < 8*1024*1024: sys.exit('At least 8 GiB available RAM is required')
    if shutil.disk_usage(ROOT).free < 10*1024**3: sys.exit('At least 10 GiB free disk space is required')
    disk = LAB / 'system.qcow2'
    if not disk.is_file(): sys.exit('The prepared prototype disk is missing; see prototype/README.md')
    import json
    image = json.loads(subprocess.check_output(['qemu-img','info','--output=json',str(disk)]))
    if image.get('full-backing-filename') != str(ROOT / 'evidence/vm/packaged-uefi.qcow2'):
        sys.exit('Unexpected backing disk; refusing to start')
    pidfile = LAB / 'qemu.pid'
    if pidfile.exists():
        pid = int(pidfile.read_text())
        if Path('/proc',str(pid)).exists(): sys.exit('A recorded process still exists; inspect before starting')
        pidfile.unlink()
    args = ['qemu-system-x86_64','-name','SteinsOS-Design-Prototype','-enable-kvm','-m','6144','-smp','2',
        '-drive','file='+str(disk)+',if=virtio,format=qcow2',
        '-drive','if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd',
        '-drive','if=pflash,format=raw,file='+str(LAB/'OVMF_VARS.fd'),
        '-device','virtio-vga','-device','qemu-xhci','-device','usb-tablet',
        '-nic','user,model=virtio-net-pci','-display','none','-daemonize','-pidfile',str(pidfile),
        '-qmp','unix:/tmp/steins-design-qmp.sock,server=on,wait=off',
        '-chardev','socket,id=serial0,path=/tmp/steins-design-serial.sock,server=on,wait=off,logfile='+str(LAB/'serial.log'),
        '-serial','chardev:serial0',
        '-spice','unix=on,addr=/tmp/steins-design-spice.sock,disable-ticketing=on,disable-copy-paste=on,disable-agent-file-xfer=on']
    subprocess.run(['sg','kvm','-c',shlex.join(args)], check=True)
    print('Prototype started. Run python3 prototype/vm.py view to open its console.')
else:
    if running.returncode: sys.exit('Start the prototype first')
    if not Path('/tmp/steins-design-spice.sock').exists(): sys.exit('Restart the prototype with this launcher to enable its SPICE console')
    os.execvp('remote-viewer',['remote-viewer','spice+unix:///tmp/steins-design-spice.sock'])
