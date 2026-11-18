#!/bin/bash
# Authenticate through Parrot/KDE, never by sending a password into chat.
set -euo pipefail
cd "$(dirname "$0")"
iso=${1:-../dist/steins-os-0.1-amd64.iso}
iso=$(realpath "$iso")
expected=9216cfec7ddc39ad6b5559b74a60c8207317869c1733a2be6dac184d5ec33a31
printf '%s\n' 'Elevated changes: install libvirt/virt-manager dependencies (no removals), start libvirtd, add your user to libvirt/kvm, create a dedicated NAT network and file-backed VM. No physical disk, bootloader, existing VM or KDE setting is changed.'
if [ "$(id -u)" -eq 0 ]; then
  exec /usr/bin/python3 "$PWD/setup-lab.py" --user "${SUDO_USER:-gary}" --iso "$iso" --sha256 "$expected"
else
  exec pkexec --disable-internal-agent /usr/bin/python3 "$PWD/setup-lab.py" --user "$(id -un)" --iso "$iso" --sha256 "$expected"
fi
