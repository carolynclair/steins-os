#!/usr/bin/env python3
"""Build the four local Steins Debian packages without installing on the host."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / 'config/includes.chroot'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=ROOT / 'dist/packages')
parser.add_argument('--version', default=(ROOT / 'packaging/VERSION').read_text().strip())
args = parser.parse_args()
version = args.version
subprocess.run(['dpkg', '--validate-version', version], check=True)
output = args.output.resolve()
output.mkdir(parents=True, exist_ok=True)
epoch = os.environ.get('SOURCE_DATE_EPOCH') or (ROOT / 'packaging/SOURCE_DATE_EPOCH').read_text().strip()
definitions = {
    'steins-artwork': ('Original Steins;OS laboratory artwork and boot splash', ''),
    'steins-desktop': ('Steins;OS XFCE defaults, worldlines and native tools',
        'steins-artwork (>= 0.1), steins-branding (>= 0.1), python3, python3-gi, gir1.2-gtk-3.0, xfce4, xfce4-terminal, xfce4-whiskermenu-plugin, conky-all, librsvg2-bin, papirus-icon-theme, dmz-cursor-theme, fonts-dejavu, fonts-jetbrains-mono, fonts-noto-core'),
    'steins-branding': ('Steins;OS identity, greeter and generated theme integration',
        'steins-artwork (>= 0.1), base-files, python3, python3-yaml, greybird-gtk-theme, lightdm-gtk-greeter, plymouth, initramfs-tools'),
    'steins-live-installer': ('Steins;OS live installer branding and launcher',
        'steins-desktop (>= 0.1), steins-branding (>= 0.1), calamares, calamares-settings-debian, console-setup, zenity'),
}
# Keep the current export unambiguous; retain old experiments outside its index.
for package in definitions:
    for previous in output.glob(package + '_*_all.deb'):
        if previous.name != f'{package}_{version}_all.deb':
            history = output.parent / (output.name + '-history')
            history.mkdir(exist_ok=True)
            destination = history / previous.name
            if destination.exists():
                destination = history / (previous.stem + '-' + hashlib.sha256(previous.read_bytes()).hexdigest()[:8] + '.deb')
            previous.replace(destination)
diversions = {
    'steins-branding': ['/etc/os-release'],
    'steins-live-installer': ['/usr/share/applications/calamares-install-debian.desktop'],
}
legacy = json.loads((ROOT / 'packaging/legacy-hashes.json').read_text())
for p in (OVERLAY / 'usr/local').rglob('*'):
    if p.is_file() and '__pycache__' not in p.parts:
        name = '/' + p.relative_to(OVERLAY).as_posix()
        legacy.setdefault(name, [])
        legacy[name] = sorted(set(legacy[name] + [hashlib.sha256(p.read_bytes()).hexdigest()]))


def put(stage, path, data, mode=0o644):
    p = stage / path.lstrip('/')
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data if isinstance(data, bytes) else data.encode())
    p.chmod(mode)
    return p


def migrate_script(package):
    lines = []
    checks = ['migrate_legacy=true',
              'if [ -L /usr/local/bin ] || [ -L /usr/local/lib ] || [ -L /usr/local/lib/steins ]; then migrate_legacy=false; fi']
    for path, hashes in sorted(legacy.items()):
        owner = 'steins-live-installer' if path.endswith('/install-steins-os') else 'steins-desktop'
        if package != owner:
            continue
        checks += [f'if [ -e "{path}" ] || [ -L "{path}" ]; then',
                   f' if [ -f "{path}" ] && [ ! -L "{path}" ] && ! dpkg-query -S "{path}" >/dev/null 2>&1; then',
                   f'  actual=$(sha256sum "{path}"); actual=${{actual%% *}}',
                   '  case "$actual" in ' + '|'.join(hashes) + ') : ;; *) migrate_legacy=false ;; esac',
                   ' else migrate_legacy=false; fi', 'fi']
        backup = '/var/lib/steins/legacy' + path
        checks += [f'if [ -e "{path}" ] && [ -e "{backup}" ] && ! cmp -s "{path}" "{backup}"; then migrate_legacy=false; fi']
        lines += [f'if [ -f "{path}" ] && [ ! -L "{path}" ] && ! dpkg-query -S "{path}" >/dev/null 2>&1; then',
                  f' actual=$(sha256sum "{path}"); actual=${{actual%% *}}',
                  ' case "$actual" in', '  ' + '|'.join(hashes) + ')',
                  f'   mkdir -p "$(dirname "{backup}")"',
                  f'   if [ ! -e "{backup}" ]; then mv "{path}" "{backup}";',
                  f'   elif cmp -s "{path}" "{backup}"; then rm "{path}";',
                  f'   else echo "Preserving differing legacy override: {path}" >&2; fi ;;',
                  f'  *) echo "Preserving edited legacy override: {path}" >&2 ;;', ' esac', 'fi']
    if not lines:
        return ''
    return '\n'.join(checks + ['if [ "$migrate_legacy" = true ]; then'] + lines + [
        'else', ' echo "Legacy overrides retained as a group, including their private libraries; packaged tools are available under /usr/bin." >&2', 'fi'])


def preinst(package):
    lines = ['#!/bin/sh', 'set -eu']
    if package == 'steins-desktop':
        # Undo only our own old ISO hook addition, preserving all other edits.
        lines += ["if [ -f /etc/bash.bashrc ] && grep -qxF '. /etc/profile.d/steins.sh' /etc/bash.bashrc; then",
                  ' mkdir -p /var/lib/steins/legacy/etc',
                  ' cp -n -p /etc/bash.bashrc /var/lib/steins/legacy/etc/bash.bashrc || true',
                  " sed -i '\\|^\\. /etc/profile\\.d/steins\\.sh$|d' /etc/bash.bashrc", 'fi']
    for path in diversions.get(package, []):
        lines += [f'path="{path}"', 'owner=$(dpkg-divert --listpackage "$path")',
            'previous=$(dpkg-divert --truename "$path")',
            'if [ "$owner" = LOCAL ] && { [ "$previous" = "$path.debian" ] || { [ "$path" = /etc/os-release ] && [ "$previous" = "$path.debootstrap" ]; }; }; then',
            ' if [ "$previous" = "$path.debootstrap" ] && [ -e "$previous" ] && [ ! -e "$path.debian" ]; then cp -a "$previous" "$path.debian"; fi',
            ' dpkg-divert --local --remove --no-rename --divert "$previous" "$path"', ' owner=', 'fi',
            f'if [ -n "$owner" ] && [ "$owner" != {package} ]; then',
            ' echo "Another package owns the diversion for $path: $owner" >&2; exit 1', 'fi',
            'if [ -z "$owner" ]; then',
            ' if [ -e "$path" ] && [ ! -e "$path.debian" ]; then cp -a "$path" "$path.debian"; fi',
            f' dpkg-divert --package {package} --add --no-rename --divert "$path.debian" "$path"', 'fi']
    lines += [migrate_script(package), 'exit 0\n']
    return '\n'.join(lines)


def postrm(package):
    lines = ['#!/bin/sh', 'set -eu', 'case "$1" in remove|purge|abort-install)']
    if package == 'steins-live-installer':
        lines += [' rm -rf /var/lib/steins/installer', ' rm -f /usr/lib/steins/calamares-install']
    for path in diversions.get(package, []):
        lines += [f' if [ "$(dpkg-divert --listpackage "{path}")" = {package} ]; then',
                  f'  if [ -e "{path}.debian" ]; then cp -a --remove-destination "{path}.debian" "{path}"; fi',
                  f'  dpkg-divert --package {package} --remove --no-rename --divert "{path}.debian" "{path}"', ' fi']
    if package == 'steins-branding':
        lines += [' rm -rf /usr/share/themes/Steins-Lab /var/lib/steins/branding',
                  ' if command -v plymouth-set-default-theme >/dev/null 2>&1; then',
                  '  if [ "$(plymouth-set-default-theme)" = steins ]; then',
                  '   plymouth-set-default-theme -r -R || true', '  fi', ' fi']
    lines += [' ;;', 'esac', 'exit 0\n']
    return '\n'.join(lines)


with tempfile.TemporaryDirectory(prefix='steins-packages-') as temporary:
    stages = {name: Path(temporary) / name for name in definitions}
    for stage in stages.values():
        stage.mkdir()
    for source in sorted(OVERLAY.rglob('*')):
        if not source.is_file() or '__pycache__' in source.parts:
            continue
        rel = source.relative_to(OVERLAY).as_posix()
        package = 'steins-desktop'
        destination = rel
        if rel.startswith('usr/local/bin/'):
            package = 'steins-live-installer' if source.name == 'install-steins-os' else 'steins-desktop'
            destination = rel.replace('usr/local/bin/', 'usr/bin/', 1)
        elif rel.startswith('usr/local/lib/'):
            destination = rel.replace('usr/local/lib/', 'usr/lib/', 1)
        elif rel.startswith(('usr/share/backgrounds/', 'usr/share/icons/', 'usr/share/plymouth/')):
            package = 'steins-artwork'
            if rel.startswith('usr/share/backgrounds/'):
                destination = 'usr/share/steins/artwork/' + source.name
        elif rel.startswith(('usr/share/steins/calamares/', 'etc/live/')) or rel.endswith('/steins-install.desktop'):
            package = 'steins-live-installer'
        elif rel.startswith(('etc/apt/', 'etc/default/grub.d/', 'etc/lightdm/')):
            package = 'steins-branding'
            if rel == 'etc/lightdm/lightdm-gtk-greeter.conf':
                destination = 'usr/share/lightdm/lightdm-gtk-greeter.conf.d/90-steins.conf'
        mode = 0o755 if destination.startswith('usr/bin/') else 0o644
        put(stages[package], destination, source.read_bytes(), mode)

    art = stages['steins-artwork']
    for source in (art / 'usr/share/steins/artwork').glob('*.svg'):
        target = art / 'usr/share/backgrounds/steins' / (source.stem + '.png')
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['rsvg-convert', str(source), '-o', str(target)], check=True)
    subprocess.run(['rsvg-convert', str(art / 'usr/share/icons/hicolor/scalable/apps/steins-os.svg'),
                    '-o', str(art / 'usr/share/plymouth/themes/steins/logo.png')], check=True)
    branding = stages['steins-branding']
    put(branding, 'etc/os-release', (ROOT / 'packaging/os-release').read_bytes())
    put(branding, 'etc/steins/theme-overrides.css', (ROOT / 'packaging/theme-overrides.css').read_bytes())
    put(branding, 'usr/lib/steins/configure-system', (ROOT / 'packaging/configure-system').read_bytes(), 0o755)
    installer = stages['steins-live-installer']
    put(installer, 'usr/share/applications/calamares-install-debian.desktop',
        '[Desktop Entry]\nType=Application\nName=Debian installer\nHidden=true\nNoDisplay=true\n')
    put(installer, 'etc/skel/.config/autostart/calamares-desktop-icon.desktop',
        '[Desktop Entry]\nType=Application\nName=Debian installer shortcut\nHidden=true\n')

    artifacts = []
    for package, (description, depends) in definitions.items():
        stage = stages[package]
        put(stage, f'usr/share/doc/{package}/package-version', version + '\n')
        put(stage, f'usr/share/doc/{package}/copyright',
            (OVERLAY / 'usr/share/doc/steins-os/copyright').read_bytes())
        payload = sorted(p for p in stage.rglob('*') if p.is_file())
        control = f'Package: {package}\nVersion: {version}\nArchitecture: all\nMaintainer: Steins;OS local build <root@localhost>\nSection: x11\nPriority: optional\n'
        if depends:
            control += 'Depends: ' + depends + '\n'
        control += f'Installed-Size: {sum(p.stat().st_size for p in payload) // 1024 + 1}\nDescription: {description}\n Native Debian/XFCE integration for the Steins;OS development preview.\n'
        put(stage, 'DEBIAN/control', control)
        # os-release is versioned distribution metadata, as in Debian base-files.
        # Treating it as a conffile preserves Debian's existing identity on the
        # first install, even though this package now owns the diverted path.
        conffiles = ['/' + p.relative_to(stage).as_posix() for p in payload
                     if p.relative_to(stage).parts[0] == 'etc' and p.relative_to(stage).as_posix() != 'etc/os-release']
        if conffiles:
            put(stage, 'DEBIAN/conffiles', '\n'.join(conffiles) + '\n')
        put(stage, 'DEBIAN/md5sums', ''.join(hashlib.md5(p.read_bytes()).hexdigest() + '  ' + p.relative_to(stage).as_posix() + '\n' for p in payload))
        if package in ('steins-branding', 'steins-live-installer', 'steins-desktop'):
            put(stage, 'DEBIAN/preinst', preinst(package), 0o755)
        if package in diversions:
            action = 'branding' if package == 'steins-branding' else 'installer'
            put(stage, 'DEBIAN/postinst', '#!/bin/sh\nset -eu\ncase "$1" in configure|triggered)\n /usr/lib/steins/configure-system ' + action + '\n ;;\nesac\n', 0o755)
            put(stage, 'DEBIAN/postrm', postrm(package), 0o755)
            paths = ['/usr/share/themes/Greybird-dark', '/usr/share/plymouth/themes/steins', '/etc/steins/theme-overrides.css'] if action == 'branding' else ['/etc/calamares', '/usr/bin/calamares-install-debian', '/usr/share/steins/calamares']
            put(stage, 'DEBIAN/triggers', ''.join('interest-noawait ' + p + '\n' for p in paths))
        for p in stage.rglob('*'):
            os.utime(p, (int(epoch), int(epoch)))
        filename = f'{package}_{version}_all.deb'
        subprocess.run(['dpkg-deb', '--root-owner-group', '-Zxz', '--build', str(stage), str(output / filename)],
                       check=True, env=dict(os.environ, SOURCE_DATE_EPOCH=epoch), stdout=subprocess.DEVNULL)
        artifacts.append({'package': package, 'version': version, 'file': filename,
                          'sha256': hashlib.sha256((output / filename).read_bytes()).hexdigest(),
                          'files': ['/' + p.relative_to(stage).as_posix() for p in payload]})
    sources = [p for name in ('config', 'packaging') for p in (ROOT / name).rglob('*')
               if p.is_file() and '__pycache__' not in p.parts]
    (output / 'manifest.json').write_text(json.dumps({'version': version, 'source_date_epoch': epoch,
        'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(sources)},
        'packages': artifacts}, indent=2) + '\n')
    # A file-based index is useful for local testing. It is not a signed/public feed.
    index = subprocess.check_output(['dpkg-scanpackages', '--multiversion', '.', '/dev/null'], cwd=output, stderr=subprocess.DEVNULL)
    (output / 'Packages').write_bytes(index)
    print(f'Built {len(artifacts)} packages, version {version}, in {output}')
