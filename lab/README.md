# Steins;OS local testing lab

Prepared for Gary's ParrotOS laptop, 2026-11-01 NZDT. `VALIDATION.md` records what actually ran; scripts alone are not proof of installation.

## Install/configure

From the project folder, run `./lab/setup.sh`. Parrot/KDE will request administrator authentication. Enter your password in that system dialog, never into chat. If the dialog is unavailable, run `sudo ./lab/setup.sh` in your own terminal. The setup requires the recorded ISO checksum; it stops if a lab directory, helper, VM or network already exists instead of replacing it. A failed partial setup is retained for inspection, not silently deleted or overwritten.

The elevated operations install the missing libvirt/virt-manager tools through APT with package removals disabled, enable libvirtd, add the regular user to `libvirt` and `kvm`, and create one named VM plus a separate NAT network. No blanket host upgrade, disk partitioning, formatting, bootloader change, panel/theme change, shared host directory or device passthrough is performed. Standard package dependencies may create libvirt's default network as well; existing networks are not redefined. No sudoers or custom Polkit exception is installed.

VM: **SteinsOS-Test**, `qemu:///system`, KVM, 6144 MiB RAM, two vCPUs, Q35, OVMF UEFI with private writable variables, 40 GiB sparse qcow2/VirtIO disk, VirtIO Ethernet/NAT, VirtIO video and local SPICE through libvirt. Secure Boot is disabled for this lab. Clipboard/file transfer and 3D acceleration are disabled. SPICE has no TCP listener. Storage, the verified ISO copy and checkpoints are confined to `/var/lib/libvirt/images/SteinsOS-Test`.

## Launch and install safely

Run `./lab/steins-vm-lab launch` as Gary. It starts the guest if necessary and opens its virt-manager console. It uses the new libvirt group membership immediately; normal Virtual Machine Manager → QEMU/KVM → SteinsOS-Test also works; plain regular-user libvirt access was verified in this session. Do not launch virt-manager with sudo.

1. Test the live desktop, launcher, terminal, networking and normal shutdown. Live credentials: `lab` / `live`.
2. In the guest only, choose **Install Steins;OS**. Its sole writable disk is the **40 GiB VirtIO virtual disk**. This is the intended installation destination; no physical laptop disk is exposed.
3. When installation finishes, shut down fully. Run `./lab/steins-vm-lab boot-disk` to eject the ISO persistently, then `./lab/steins-vm-lab launch` to test installed boot, your personal login, networking, desktop and shutdown.
4. Once the installed system is satisfactory and fully shut down, run `./lab/steins-vm-lab checkpoint installed-clean`.
5. To return to the live ISO later, shut down and run `./lab/steins-vm-lab boot-iso`.

Status: `./lab/steins-vm-lab status`. A shutdown request can require confirmation inside the guest; verify it says **shut off**, not merely paused.

## Checkpoints

The setup creates **ready-to-install** before first boot and tests restoring it. To save another checkpoint, shut the VM down completely and run `./lab/steins-vm-lab checkpoint LABEL`. Restore with `./lab/steins-vm-lab restore LABEL`. Parrot authentication is required for checkpoint files and UEFI-variable copies. Do not take these checkpoints while the guest is running or in a saved/paused state.

Each checkpoint preserves a frozen qcow2 base, the domain XML and UEFI variables. Subsequent writes use a fresh external qcow2 overlay with an explicit backing format. Restoring creates another overlay; it does not delete or overwrite previous disk chains. The pre-restore XML and UEFI variables are retained in `history/`. Checkpoints include ISO attachment/boot configuration. Do not move/rename chain files, discard backing images or remove these checkpoints using virt-manager's snapshot UI; use the supplied helper. Chains are limited to eight layers pending an explicit consolidation/export.

This follows libvirt's [backing-chain guidance](https://libvirt.org/kbase/backing_chains.html), including explicit backing formats. UEFI and local SPICE are described in the [domain XML reference](https://libvirt.org/formatdomain.html); NAT in the [network reference](https://libvirt.org/formatnetwork.html).

## Capacity limits

The initial host inspection found about **22 GiB free** and **12 GiB available RAM**. The 40 GiB virtual disk is dynamically allocated; 40 GiB is **not reserved or currently available on the host**. The ISO copy and guest writes consume that same free filesystem space. Offline overlays avoid 6 GiB RAM snapshots and full-disk checkpoint copies.

The launcher requires 10 GiB free and 8 GiB available RAM before a cold start; checkpoint operations require 8 GiB free. Starting directly in virt-manager bypasses those launcher checks. Monitor host space during testing with `df -h /var/lib/libvirt/images` and the status command; free space or stop testing before approaching exhaustion. Disk write errors pause the VM. Snapshots share backing files and are not independent backups.

The setup does not install Steins;OS into the guest automatically. Installed-system tests remain for your test session; the prepared pristine checkpoint lets you repeat them.
