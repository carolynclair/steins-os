#!/usr/bin/env python3
"""Build experimental themes without selecting them or changing initramfs."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
OUT=PROJECT/'dist/v3/startup';OUT.mkdir(parents=True,exist_ok=True)
ASSETS=ROOT/'assets';ASSETS.mkdir(exist_ok=True)
source=PROJECT/'config/includes.chroot/usr/share/icons/hicolor/scalable/apps/steins-os.svg'
mark=re.search(r'(<g\b.*</g>)',source.read_text(),re.S).group(1)
# The unchanged original mark is centred in a transparent 320px canvas.
for index in range(12):
 clip=32+(index+1)*256/12
 text=f'<svg xmlns="http://www.w3.org/2000/svg" width="320" height="320" viewBox="0 0 320 320"><defs><clipPath id="reveal"><rect x="0" y="{320-clip}" width="320" height="{clip}"/></clipPath></defs><g clip-path="url(#reveal)"><g transform="translate(64 64) scale(1.5)">{mark}</g></g></svg>'
 (ASSETS/f'assembly-{index}.svg').write_text(text)
(ASSETS/'logo.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="320" height="320" viewBox="0 0 320 320"><g transform="translate(64 64) scale(1.5)">{mark}</g></svg>')
(ASSETS/'traces.svg').write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="480" height="320" viewBox="0 0 480 320"><g fill="none" stroke="#e99a45" stroke-width="1.3"><path d="M24 196H98L132 162H166M314 162H348L382 128H456M54 220H126L148 198M332 122L354 100H426"/><circle cx="24" cy="196" r="3"/><circle cx="456" cy="128" r="3"/><path d="M174 64H202M278 256H306" opacity=".5"/></g></svg>''')
# GRUB keeps a large uniform menu region; identity stays in the header margin.
GRUB=ASSETS/'grub';GRUB.mkdir(exist_ok=True)
for width,height in [(1280,800),(1366,768)]:
    logo_x=width-48
    text=f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><rect width="{width}" height="{height}" fill="#0e1317"/><g fill="none" stroke="#e99a45" stroke-width="1" opacity=".45"><path d="M8 26V8H38M{width-38} 8H{width-8}V26M8 {height-26}V{height-8}H38M{width-38} {height-8}H{width-8}V{height-26}"/><path d="M60 22H148M{width-148} {height-22}H{width-60}" opacity=".22"/></g><g transform="translate({logo_x} 6) scale(.25)">{mark}</g></svg>'''
    (GRUB/f'grub-background-{width}x{height}.svg').write_text(text)
subprocess.run(['docker','run','--rm','--user',f'{os.getuid()}:{os.getgid()}','-v',str(ASSETS)+':/work','-w','/work','steins-os-builder:trixie','sh','-c','for file in *.svg grub/*.svg; do rsvg-convert "$file" -o "${file%.svg}.png" || exit; done'],check=True)
version='0.1.0~v3.2'
with tempfile.TemporaryDirectory(prefix='steins-startup-') as td:
 stage=Path(td); themes=stage/'usr/share/plymouth/themes'
 for variant,motion in [('steins-lab-v3','full'),('steins-lab-v3-reduced','reduced'),('steins-lab-v3-static','off')]:
  theme=themes/variant;theme.mkdir(parents=True)
  for asset in ASSETS.glob('*.png'):shutil.copy2(asset,theme/asset.name)
  (theme/'steins.script').write_text((ROOT/'theme/steins.script.in').read_text().replace('@MOTION@',motion))
  (theme/(variant+'.plymouth')).write_text(f'[Plymouth Theme]\nName=Steins;OS Laboratory V3 ({motion})\nDescription=Original restrained laboratory startup; silent\nModuleName=script\n[script]\nImageDir=/usr/share/plymouth/themes/{variant}\nScriptFile=/usr/share/plymouth/themes/{variant}/steins.script\n')
  exported=ROOT/'generated'/variant
  if exported.exists():shutil.rmtree(exported)
  shutil.copytree(theme,exported)
 grub=stage/'usr/share/steins/startup';grub.mkdir(parents=True)
 for asset in GRUB.glob('*'):shutil.copy2(asset,grub/asset.name)
 helper=stage/'usr/lib/steins/startup/grub-lab.py';helper.parent.mkdir(parents=True)
 shutil.copy2(ROOT/'tools/grub-lab.py',helper);helper.chmod(0o755)
 doc=stage/'usr/share/doc/steins-startup-prototype';doc.mkdir(parents=True)
 (doc/'copyright').write_text('Code: MIT. Original art derived from current Steins;OS emblem: CC-BY-4.0, Steins;OS contributors. Upstream Plymouth remains GPL-2.0-or-later.\n')
 (doc/'README').write_text('Experimental optional themes only. No maintainer script selects a theme or rebuilds initramfs. See prototype/startup/README.md for disposable guest qualification and rollback.\n')
 control=stage/'DEBIAN';control.mkdir()
 (control/'control').write_text(f'Package: steins-startup-prototype\nVersion: {version}\nArchitecture: all\nMaintainer: Steins;OS contributors\nDepends: plymouth (>= 24.004.60), plymouth-label, python3\nDescription: Experimental original laboratory Plymouth themes\n Optional full, reduced and static themes plus guest-only GRUB assets; never selects itself.\n')
 # Debian payloads must not inherit the workstation's group-writable umask.
 stage.chmod(0o755)
 for installed in stage.rglob('*'):
  if installed.is_dir():installed.chmod(0o755)
  elif installed.is_file():installed.chmod(0o755 if installed==helper else 0o644)
 target=OUT/f'steins-startup-prototype_{version}_all.deb'
 subprocess.run(['dpkg-deb','--root-owner-group','-Zxz','--build',str(stage),str(target)],check=True)
 report={'version':version,'package':str(target.relative_to(PROJECT)),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'original_emblem_source':str(source.relative_to(PROJECT)),'original_emblem_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'no_automatic_selection':True,'no_audio':True,'motion_variants':['full','reduced','off'],'nominal_full_frames':33,'requested_refresh_hz':30,'real_boot_qualified':False,'grub_background_sizes':['1280x800','1366x768'],'grub_explicit_guest_opt_in_only':True}
 (OUT/'BUILD.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
