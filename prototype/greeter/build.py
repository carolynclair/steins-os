#!/usr/bin/python3
"""Package opt-in presets around upstream Breeze; never deploy on the host."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2];SOURCE=Path(__file__).resolve().parent
OUT=ROOT/'dist/v3/greeter';OUT.mkdir(parents=True,exist_ok=True)
package=OUT/'steins-login-prototype_0.1.0~v3.1_all.deb'
with tempfile.TemporaryDirectory(prefix='steins-greeter-') as tmp:
 stage=Path(tmp)
 for source,dest,mode in [('login-lab.py','usr/lib/steins/login-lab.py',0o755),('breeze-theme.conf','usr/share/steins-login/breeze-theme.conf',0o644),('README.md','usr/share/doc/steins-login-prototype/README.md',0o644)]:
  target=stage/dest;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(SOURCE/source,target);target.chmod(mode)
 target=stage/'usr/share/doc/steins-login-prototype/copyright';shutil.copyfile(ROOT/'LICENSE',target)
 control=stage/'DEBIAN/control';control.parent.mkdir();control.write_text('Package: steins-login-prototype\nVersion: 0.1.0~v3.1\nArchitecture: all\nMaintainer: Steins OS contributors <steins@localhost>\nSection: x11\nPriority: optional\nDepends: python3, sddm-theme-breeze (>= 4:6.3), steins-plasma-prototype, steins-startup-prototype\nDescription: Opt-in Steins artwork presets for maintained Breeze authentication\n No display-manager code or user authentication is replaced.\n')
 subprocess.run(['dpkg-deb','--root-owner-group','--build',str(stage),str(package)],check=True)
(OUT/'BUILD.json').write_text(json.dumps({'package':str(package.relative_to(ROOT)),'sha256':hashlib.sha256(package.read_bytes()).hexdigest(),'automatic_enablement':False},indent=2)+'\n')
print(package)
