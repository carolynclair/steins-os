#!/usr/bin/python3
"""Offline checkpoints: preserve qcow2 bases, UEFI variables and domain XML."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import pwd
import re
import shutil
import subprocess as sp
import sys
import uuid
import xml.etree.ElementTree as ET

LAB = Path('/var/lib/libvirt/images/SteinsOS-Test')
URI = 'qemu:///system'


def virsh(*args, input=None):
    return sp.run(['virsh', '-c', URI, *args], input=input, text=True, capture_output=True, check=True).stdout


def owned(path):
    p = Path(path).resolve(strict=True)
    assert p.is_relative_to(LAB) and p.is_file(), f'Not a regular lab file: {p}'
    return p


def current():
    state = json.loads((LAB / 'lab.json').read_text())
    assert state['name'] == 'SteinsOS-Test'
    xml = virsh('dumpxml', state['name'], '--inactive')
    root = ET.fromstring(xml)
    assert root.findtext('uuid') == state['uuid'], 'VM UUID differs from this lab'
    disks = root.findall('./devices/disk[@device="disk"]')
    assert len(disks) == 1 and disks[0].get('type') == 'file'
    assert disks[0].find('target').get('bus') == 'virtio'
    disk = owned(disks[0].find('source').get('file'))
    nvram = owned(root.findtext('./os/nvram'))
    assert root.findtext('./os/loader') == '/usr/share/OVMF/OVMF_CODE_4M.fd'
    assert not root.findall('./devices/hostdev') and not root.findall('./devices/filesystem')
    for device in root.findall('./devices/disk'):
        assert device.get('type') == 'file', 'Block/passthrough storage is forbidden'
        source = device.find('source')
        if source is not None and source.get('file'): owned(source.get('file'))
    for interface in root.findall('./devices/interface'):
        assert interface.get('type') == 'network'
        assert interface.find('source').get('network') == state['network']
    return state, root, xml, disk, nvram


def cold(state):
    assert virsh('domstate', state['name']).strip() == 'shut off', 'Shut the guest down completely first; paused/saved state is not sufficient'
    assert shutil.disk_usage(LAB).free >= 8 * 1024**3, 'Keep at least 8 GiB free before making/restoring checkpoints'


def save_xml(root, path):
    ET.indent(root)
    path.write_text(ET.tostring(root, encoding='unicode') + '\n')


def overlay(base):
    chain = json.loads(sp.check_output(['qemu-img', 'info', '--backing-chain', '--output=json', str(base)]))
    assert len(chain) < 8, 'Chain limit reached; consolidate/export before more checkpoints'
    for entry in chain: owned(entry['filename'])
    dest = LAB / ('run-' + uuid.uuid4().hex + '.qcow2')
    sp.run(['qemu-img', 'create', '-f', 'qcow2', '-F', 'qcow2', '-b', str(base), str(dest)], check=True)
    qemu = pwd.getpwnam('libvirt-qemu')
    os.chown(dest, qemu.pw_uid, qemu.pw_gid); dest.chmod(0o600)
    return dest


def set_disk(root, disk):
    node = root.find('./devices/disk[@device="disk"]')
    node.find('source').set('file', str(disk))
    for tag in ('backingStore', 'mirror'):
        for old in node.findall(tag): node.remove(old)


def label(value):
    assert re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,39}', value), 'Use a short label containing letters, digits, hyphens or underscores'
    return value


def main():
    assert os.geteuid() == 0, 'Use pkexec or sudo for checkpoint file access'
    action = sys.argv[1] if len(sys.argv) > 1 else 'verify'
    state, root, xml, disk, nvram = current()
    if action == 'verify':
        assert root.get('type') == 'kvm'
        assert int(root.findtext('memory')) == 6144 * 1024  # libvirt normalises to KiB
        assert root.findtext('vcpu') == '2'
        assert root.find('./devices/graphics').get('type') == 'spice'
        assert root.find('./devices/graphics/listen').get('type') == 'none'
        net = ET.fromstring(virsh('net-dumpxml', state['network']))
        assert net.find('forward').get('mode') == 'nat'
        info = json.loads(sp.check_output(['qemu-img', 'info', '--output=json', str(disk)]))
        assert info['virtual-size'] == 40 * 1024**3 and info['format'] == 'qcow2'
        print('PASS: KVM definition, 6 GiB/2 vCPU, UEFI, 40 GiB VirtIO qcow2, NAT, local SPICE and file-only lab storage')
        return
    cold(state)
    name = label(sys.argv[2]) if len(sys.argv) > 2 else ''
    if action == 'checkpoint':
        folder = LAB / 'checkpoints' / name
        assert name and not folder.exists(), 'Checkpoint exists or missing label; refusing overwrite'
        folder.mkdir()
        (folder / 'domain.xml').write_text(xml)
        shutil.copy2(nvram, folder / 'nvram.fd')
        (folder / 'checkpoint.json').write_text(json.dumps({'base': str(disk), 'uuid': state['uuid'], 'nvram_sha256': hashlib.sha256(nvram.read_bytes()).hexdigest()}, indent=2) + '\n')
        new = overlay(disk)
        set_disk(root, new)
        path = folder / 'next-domain.xml'; save_xml(root, path)
        virsh('define', str(path))
        print(f'Checkpoint {name} saved; new guest writes go to {new.name}. No existing disk was overwritten.')
    elif action == 'restore':
        folder = LAB / 'checkpoints' / name
        data = json.loads((folder / 'checkpoint.json').read_text())
        assert data['uuid'] == state['uuid']
        saved = owned(folder / 'nvram.fd')
        assert hashlib.sha256(saved.read_bytes()).hexdigest() == data['nvram_sha256']
        target = ET.fromstring((folder / 'domain.xml').read_text())
        assert target.findtext('uuid') == state['uuid']
        assert target.findtext('./os/nvram') == str(nvram)
        new = overlay(owned(data['base']))
        history = LAB / 'history' / (dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:8])
        history.mkdir(); (history / 'domain.xml').write_text(xml)
        shutil.copy2(nvram, history / 'nvram.fd')
        set_disk(target, new); path = history / 'restored-domain.xml'; save_xml(target, path)
        try:
            # Copy bytes into the existing lab-owned NVRAM file, preserving DAC/security metadata.
            nvram.write_bytes(saved.read_bytes())
            virsh('define', str(path))
        except Exception:
            nvram.write_bytes((history / 'nvram.fd').read_bytes())
            virsh('define', '/dev/stdin', input=xml)
            raise
        print(f'Restored {name}; previous disk chain and UEFI variables retained in history. No disk files deleted.')
    else:
        raise SystemExit('Use verify, checkpoint LABEL, or restore LABEL')


if __name__ == '__main__':
    main()
