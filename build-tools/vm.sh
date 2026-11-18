#!/bin/bash
# Explicitly creates and operates only a disposable qcow2 image, never /dev disks.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p evidence/vm
mode=${1:-bios}
case "$mode" in bios|bios-disk) disk=evidence/vm/target.qcow2;; uefi|uefi-disk) disk=evidence/vm/target-uefi.qcow2;; *) echo 'Use bios, bios-disk, uefi or uefi-disk' >&2; exit 2;; esac
[ -f "$disk" ] || qemu-img create -f qcow2 "$disk" 32G
args=()
if [[ "$mode" = uefi* ]]; then
 [ -f evidence/vm/OVMF_VARS.fd ] || cp /usr/share/OVMF/OVMF_VARS_4M.fd evidence/vm/OVMF_VARS.fd
 args+=(-drive if=pflash,format=raw,readonly=on,file=/usr/share/OVMF/OVMF_CODE_4M.fd -drive if=pflash,format=raw,file=evidence/vm/OVMF_VARS.fd)
fi
media=(-boot order=c)
if [[ "$mode" != *-disk ]]; then media=(-cdrom dist/steins-os-0.1-amd64.iso -boot order=d); fi
exec qemu-system-x86_64 -enable-kvm -m 4096 -smp 2 \
 -drive "file=$disk,format=qcow2,if=virtio" \
 "${media[@]}" \
 -device virtio-vga -device qemu-xhci -device usb-tablet \
 -nic user,model=virtio-net-pci -display none -daemonize -pidfile evidence/vm/qemu.pid \
 -qmp unix:/tmp/steins-qmp.sock,server=on,wait=off \
 -chardev socket,id=serial0,path=/tmp/steins-serial.sock,server=on,wait=off,logfile=evidence/vm/${mode}-serial.log -serial chardev:serial0 "${args[@]}"
