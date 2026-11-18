#!/bin/bash
# Reassemble only the media package pool/checksums/ISO after a successful build.
# Runtime source/rootfs changes require rebuild-tested.sh instead.
set -euo pipefail
ulimit -n 4096
cd /src/build
for stage in binary_chroot binary_rootfs binary_linux-image binary_grub-efi binary_syslinux; do
 test -f ".build/$stage"
done
test -s binary/live/filesystem.squashfs
before=$(sha256sum binary/live/filesystem.squashfs)
cp /src/config/package-lists/*.list.binary config/package-lists/
rm -f .build/binary_package-lists .build/binary_checksums .build/binary_iso
lb binary
[ "$before" = "$(sha256sum binary/live/filesystem.squashfs)" ]
printf '%s\n' "$before" > /src/evidence/packaged-rootfs-preserved.txt
cp steins-os-0.1-amd64-amd64.hybrid.iso /src/dist/.steins-os-0.1-amd64.iso.new
mv -f /src/dist/.steins-os-0.1-amd64.iso.new /src/dist/steins-os-0.1-amd64.iso
cd /src/dist
sha256sum steins-os-0.1-amd64.iso > SHA256SUMS
chown -R "$(stat -c %u:%g /src)" /src/dist
