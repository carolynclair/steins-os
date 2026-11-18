FROM debian:trixie
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends live-build debootstrap ca-certificates xorriso isolinux syslinux-common grub-pc-bin grub-efi-amd64-bin mtools dosfstools squashfs-tools qemu-utils python3 python3-yaml librsvg2-bin dpkg-dev && rm -rf /var/lib/apt/lists/*
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends fonts-dejavu fonts-noto-core fonts-liberation && rm -rf /var/lib/apt/lists/*
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends apt-utils && rm -rf /var/lib/apt/lists/*
WORKDIR /build
