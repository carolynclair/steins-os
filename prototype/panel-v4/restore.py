#!/usr/bin/env python3
"""Restore an apply.py backup, with Plasma stopped so it cannot overwrite it."""
from pathlib import Path
import json,os,shutil,subprocess,sys
if len(sys.argv)!=2:sys.exit('Usage: restore.py BACKUP_DIRECTORY (run after ending Plasma)')
if os.geteuid()==0:sys.exit('Run as the desktop user, without sudo.')
if subprocess.run(['pgrep','-u',str(os.getuid()),'-x','plasmashell'],stdout=subprocess.DEVNULL).returncode==0:
    sys.exit('End this user Plasma session before restoring; a live shell would overwrite the saved layout.')
b=Path(sys.argv[1]).resolve();m=json.loads((b/'manifest.json').read_text());config=Path(m['config_home']);config.mkdir(parents=True,exist_ok=True)
allowed={'plasma-org.kde.plasma.desktop-appletsrc','plasmarc','kdeglobals'}
if set(m['files'])!=allowed:sys.exit('Invalid backup manifest.')
for name,existed in m['files'].items():
    dest=config/name
    if existed:shutil.copy2(b/name,dest)
    elif dest.exists():dest.unlink()
print('Restored pre-V4 panel, theme and icon configuration. Start the normal Plasma session.')
