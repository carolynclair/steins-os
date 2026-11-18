#!/usr/bin/python3
"""Install the host tools and create ONLY the named Steins;OS virtual lab."""
import argparse
import fcntl
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import pwd
import shutil
import subprocess as sp
import sys
import uuid
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
LAB = Path('/var/lib/libvirt/images/SteinsOS-Test')
NAME = 'SteinsOS-Test'
NETWORK = 'SteinsOSLab'
URI = 'qemu:///system'
PACKAGES = ['qemu-system-x86', 'qemu-system-gui', 'qemu-utils',
            'libvirt-daemon-system', 'libvirt-daemon-driver-qemu',
            'libvirt-clients', 'virt-manager', 'virtinst', 'virt-viewer',
            'ovmf', 'dnsmasq-base', 'gir1.2-spiceclientgtk-3.0']


def run(*args, **kwargs):
    print('+', ' '.join(map(str, args)), flush=True)
    return sp.run(list(map(str, args)), check=True, **kwargs)


def virsh(*args):
    return run('virsh', '-c', URI, *args, capture_output=True, text=True).stdout


def digest(path):
    with open(path, 'rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def define_xml(root, filename, command):
    path = LAB / filename
    ET.indent(root)
    path.write_text(ET.tostring(root, encoding='unicode') + '\n')
    virsh(command, str(path))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--user', default='gary')
    p.add_argument('--iso', type=Path, required=True)
    p.add_argument('--sha256', required=True)
    a = p.parse_args()
    if os.geteuid() != 0:
        raise SystemExit('Run with sudo or the supplied Parrot authentication launcher.')
    account = pwd.getpwnam(a.user)
    assert account.pw_uid != 0, 'A regular user is required'
    iso = a.iso.resolve(strict=True)
    assert iso.is_file() and iso.suffix == '.iso', 'Expected a regular ISO file'
    assert digest(iso) == a.sha256.lower(), 'ISO checksum mismatch'
    assert Path('/dev/kvm').exists(), 'KVM is unavailable'
    with open('/dev/kvm', 'r+b', buffering=0) as kvm:
        assert fcntl.ioctl(kvm, 0xAE00, 0) == 12, 'Unexpected KVM API'
    # Refuse existing storage before doing any package/configuration work.
    assert not LAB.exists(), f'{LAB} already exists; inspect it, do not overwrite it'
    assert shutil.disk_usage('/var/lib').free >= 16 * 1024**3, 'Need 16 GiB free for setup and the initial guest installation'
    helper = Path('/usr/local/libexec/steins-vm-lab')
    assert not helper.exists(), f'Existing helper {helper}; refusing to overwrite'
    plan = run('apt-get', '-s', '--no-remove', '--no-install-recommends',
               'install', *PACKAGES, capture_output=True, text=True).stdout
    print(plan, flush=True)
    # --no-remove prevents an installation resolver from removing host packages.
    env = dict(os.environ, DEBIAN_FRONTEND='noninteractive')
    run('apt-get', 'update', env=env)
    run('apt-get', '-y', '--no-remove', '--no-install-recommends',
        '-o', 'Dpkg::Options::=--force-confold', 'install', *PACKAGES, env=env)
    run('systemctl', 'enable', '--now', 'libvirtd.service')
    inventory = virsh('list', '--all', '--name').splitlines()
    assert NAME not in inventory, f'Existing VM {NAME}; refusing to overwrite'
    assert NETWORK not in virsh('net-list', '--all', '--name').splitlines(), 'Existing SteinsOSLab network; refusing to overwrite'
    run('usermod', '-aG', 'libvirt,kvm', a.user)
    qemu_user = pwd.getpwnam('libvirt-qemu')
    run('usermod', '-aG', 'kvm', 'libvirt-qemu')
    LAB.mkdir(mode=0o755)
    LAB.chmod(0o755)
    (LAB / 'checkpoints').mkdir(mode=0o755)
    (LAB / 'history').mkdir(mode=0o755)
    identity = str(uuid.uuid4())
    state = {'name': NAME, 'uuid': identity, 'network': NETWORK,
             'user': a.user, 'iso_sha256': a.sha256, 'uri': URI,
             'stage': 'preparing', 'original_domains': inventory}
    (LAB / 'lab.json').write_text(json.dumps(state, indent=2) + '\n')
    (LAB / 'lab.json').chmod(0o644)
    target_iso = LAB / 'steins-os.iso'
    run('cp', '--reflink=auto', '--sparse=always', '--no-clobber', iso, target_iso)
    assert digest(target_iso) == a.sha256, 'Copied ISO failed checksum'
    target_iso.chmod(0o644)
    disk = LAB / 'base.qcow2'
    run('qemu-img', 'create', '-f', 'qcow2', disk, '40G')
    nvram = LAB / 'nvram.fd'
    shutil.copyfile('/usr/share/OVMF/OVMF_VARS_4M.fd', nvram)
    for path in (disk, nvram):
        os.chown(path, qemu_user.pw_uid, qemu_user.pw_gid)
        path.chmod(0o600)
    occupied = []
    routes = json.loads(run('ip', '-j', '-4', 'route', 'show', 'table', 'all', capture_output=True, text=True).stdout)
    for route in routes:
        dest = route.get('dst', 'default')
        if dest != 'default':
            occupied.append(ipaddress.ip_network(dest, strict=False))
    for net in virsh('net-list', '--all', '--name').splitlines():
        if not net: continue
        for ip in ET.fromstring(virsh('net-dumpxml', net)).findall('ip'):
            if ip.get('address') and ':' not in ip.get('address'):
                occupied.append(ipaddress.ip_network(f"{ip.get('address')}/{ip.get('netmask', ip.get('prefix', '24'))}", strict=False))
    candidates = ['192.168.157.0/24', '192.168.158.0/24', '192.168.159.0/24', '10.240.77.0/24', '172.30.157.0/24']
    subnet = next((ipaddress.ip_network(x) for x in candidates if not any(ipaddress.ip_network(x).overlaps(n) for n in occupied)), None)
    assert subnet is not None, 'No non-overlapping candidate NAT subnet; review host routes'
    assert not Path('/sys/class/net/virbr-stos').exists(), 'Existing virbr-stos bridge; refusing to reuse'
    net = ET.Element('network')
    ET.SubElement(net, 'name').text = NETWORK
    ET.SubElement(net, 'forward', mode='nat')
    ET.SubElement(net, 'bridge', name='virbr-stos', stp='on', delay='0')
    ip = ET.SubElement(net, 'ip', address=str(subnet[1]), netmask='255.255.255.0')
    dhcp = ET.SubElement(ip, 'dhcp')
    ET.SubElement(dhcp, 'range', start=str(subnet[100]), end=str(subnet[200]))
    define_xml(net, 'network.xml', 'net-define')
    virsh('net-start', NETWORK)
    virsh('net-autostart', NETWORK)
    caps = ET.fromstring(virsh('domcapabilities', '--virttype', 'kvm', '--arch', 'x86_64', '--machine', 'q35'))
    machine = caps.findtext('machine') or 'q35'
    domain = ET.fromstring(f'''<domain type="kvm">
      <name>{NAME}</name><uuid>{identity}</uuid>
      <title>Steins;OS isolated testing lab</title>
      <memory unit="MiB">6144</memory><currentMemory unit="MiB">6144</currentMemory>
      <vcpu placement="static">2</vcpu>
      <os><type arch="x86_64" machine="{machine}">hvm</type>
       <loader readonly="yes" secure="no" type="pflash">/usr/share/OVMF/OVMF_CODE_4M.fd</loader>
       <nvram>{nvram}</nvram><bootmenu enable="yes"/></os>
      <features><acpi/><apic/></features>
      <cpu mode="host-passthrough" check="none"><topology sockets="1" dies="1" cores="2" threads="1"/></cpu>
      <clock offset="utc"/><on_poweroff>destroy</on_poweroff><on_reboot>restart</on_reboot><on_crash>destroy</on_crash>
      <devices><emulator>/usr/bin/qemu-system-x86_64</emulator>
       <disk type="file" device="disk"><driver name="qemu" type="qcow2" cache="none" discard="unmap" error_policy="stop"/>
        <source file="{disk}"/><target dev="vda" bus="virtio"/><boot order="2"/></disk>
       <controller type="sata" index="0"/>
       <disk type="file" device="cdrom"><driver name="qemu" type="raw"/><source file="{target_iso}"/>
        <target dev="sda" bus="sata"/><readonly/><boot order="1"/></disk>
       <interface type="network"><source network="{NETWORK}"/><model type="virtio"/></interface>
       <controller type="usb" model="qemu-xhci"/><input type="tablet" bus="usb"/>
       <graphics type="spice"><listen type="none"/><clipboard copypaste="no"/><filetransfer enable="no"/></graphics>
       <video><model type="virtio" heads="1" primary="yes"><acceleration accel3d="no"/></model></video>
       <channel type="spicevmc"><target type="virtio" name="com.redhat.spice.0"/></channel>
       <serial type="pty"><target port="0"/></serial><console type="pty"><target type="serial" port="0"/></console>
       <memballoon model="virtio"/>
       <rng model="virtio"><backend model="random">/dev/urandom</backend></rng>
      </devices></domain>''')
    define_xml(domain, 'initial-domain.xml', 'define')
    helper.parent.mkdir(parents=True, exist_ok=True)
    with helper.open('xb') as f: f.write((HERE / 'checkpoint.py').read_bytes())
    helper.chmod(0o755)
    state.update(stage='configured', subnet=str(subnet))
    (LAB / 'lab.json').write_text(json.dumps(state, indent=2) + '\n')
    run(helper, 'checkpoint', 'ready-to-install')
    run(helper, 'restore', 'ready-to-install')
    run(helper, 'verify')
    print('SETUP SUCCESS: SteinsOS-Test defined; pristine checkpoint created and restore tested.', flush=True)


if __name__ == '__main__':
    try: main()
    except Exception as error:
        print(f'SETUP STOPPED: {error}. Existing VMs were not overwritten; inspect retained partial lab files before retrying.', file=sys.stderr)
        raise
