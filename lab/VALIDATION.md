# VM lab validation — 2026-11-01 NZDT

Configured directly on Gary's Parrot Security 7.4 laptop: Intel Celeron N4500, 2 cores/threads, approximately 20 GB RAM. The regular account is Gary (UID 1000). No existing libvirt domains were present; earlier project test images were not changed.

## Configured and verified

| Item | Result |
|---|---|
| Host hypervisor | QEMU 10.0.13, libvirt 11.3.0; /dev/kvm API 12; running QEMU reports KVM enabled |
| User permissions | Gary added to libvirt/kvm; plain regular-user virsh lists/manages the VM; virt-manager runs as Gary |
| VM | SteinsOS-Test, persistent qemu:///system domain; UUID 9fa315e1-19c8-4aa2-9854-0965a7bc956c; no automatic start on host boot |
| Resources | 6144 MiB RAM; 2 host-passthrough vCPUs; Q35 |
| Firmware | Read-only OVMF_CODE_4M.fd with lab-private writable nvram.fd; UEFI menu boots successfully; Secure Boot disabled |
| Storage | 40 GiB sparse qcow2/VirtIO vda, external backing chain; read-only ISO file as SATA CD; all VM storage under /var/lib/libvirt/images/SteinsOS-Test |
| Isolation | File-backed disks only; no physical disk, PCI/USB device or host-directory passthrough; AppArmor enforcing |
| ISO | Latest verified Steins;OS 0.1 image, SHA-256 9216cfec7ddc39ad6b5559b74a60c8207317869c1733a2be6dac184d5ec33a31; verified copy in the lab |
| Graphics | VirtIO video, 3D off; virt-manager's SPICE display/cursor/input channels connected over UNIX transport, no SPICE TCP listener |
| NAT | Dedicated SteinsOSLab, virbr-stos, 192.168.157.0/24; host default route unchanged |
| Guest networking | DHCP address 192.168.157.125; route via .1; Debian hostname resolved; HTTPS HEAD returned HTTP/2 200 |
| Live desktop | Booted normally; XFCE, panel, wallpaper, system readout and terminal visible |
| Shutdown | Guest sudo poweroff produced SHUTDOWN_GUEST then STOPPED_SHUTDOWN lifecycle events; not a forced VM termination |
| Current handoff | The VM was started again through virt-manager while Gary began reviewing it; left running for that review |
| Checkpoints | ready-to-install created and restored before first boot; new overlays selected, original disk files retained; XML and UEFI-variable copies saved |

The installation intentionally leaves the 40 GiB virtual disk blank. Guest installer execution, installed-system reboot and installed-clean checkpoint/data rollback have **not** been tested in this new VM. Follow README.md to install inside the VM, eject the ISO and save an installed-clean checkpoint after shutdown. Earlier distribution installation tests used different disposable VMs and are not substituted for this lab's results.

## Changes and resolved error

The initial package installation added 43 packages without host package upgrades or removals. Its minimal dependency selection missed virt-manager's optional SPICE introspection bindings. The console reported `Namespace SpiceClientGtk not available`; installing `gir1.2-spiceclientgtk-3.0` and its dependencies (3 additional packages, zero upgrades/removals), then restarting only the console, resolved it. The setup script now includes this dependency explicitly. Parrot's normal APT post-install hooks also ran.

Enabled libvirtd and the dedicated NAT network, added the requested groups, and installed the scoped checkpoint helper at /usr/local/libexec/steins-vm-lab. Standard libvirt packages also supplied the default network; it was not repurposed or overwritten. No custom sudoers/Polkit permission rule, host partitioning, physical-disk formatting or host bootloader operation was performed. No existing KDE panel/theme configuration was edited.

## Limits and evidence

Approximately 21 GiB host filesystem space remained after setup. The 40 GiB guest capacity is not reserved; monitor host space and observe the launcher/checkpoint thresholds in README.md. Direct virt-manager starts bypass launcher resource checks. External checkpoints are space-efficient rollback points, not independent backups, and only operate while the VM is fully shut down. Live-session RAM changes are not preserved by disk-only checkpoints; install the guest to persist desktop settings.

Evidence is in evidence/vm-lab/: setup.log, spice-client-repair.log, host-before.json, domain-final.xml, network.xml, kvm-enabled.json, spice-connected.json, user-management.txt, dhcp.txt, network-check.png and virt-manager-fixed.log (contains the normal shutdown/restart lifecycle events). Read-only monitor diagnostics produced a temporary libvirt custom-monitor taint on the first VM run; the subsequent normal start cleared that runtime flag. No hypervisor failure was observed.

Scripts: setup.sh, setup-lab.py, checkpoint.py and steins-vm-lab. Their shell/Python syntax checks pass. They reject existing storage/domain names rather than overwrite them. The setup is completed; do not rerun it to launch the VM. Use steins-vm-lab launch or normal Virtual Machine Manager instead.
