#!/bin/bash
set -euo pipefail
if [[ $# != 2 ]]; then
    echo "Usage: $0 PREPARED_XFCE_BUILD V4_DEB_TREE" >&2
    exit 2
fi
project=$(cd "$(dirname "$0")" && pwd)
xfce=$(realpath "$1")
packages=$(realpath "$2")
mkdir -p config
cp -a "$xfce/auto" .
for directory in package-lists hooks steins-assets; do
    cp -a "$xfce/config/$directory" config/
done
mkdir -p config/packages.chroot config/includes.chroot/usr/share/steins-v4
cp "$packages"/packages/*.deb "$packages"/v4/{core,identity,panel,surfaces,surfaces/terminal}/*.deb config/packages.chroot/
cp "$project/default-panel.js" config/includes.chroot/usr/share/steins-v4/
cp "$project/0910-plasma.hook.chroot" config/hooks/live/
sed -i 's/--image-name steins-os-0.1-amd64/--image-name steins-os-v4/; s/Steins;OS 0.1 — Gate of Steiner/Steins;OS V4 Plasma/; s/--iso-volume STEINS_OS /--iso-volume STEINS_OS_V4 /' auto/config
printf '%s\n' kde-plasma-desktop sddm konsole dolphin thunderbird > config/package-lists/steins-plasma.list.chroot
