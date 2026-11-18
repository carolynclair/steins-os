#!/usr/bin/env python3
"""Explicit, user-session-only V4 panel preset with a full config backup."""
from pathlib import Path
from datetime import datetime, timezone
import argparse,json,os,shutil,subprocess,sys
HERE=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--replace-v3',action='store_true',help='Remove only org.steinsos.worldline V3 meters after the V4 meter is added successfully.')
    p.add_argument('--panel-id',help='Choose a specific existing bottom panel.')
    p.add_argument('--print-script',action='store_true',help='Read-only: print the script without applying or backing up anything.')
    a=p.parse_args()
    source=HERE/'attach.js'
    script=source.read_text().replace('__STEINS_OPTIONS__',json.dumps({'replaceV3':a.replace_v3,'panelId':a.panel_id}))
    if a.print_script:print(script);return
    if os.geteuid()==0:sys.exit('Run as the desktop user inside the isolated V4 guest, without sudo.')
    detect=shutil.which('systemd-detect-virt')
    vm=subprocess.run([detect,'--vm'],capture_output=True,text=True).stdout.strip() if detect else ''
    if vm not in ('kvm','qemu'):sys.exit('This prototype preset is restricted to the isolated QEMU/KVM test guest. No configuration was changed.')
    qdbus=shutil.which('qdbus6') or shutil.which('qdbus')
    theme=shutil.which('plasma-apply-desktoptheme')
    if not qdbus or not theme:sys.exit('Plasma 6 session tools are required.')
    config=Path(os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))
    saved=Path(os.environ.get('XDG_STATE_HOME',str(Path.home()/'.local/state')))/'steins-v4/panel-backups'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    saved.mkdir(parents=True)
    names=['plasma-org.kde.plasma.desktop-appletsrc','plasmarc','kdeglobals']
    manifest={}
    for name in names:
        f=config/name;manifest[name]=f.exists()
        if f.exists():shutil.copy2(f,saved/name)
    (saved/'manifest.json').write_text(json.dumps({'config_home':str(config),'files':manifest,'replace_v3':a.replace_v3},indent=2)+'\n')
    print('Config backup: '+str(saved),flush=True)
    result=subprocess.run([qdbus,'org.kde.plasmashell','/PlasmaShell','org.kde.PlasmaShell.evaluateScript',script],capture_output=True,text=True)
    print(result.stdout,end='');print(result.stderr,end='',file=sys.stderr)
    if result.returncode or 'Error:' in result.stdout or 'Error:' in result.stderr:
        sys.exit('Panel script failed. Backup retained; review its output before retrying.')
    subprocess.run([theme,'SteinsLab'],check=True)
    print('Applied V4 panel/theme preset. A guest-only sign-out/in confirms the saved panel order. No shell restart was requested automatically.')
    print('Rollback after ending the guest Plasma session: python3 '+str(HERE/'restore.py')+' '+str(saved))
if __name__=='__main__':main()
