#!/bin/bash
# Run inside the builder container after a successful image build.
set -euo pipefail
cd /src
iso=dist/steins-os-0.1-amd64.iso
[ -s "$iso" ]
(cd dist && sha256sum -c SHA256SUMS)
xorriso -indev "$iso" -report_el_torito plain -report_system_area plain 2>&1 | tee evidence/iso-boot-layout.txt
# Extract the tested ISO's root, so stale build output cannot produce a pass.
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
xorriso -osirrox on -indev "$iso" -extract /live/filesystem.squashfs "$scratch/filesystem.squashfs"
sq=$scratch/filesystem.squashfs
# Debian's stock installer selects a firmware-specific GRUB frontend.
# Both mutually exclusive frontends must be available on the media offline.
xorriso -osirrox on -indev "$iso" -extract /dists "$scratch/dists" -extract /pool "$scratch/pool"
python3 - "$scratch" <<'PYPOOL'
import hashlib
from pathlib import Path
import sys
root = Path(sys.argv[1])
index = root / 'dists/trixie/main/binary-amd64/Packages'
packages = {}
for paragraph in index.read_text().strip().split('\n\n'):
    fields = dict(line.split(': ', 1) for line in paragraph.splitlines() if ': ' in line and not line.startswith(' '))
    if 'Package' not in fields:
        continue
    file = (root / fields['Filename']).resolve()
    assert file.is_relative_to(root.resolve()), fields['Filename']
    assert hashlib.sha256(file.read_bytes()).hexdigest() == fields['SHA256'], file
    packages[fields['Package']] = fields
required = {'grub-pc', 'grub-pc-bin', 'grub-efi', 'grub-efi-amd64', 'grub-efi-amd64-bin', 'grub-common', 'grub2-common'}
assert required <= packages.keys(), required - packages.keys()
print('PASS: offline BIOS/UEFI bootloader pool and every indexed archive hash')
PYPOOL
unsquashfs -cat "$sq" etc/os-release | tee evidence/image-os-release.txt
for file in usr/bin/steins-about usr/bin/steins-info usr/bin/install-steins-os usr/bin/calamares-install-debian usr/lib/steins/calamares-install var/lib/steins/installer/config/settings.conf usr/share/backgrounds/steins/worldline.png usr/share/plymouth/themes/steins/steins.plymouth; do
 unsquashfs -cat "$sq" "$file" > /dev/null
done
for pack in alpha steins-gate hinamizawa hitogashima lugunica mitakihara; do
 for asset in worldline.json wallpaper.svg; do
  path="etc/steins/worldlines/$pack/$asset"
  cmp <(unsquashfs -cat "$sq" "$path") "config/includes.chroot/$path"
 done
done
for pack in higurashi elfen-lied summer-time-rendering; do
 if unsquashfs -cat "$sq" "etc/steins/worldlines/$pack/worldline.json" >/dev/null 2>&1; then
  echo "FAIL: removed pack remains in ISO: $pack" >&2
  exit 1
 fi
done
for file in usr/bin/steins-worldline usr/bin/ibm5100 usr/bin/dmail usr/bin/steins-about usr/bin/steins-info usr/bin/steins-session usr/bin/install-steins-os usr/lib/steins/steinslib.py usr/lib/steins/aboutlib.py etc/steins/default-divergence etc/steins/worldlines/hinamizawa/worldline.json etc/steins/worldlines/mitakihara/worldline.json usr/lib/steins/meterlib.py usr/bin/steins-meter usr/share/applications/steins-meter.desktop; do
 source=$file
 case "$file" in usr/bin/*) source=usr/local/bin/${file#usr/bin/};; usr/lib/steins/*) source=usr/local/lib/steins/${file#usr/lib/steins/};; esac
 cmp <(unsquashfs -cat "$sq" "$file") "config/includes.chroot/$source"
done
unsquashfs -cat "$sq" var/lib/dpkg/status > "$scratch/status"
python3 - "$scratch/status" <<'PYSTATUS'
from pathlib import Path
import sys
expected = Path('packaging/VERSION').read_text().strip()
packages = {}
for paragraph in Path(sys.argv[1]).read_text().split('\n\n'):
    fields = dict(line.split(': ', 1) for line in paragraph.splitlines() if ': ' in line and not line.startswith(' '))
    if 'Package' in fields:
        packages[fields['Package']] = fields
for name in ('steins-artwork', 'steins-branding', 'steins-desktop', 'steins-live-installer'):
    assert packages[name]['Version'] == expected, (name, packages[name]['Version'], expected)
    assert packages[name]['Status'] == 'install ok installed', name
print('PASS: all four Steins packages configured at version', expected)
PYSTATUS
for package in steins-artwork steins-desktop steins-branding steins-live-installer; do
 unsquashfs -cat "$sq" "var/lib/dpkg/info/$package.list" > /dev/null
done
if unsquashfs -cat "$sq" usr/local/bin/steins-worldline >/dev/null 2>&1; then
 echo 'FAIL: unowned legacy /usr/local executable shadows the desktop package' >&2
 exit 1
fi
unsquashfs -cat "$sq" var/lib/steins/installer/config/settings.conf | grep 'branding: steins'
unsquashfs -cat "$sq" var/lib/steins/installer/config/modules/packages.conf | python3 -c '
import sys,yaml
p=yaml.safe_load(sys.stdin)
assert any("calamares" in operation.get("remove", []) for operation in p["operations"]), "Target cleanup leaves a dead generic installer entry"
'
cmp <(unsquashfs -cat "$sq" usr/bin/calamares-install-debian | sed 's|^pkexec calamares$|pkexec calamares --config /var/lib/steins/installer/config|') <(unsquashfs -cat "$sq" usr/lib/steins/calamares-install)
cmp <(unsquashfs -cat "$sq" usr/lib/steins/configure-system) packaging/configure-system
cmp <(unsquashfs -cat "$sq" var/lib/steins/installer/config/branding/steins/stylesheet.qss) config/includes.chroot/usr/share/steins/calamares/stylesheet.qss
unsquashfs -cat "$sq" var/lib/dpkg/diversions | python3 -c '
import sys
lines = sys.stdin.read().splitlines()
assert any(lines[i:i+3] == ["/etc/os-release", "/etc/os-release.debian", "steins-branding"]
           for i in range(0, len(lines), 3)), "Steins identity is not protected from base-files updates"
'
printf 'PASS: ISO checksum, hybrid boot report, rootfs identity, required launchers and exact merged worldline assets/code\n'
