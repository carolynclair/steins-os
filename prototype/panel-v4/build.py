#!/usr/bin/env python3
"""Build the separate opt-in V4 panel/theme package; never install or configure."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2];SOURCE=Path(__file__).resolve().parent
OUT=ROOT/'dist/v4/panel';VERSION='0.4.0~prototype6'
subprocess.run(['python3',str(SOURCE/'generate.py')],check=True)
OUT.mkdir(parents=True,exist_ok=True);package=OUT/('steins-panel-v4_'+VERSION+'_all.deb')
with tempfile.TemporaryDirectory(prefix='steins-panel-v4-build-') as tmp:
    stage=Path(tmp)
    shutil.copytree(SOURCE/'package',stage/'usr/share/plasma/plasmoids/org.steinsos.worldline.v4')
    shutil.copytree(SOURCE/'theme',stage/'usr/share/plasma/desktoptheme/SteinsLab')
    helper=stage/'usr/share/steins-v4/panel';helper.mkdir(parents=True)
    for name in ['attach.js','apply.py','restore.py']:shutil.copyfile(SOURCE/name,helper/name)
    doc=stage/'usr/share/doc/steins-panel-v4';doc.mkdir(parents=True)
    shutil.copyfile(ROOT/'LICENSE',doc/'copyright');shutil.copyfile(SOURCE/'README.md',doc/'README.md')
    (stage/'DEBIAN').mkdir()
    (stage/'DEBIAN/control').write_text('Package: steins-panel-v4\nVersion: '+VERSION+'\nArchitecture: all\n'
       'Maintainer: Steins OS contributors <steins@localhost>\nSection: x11\nPriority: optional\n'
       'Depends: steins-plasma-prototype (>= 0.1.0~prototype7v4.1), steins-identity-v4 (>= 0.4.0~prototype1), '
       'steins-surfaces-v4 (>= 0.4.0~prototype1), steins-terminal-v3, plasma-workspace (>= 4:6.3), plasma-desktoptheme, python3, qdbus-qt6, '
       'qml6-module-qtquick, qml6-module-qtquick-controls, qml6-module-qtquick-layouts, qml6-module-org-kde-kirigami\n'
       'Description: Steins Lab V4 native Plasma panel theme and worldline instrument\n'
       ' Original neutral panel/task frames, a clickable shared-service instrument,\n'
       ' and explicit reversible panel configuration helpers. No layout changes at install.\n')
    for p in stage.rglob('*'):p.chmod(0o755 if p.is_dir() else 0o644)
    subprocess.run(['dpkg-deb','--root-owner-group','--build',str(stage),str(package)],check=True)
print(json.dumps({'package':str(package),'sha256':hashlib.sha256(package.read_bytes()).hexdigest(),'bytes':package.stat().st_size,'host_installed':False},indent=2))
